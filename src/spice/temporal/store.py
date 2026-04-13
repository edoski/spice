"""Timestamp-native temporal stores and sample slicing helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ..config import SplitConfig
from ..features import FeatureTable
from ..temporal.window import DelayWindow

FloatMatrix = NDArray[np.float32]
FloatVector = NDArray[np.float32]
IntVector = NDArray[np.int64]


@dataclass(slots=True)
class DatasetSplitIndices:
    train: IntVector
    validation: IntVector
    test: IntVector


@dataclass(slots=True)
class TemporalDatasetStore:
    feature_matrix: FloatMatrix
    log_base_fees: FloatVector
    timestamps: IntVector
    anchor_rows: IntVector
    context_start_rows: IntVector
    candidate_end_rows: IntVector
    max_candidate_slots: int

    @property
    def n_rows(self) -> int:
        return int(self.feature_matrix.shape[0])

    @property
    def n_features(self) -> int:
        return int(self.feature_matrix.shape[1])

    @property
    def n_samples(self) -> int:
        return int(self.anchor_rows.shape[0])

    @property
    def candidate_start_rows(self) -> IntVector:
        return self.anchor_rows + 1

    @property
    def candidate_counts(self) -> IntVector:
        return self.candidate_end_rows - self.candidate_start_rows


def build_temporal_store(
    feature_table: FeatureTable,
    *,
    window: DelayWindow,
    max_candidate_slots: int | None = None,
) -> TemporalDatasetStore:
    if window.lookback_seconds <= 0:
        raise ValueError("lookback_seconds must be positive")
    if window.delay_seconds <= 0:
        raise ValueError("delay_seconds must be positive")

    timestamps = feature_table.timestamps
    log_base_fees = feature_table.log_base_fees
    feature_matrix = feature_table.feature_matrix
    if timestamps.size == 0:
        raise ValueError("Feature table is too short to produce any supervised samples")

    required_history_seconds = window.required_history_seconds
    context_start_rows = np.searchsorted(
        timestamps,
        timestamps - window.lookback_seconds,
        side="left",
    ).astype(np.int64, copy=False)
    candidate_end_rows = np.searchsorted(
        timestamps,
        timestamps + window.delay_seconds,
        side="right",
    ).astype(np.int64, copy=False)
    anchor_candidates = np.arange(timestamps.shape[0], dtype=np.int64)
    candidate_counts = candidate_end_rows - (anchor_candidates + 1)
    history_ready = (timestamps - timestamps[0]) >= required_history_seconds
    valid_anchor_mask = history_ready & (candidate_counts > 0)
    anchor_rows = anchor_candidates[valid_anchor_mask].astype(np.int64, copy=False)
    if anchor_rows.size == 0:
        raise ValueError("Feature table is too short to produce any supervised samples")

    selected_context_starts = context_start_rows[anchor_rows].astype(np.int64, copy=False)
    selected_candidate_ends = candidate_end_rows[anchor_rows].astype(np.int64, copy=False)
    candidate_starts = anchor_rows + 1
    selected_candidate_counts = selected_candidate_ends - candidate_starts
    resolved_max_candidate_slots = (
        int(selected_candidate_counts.max())
        if max_candidate_slots is None
        else int(max_candidate_slots)
    )
    if resolved_max_candidate_slots <= 0:
        raise ValueError("max_candidate_slots must be positive")
    if np.any(selected_candidate_counts > resolved_max_candidate_slots):
        raise ValueError("Configured max_candidate_slots is too small for this dataset")

    return TemporalDatasetStore(
        feature_matrix=feature_matrix,
        log_base_fees=log_base_fees,
        timestamps=timestamps,
        anchor_rows=anchor_rows,
        context_start_rows=selected_context_starts,
        candidate_end_rows=selected_candidate_ends,
        max_candidate_slots=resolved_max_candidate_slots,
    )


def tail_sample_indices(
    store: TemporalDatasetStore,
    *,
    sample_count: int,
) -> IntVector:
    if sample_count <= 0:
        raise ValueError("sample_count must be positive")
    if store.n_samples < sample_count:
        raise ValueError(
            "History dataset is too short for the requested sample count; "
            f"need at least {sample_count} valid anchors, got {store.n_samples}"
        )
    return np.arange(store.n_samples - sample_count, store.n_samples, dtype=np.int64)


def filter_sample_indices_by_timestamp_window(
    store: TemporalDatasetStore,
    *,
    start_timestamp: int,
    end_timestamp: int,
) -> IntVector:
    sample_timestamps = store.timestamps[store.anchor_rows]
    mask = (sample_timestamps >= start_timestamp) & (sample_timestamps < end_timestamp)
    return np.flatnonzero(mask).astype(np.int64, copy=False)


def chronological_split_indices(
    n_samples: int,
    split_config: SplitConfig,
) -> DatasetSplitIndices:
    if n_samples < 3:
        raise ValueError("Need at least three examples to create train/validation/test splits")

    train_end = int(n_samples * split_config.train_fraction)
    validation_end = train_end + int(n_samples * split_config.validation_fraction)
    train_end = max(1, min(train_end, n_samples - 2))
    validation_end = max(train_end + 1, min(validation_end, n_samples - 1))
    all_indices = np.arange(n_samples, dtype=np.int64)
    return DatasetSplitIndices(
        train=all_indices[:train_end],
        validation=all_indices[train_end:validation_end],
        test=all_indices[validation_end:],
    )
