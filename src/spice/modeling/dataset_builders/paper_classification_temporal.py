"""Paper-classification dataset-preparation path."""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import polars as pl

from ...core.errors import ConfigResolutionError
from ...temporal.problem_store import CompiledProblemStore, DatasetSplitIndices
from ...temporal.scaling import ScalerStats, transform_feature_matrix
from ..pipeline import (
    InferencePreparationSpec,
    PreparedInferenceDataset,
    PreparedTrainingDataset,
    TrainingSpec,
)
from .base import (
    CompiledDatasetBuilderContract,
    PaperClassificationTemporalDatasetBuilderConfig,
)
from .registry import DatasetBuilderSpec, register_dataset_builder_spec


@dataclass(frozen=True, slots=True)
class _PaperSplitStore:
    feature_matrix: np.ndarray
    log_base_fees: np.ndarray
    timestamps: np.ndarray
    anchor_rows: np.ndarray
    context_start_rows: np.ndarray
    candidate_end_rows: np.ndarray
    precomputed_min_block_offsets: np.ndarray
    precomputed_min_block_log_fees: np.ndarray


def _prepare_blocks(blocks: pl.DataFrame) -> pl.DataFrame:
    if blocks.height == 0:
        raise ValueError("dataset builder received an empty block frame")
    return (
        blocks.sort("timestamp")
        .unique(subset=["block_number"], keep="first", maintain_order=True)
        .sort("block_number")
    )


def _compute_seq_len(
    timestamps: np.ndarray,
    *,
    lookback_seconds: int,
    min_sequence_length: int,
    max_sequence_length: int,
) -> tuple[int, float]:
    if timestamps.size < 2:
        raise ValueError("paper builder requires at least two timestamps")
    deltas = np.diff(timestamps.astype(np.float64, copy=False), prepend=timestamps[:1])
    if deltas.size > 1:
        deltas[0] = float(np.median(deltas[1:]))
    median_dt = float(np.median(deltas[1:])) if deltas.size > 1 else float(deltas[0])
    seq_len = int(round(lookback_seconds / max(median_dt, 1e-6)))
    seq_len = int(np.clip(seq_len, min_sequence_length, max_sequence_length))
    return seq_len, median_dt


def _drop_invalid_feature_rows(
    feature_matrix: np.ndarray,
    log_base_fees: np.ndarray,
    paper_log_base_fees: np.ndarray,
    timestamps: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    valid_mask = np.isfinite(feature_matrix).all(axis=1)
    if not np.any(valid_mask):
        raise ValueError("paper builder produced no finite feature rows")
    return (
        feature_matrix[valid_mask].astype(np.float32, copy=False),
        log_base_fees[valid_mask].astype(np.float32, copy=False),
        paper_log_base_fees[valid_mask].astype(np.float32, copy=False),
        timestamps[valid_mask].astype(np.int64, copy=False),
    )


def _candidate_end_rows(timestamps: np.ndarray, *, delay_seconds: int) -> np.ndarray:
    return np.searchsorted(timestamps, timestamps + delay_seconds, side="right").astype(
        np.int64,
        copy=False,
    )


def _build_split_store(
    blocks: pl.DataFrame,
    *,
    spec: TrainingSpec,
    seq_len: int,
    class_cap: int | None = None,
) -> _PaperSplitStore:
    feature_table = spec.feature_contract.build_table(_prepare_blocks(blocks))
    try:
        paper_log_fee_index = feature_table.feature_names.index("log_base_fee_per_gas")
    except ValueError as exc:
        raise ValueError(
            "paper builder requires feature_set output 'log_base_fee_per_gas'"
        ) from exc
    paper_log_base_fees = feature_table.feature_matrix[:, paper_log_fee_index]
    feature_matrix, log_base_fees, paper_log_base_fees, timestamps = _drop_invalid_feature_rows(
        feature_table.feature_matrix,
        feature_table.series.log_base_fees,
        paper_log_base_fees,
        feature_table.series.timestamps,
    )
    if feature_matrix.shape[0] < seq_len:
        raise ValueError(
            f"paper builder split is too short for seq_len={seq_len}: rows={feature_matrix.shape[0]}"
        )
    anchor_candidates = np.arange(feature_matrix.shape[0], dtype=np.int64)
    candidate_end_rows = _candidate_end_rows(timestamps, delay_seconds=spec.problem.max_delay_seconds)
    candidate_counts = candidate_end_rows - (anchor_candidates + 1)
    valid_anchor_mask = (anchor_candidates >= (seq_len - 1)) & (candidate_counts > 0)
    anchor_rows = anchor_candidates[valid_anchor_mask].astype(np.int64, copy=False)
    if anchor_rows.size == 0:
        raise ValueError("paper builder split produced no supervised samples")
    context_start_rows = (anchor_rows - seq_len + 1).astype(np.int64, copy=False)
    selected_candidate_ends = candidate_end_rows[anchor_rows].astype(np.int64, copy=False)
    precomputed_min_block_offsets = np.zeros(anchor_rows.shape[0], dtype=np.int64)
    precomputed_min_block_log_fees = np.zeros(anchor_rows.shape[0], dtype=np.float32)
    for row, (anchor_row, candidate_end) in enumerate(
        zip(anchor_rows, selected_candidate_ends, strict=True)
    ):
        candidate_values = paper_log_base_fees[int(anchor_row) + 1 : int(candidate_end)]
        min_offset = int(np.argmin(candidate_values))
        precomputed_min_block_offsets[row] = (
            min(min_offset, class_cap) if class_cap is not None else min_offset
        )
        precomputed_min_block_log_fees[row] = float(candidate_values[min_offset])
    return _PaperSplitStore(
        feature_matrix=feature_matrix,
        log_base_fees=log_base_fees,
        timestamps=timestamps,
        anchor_rows=anchor_rows,
        context_start_rows=context_start_rows,
        candidate_end_rows=selected_candidate_ends,
        precomputed_min_block_offsets=precomputed_min_block_offsets,
        precomputed_min_block_log_fees=precomputed_min_block_log_fees,
    )


def _split_row_bounds(n_rows: int, *, train_fraction: float, validation_fraction: float) -> tuple[int, int]:
    train_end = int(n_rows * train_fraction)
    validation_end = train_end + int(n_rows * validation_fraction)
    train_end = max(1, min(train_end, n_rows - 2))
    validation_end = max(train_end + 1, min(validation_end, n_rows - 1))
    return train_end, validation_end


def _concatenate_split_stores(
    train_store: _PaperSplitStore,
    validation_store: _PaperSplitStore,
    test_store: _PaperSplitStore,
    *,
    scaler: ScalerStats,
    feature_semantics,
    builder_runtime_metadata: dict[str, object],
    n_rows_available: int,
) -> PreparedTrainingDataset:
    split_stores = (train_store, validation_store, test_store)
    row_offsets: list[int] = []
    cursor = 0
    for store in split_stores:
        row_offsets.append(cursor)
        cursor += int(store.feature_matrix.shape[0])
    feature_matrix = np.concatenate([store.feature_matrix for store in split_stores], axis=0)
    log_base_fees = np.concatenate([store.log_base_fees for store in split_stores], axis=0)
    timestamps = np.concatenate([store.timestamps for store in split_stores], axis=0)
    anchor_rows = np.concatenate(
        [
            (store.anchor_rows + row_offset).astype(np.int64, copy=False)
            for store, row_offset in zip(split_stores, row_offsets, strict=True)
        ],
        axis=0,
    )
    context_start_rows = np.concatenate(
        [
            (store.context_start_rows + row_offset).astype(np.int64, copy=False)
            for store, row_offset in zip(split_stores, row_offsets, strict=True)
        ],
        axis=0,
    )
    candidate_end_rows = np.concatenate(
        [
            (store.candidate_end_rows + row_offset).astype(np.int64, copy=False)
            for store, row_offset in zip(split_stores, row_offsets, strict=True)
        ],
        axis=0,
    )
    precomputed_min_block_offsets = np.concatenate(
        [store.precomputed_min_block_offsets for store in split_stores],
        axis=0,
    )
    precomputed_min_block_log_fees = np.concatenate(
        [store.precomputed_min_block_log_fees for store in split_stores],
        axis=0,
    )
    train_count = int(train_store.anchor_rows.shape[0])
    validation_count = int(validation_store.anchor_rows.shape[0])
    test_count = int(test_store.anchor_rows.shape[0])
    scaled_store = CompiledProblemStore(
        feature_matrix=transform_feature_matrix(feature_matrix, scaler),
        log_base_fees=log_base_fees.astype(np.float32, copy=False),
        timestamps=timestamps.astype(np.int64, copy=False),
        anchor_rows=anchor_rows.astype(np.int64, copy=False),
        context_start_rows=context_start_rows.astype(np.int64, copy=False),
        candidate_end_rows=candidate_end_rows.astype(np.int64, copy=False),
        max_candidate_slots=int(builder_runtime_metadata["paper_class_count"]),
        precomputed_min_block_offsets=precomputed_min_block_offsets.astype(
            np.int64,
            copy=False,
        ),
        precomputed_min_block_log_fees=precomputed_min_block_log_fees.astype(
            np.float32,
            copy=False,
        ),
        fixed_candidate_class_space=True,
    )
    return PreparedTrainingDataset(
        n_rows_available=n_rows_available,
        n_rows_used=int(feature_matrix.shape[0]),
        sample_count=train_count + validation_count + test_count,
        feature=feature_semantics,
        store=scaled_store,
        split_indices=DatasetSplitIndices(
            train=np.arange(train_count, dtype=np.int64),
            validation=np.arange(train_count, train_count + validation_count, dtype=np.int64),
            test=np.arange(
                train_count + validation_count,
                train_count + validation_count + test_count,
                dtype=np.int64,
            ),
        ),
        scaler=scaler,
        builder_runtime_metadata=builder_runtime_metadata,
    )


def prepare_training_dataset(blocks: pl.DataFrame, spec: TrainingSpec) -> PreparedTrainingDataset:
    if not isinstance(spec.dataset_builder, PaperClassificationTemporalDatasetBuilderConfig):
        raise TypeError("paper builder requires PaperClassificationTemporalDatasetBuilderConfig")
    sorted_blocks = blocks.sort("block_number")
    if sorted_blocks.height == 0:
        raise ValueError("Training dataset is empty")
    if sorted_blocks.height < spec.problem.sample_count:
        raise ValueError(
            "History dataset is too short for the requested sample count; "
            f"need at least {spec.problem.sample_count} rows, got {sorted_blocks.height}"
        )
    selected_blocks = sorted_blocks.tail(spec.problem.sample_count)
    train_end, validation_end = _split_row_bounds(
        selected_blocks.height,
        train_fraction=spec.split.train_fraction,
        validation_fraction=spec.split.validation_fraction,
    )
    train_blocks = selected_blocks.slice(0, train_end)
    validation_blocks = selected_blocks.slice(train_end, validation_end - train_end)
    test_blocks = selected_blocks.slice(validation_end)
    train_prepared_blocks = _prepare_blocks(train_blocks)
    seq_len, median_dt = _compute_seq_len(
        train_prepared_blocks["timestamp"].cast(pl.Int64).to_numpy(),
        lookback_seconds=spec.problem.lookback_seconds,
        min_sequence_length=spec.dataset_builder.min_sequence_length,
        max_sequence_length=spec.dataset_builder.max_sequence_length,
    )
    train_store = _build_split_store(
        train_blocks,
        spec=spec,
        seq_len=seq_len,
    )
    paper_class_count = int(train_store.precomputed_min_block_offsets.max()) + 1
    validation_store = _build_split_store(
        validation_blocks,
        spec=spec,
        seq_len=seq_len,
        class_cap=paper_class_count - 1,
    )
    test_store = _build_split_store(
        test_blocks,
        spec=spec,
        seq_len=seq_len,
        class_cap=paper_class_count - 1,
    )
    train_feature_matrix = train_store.feature_matrix
    train_combined_store = CompiledProblemStore(
        feature_matrix=train_feature_matrix,
        log_base_fees=train_store.log_base_fees,
        timestamps=train_store.timestamps,
        anchor_rows=train_store.anchor_rows,
        context_start_rows=train_store.context_start_rows,
        candidate_end_rows=train_store.candidate_end_rows,
        max_candidate_slots=paper_class_count,
        precomputed_min_block_offsets=train_store.precomputed_min_block_offsets,
        precomputed_min_block_log_fees=train_store.precomputed_min_block_log_fees,
        fixed_candidate_class_space=True,
    )
    train_sample_indices = np.arange(int(train_store.anchor_rows.shape[0]), dtype=np.int64)
    scaler = spec.input_normalization_contract.fit_scaler(
        train_combined_store.feature_matrix,
        context_start_rows=train_combined_store.context_start_rows,
        anchor_rows=train_combined_store.anchor_rows,
        sample_indices=train_sample_indices,
    )
    builder_runtime_metadata = {
        "seq_len": seq_len,
        "median_dt_seconds": median_dt,
        "paper_class_count": paper_class_count,
        "min_sequence_length": spec.dataset_builder.min_sequence_length,
        "max_sequence_length": spec.dataset_builder.max_sequence_length,
    }
    return _concatenate_split_stores(
        train_store,
        validation_store,
        test_store,
        scaler=scaler,
        feature_semantics=spec.feature_contract.semantics,
        builder_runtime_metadata=builder_runtime_metadata,
        n_rows_available=selected_blocks.height,
    )


def prepare_inference_dataset(
    history_blocks: pl.DataFrame,
    evaluation_blocks: pl.DataFrame,
    spec: InferencePreparationSpec,
) -> PreparedInferenceDataset:
    builder_runtime_metadata = spec.builder_runtime_metadata
    seq_len = int(builder_runtime_metadata["seq_len"])
    combined_blocks = pl.concat([history_blocks, evaluation_blocks]).sort("block_number")
    feature_table = spec.feature_contract.build_table(_prepare_blocks(combined_blocks))
    feature_matrix, log_base_fees, timestamps = _drop_invalid_feature_rows(
        feature_table.feature_matrix,
        feature_table.series.log_base_fees,
        feature_table.series.timestamps,
    )
    if feature_matrix.shape[0] < seq_len:
        raise ValueError(
            f"Evaluation dataset is too short for seq_len={seq_len}: rows={feature_matrix.shape[0]}"
        )
    anchor_candidates = np.arange(feature_matrix.shape[0], dtype=np.int64)
    candidate_end_rows = _candidate_end_rows(timestamps, delay_seconds=spec.delay_seconds)
    candidate_counts = candidate_end_rows - (anchor_candidates + 1)
    valid_anchor_mask = (anchor_candidates >= (seq_len - 1)) & (candidate_counts > 0)
    anchor_rows = anchor_candidates[valid_anchor_mask].astype(np.int64, copy=False)
    context_start_rows = (anchor_rows - seq_len + 1).astype(np.int64, copy=False)
    selected_candidate_ends = candidate_end_rows[anchor_rows].astype(np.int64, copy=False)
    candidate_starts = anchor_rows + 1
    clipped_candidate_ends = np.minimum(
        selected_candidate_ends,
        candidate_starts + spec.max_candidate_slots,
    ).astype(np.int64, copy=False)
    store = CompiledProblemStore(
        feature_matrix=transform_feature_matrix(feature_matrix, spec.scaler),
        log_base_fees=log_base_fees.astype(np.float32, copy=False),
        timestamps=timestamps.astype(np.int64, copy=False),
        anchor_rows=anchor_rows.astype(np.int64, copy=False),
        context_start_rows=context_start_rows.astype(np.int64, copy=False),
        candidate_end_rows=clipped_candidate_ends,
        max_candidate_slots=spec.max_candidate_slots,
        fixed_candidate_class_space=True,
    )
    sample_timestamps = store.timestamps[store.anchor_rows]
    sample_mask = (
        (sample_timestamps >= spec.window_start_timestamp)
        & (sample_timestamps < spec.window_end_timestamp)
    )
    sample_indices = np.flatnonzero(sample_mask).astype(np.int64, copy=False)
    if sample_indices.size == 0:
        raise ValueError("Evaluation dataset produced no valid inference examples")
    return PreparedInferenceDataset(
        n_history_rows=history_blocks.height,
        n_evaluation_rows=evaluation_blocks.height,
        sample_count=int(sample_indices.shape[0]),
        feature=spec.feature_contract.semantics,
        store=store,
        sample_indices=sample_indices,
    )


def _compile(
    config: PaperClassificationTemporalDatasetBuilderConfig,
) -> CompiledDatasetBuilderContract:
    if config.id != "paper_classification_temporal":
        raise ConfigResolutionError("dataset_builder.id must be paper_classification_temporal")
    return CompiledDatasetBuilderContract(
        dataset_builder_id="paper_classification_temporal",
        config_payload=config.model_dump(mode="json", exclude_none=True),
        prepare_training_fn=prepare_training_dataset,
        prepare_inference_fn=prepare_inference_dataset,
    )


register_dataset_builder_spec(
    DatasetBuilderSpec(
        id="paper_classification_temporal",
        config_type=PaperClassificationTemporalDatasetBuilderConfig,
        compile=_compile,
    )
)
