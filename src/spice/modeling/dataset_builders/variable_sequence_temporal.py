"""Current production dataset-preparation path."""

from __future__ import annotations

from dataclasses import replace

import polars as pl

from ...core.errors import ConfigResolutionError
from ...temporal.problem_store import (
    DatasetSplitIndices,
    chronological_split_indices,
    filter_sample_indices_by_timestamp_window,
    tail_sample_indices,
)
from ...temporal.scaling import transform_feature_matrix
from ..pipeline import (
    InferencePreparationSpec,
    PreparedInferenceDataset,
    PreparedTrainingDataset,
    TrainingSpec,
    selected_row_span,
)
from .base import (
    CompiledDatasetBuilderContract,
    VariableSequenceTemporalDatasetBuilderConfig,
    compiler_runtime_metadata_from_builder_payload,
    validate_feature_prerequisites,
    variable_sequence_temporal_runtime_metadata,
)


def _prepare_blocks(blocks: pl.DataFrame, *, allow_empty: bool = False) -> pl.DataFrame:
    if blocks.height == 0 and not allow_empty:
        raise ValueError("dataset builder received an empty block frame")
    return blocks.sort("block_number")


def prepare_training_dataset(blocks: pl.DataFrame, spec: TrainingSpec) -> PreparedTrainingDataset:
    sorted_blocks = _prepare_blocks(blocks)
    feature_table = spec.feature_contract.build_table(sorted_blocks)
    validate_feature_prerequisites(
        feature_table.feature_prerequisites,
        spec.problem_contract.feature_prerequisites,
    )
    store, compiler_runtime_metadata = spec.problem_contract.build_capability_store(feature_table)
    selected_sample_indices = tail_sample_indices(store, sample_count=spec.problem.sample_count)
    split_positions = chronological_split_indices(int(selected_sample_indices.shape[0]), spec.split)
    split_indices = DatasetSplitIndices(
        train=selected_sample_indices[split_positions.train],
        validation=selected_sample_indices[split_positions.validation],
        test=selected_sample_indices[split_positions.test],
    )
    scaler = spec.input_normalization_contract.fit_scaler(
        store.feature_matrix,
        context_start_rows=store.context_start_rows,
        anchor_rows=store.anchor_rows,
        sample_indices=split_indices.train,
    )
    scaled_store = replace(
        store,
        feature_matrix=transform_feature_matrix(store.feature_matrix, scaler),
    )
    used_start, used_end = selected_row_span(store, selected_sample_indices)
    return PreparedTrainingDataset(
        n_rows_available=sorted_blocks.height,
        n_rows_used=used_end - used_start,
        sample_count=int(selected_sample_indices.shape[0]),
        feature=spec.feature_contract.semantics,
        execution_policy=spec.problem_contract.execution_policy,
        store=scaled_store,
        split_indices=split_indices,
        scaler=scaler,
        builder_runtime_metadata=variable_sequence_temporal_runtime_metadata(
            compiler_id=spec.problem_contract.compiler_id,
            compiler_runtime_metadata=compiler_runtime_metadata,
        ),
    )


def prepare_inference_dataset(
    history_blocks: pl.DataFrame,
    evaluation_blocks: pl.DataFrame,
    spec: InferencePreparationSpec,
) -> PreparedInferenceDataset:
    sorted_history_blocks = _prepare_blocks(history_blocks)
    combined_blocks = pl.concat(
        [
            sorted_history_blocks,
            _prepare_blocks(
                evaluation_blocks,
                allow_empty=True,
            ),
        ]
    )
    feature_table = spec.feature_contract.build_table(combined_blocks)
    store = spec.problem_contract.build_delay_store(
        feature_table,
        spec.delay_seconds,
        compiler_runtime_metadata=compiler_runtime_metadata_from_builder_payload(
            spec.builder_runtime_metadata,
            compiler_id=spec.problem_contract.compiler_id,
        ),
        max_candidate_slots=spec.max_candidate_slots,
    )
    sample_indices = filter_sample_indices_by_timestamp_window(
        store,
        start_timestamp=spec.window_start_timestamp,
        end_timestamp=spec.window_end_timestamp,
    )
    if sample_indices.size == 0:
        raise ValueError("Evaluation dataset produced no valid inference examples")
    scaled_store = replace(
        store,
        feature_matrix=transform_feature_matrix(store.feature_matrix, spec.scaler),
    )
    return PreparedInferenceDataset(
        n_history_rows=history_blocks.height,
        n_evaluation_rows=evaluation_blocks.height,
        sample_count=int(sample_indices.shape[0]),
        feature=spec.feature_contract.semantics,
        execution_policy=spec.problem_contract.execution_policy,
        store=scaled_store,
        sample_indices=sample_indices,
    )


def compile_dataset_builder(
    config: VariableSequenceTemporalDatasetBuilderConfig,
) -> CompiledDatasetBuilderContract:
    if config.id != "variable_sequence_temporal":
        raise ConfigResolutionError("dataset_builder.id must be variable_sequence_temporal")
    return CompiledDatasetBuilderContract(
        dataset_builder_id="variable_sequence_temporal",
        prepare_training_fn=prepare_training_dataset,
        prepare_inference_fn=prepare_inference_dataset,
    )
