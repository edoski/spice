"""Shared compiled problem-store helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from ..config import SplitConfig

FloatMatrix = NDArray[np.float32]
FloatVector = NDArray[np.float32]
IntVector = NDArray[np.int64]
BoolMatrix = NDArray[np.bool_]


@dataclass(slots=True)
class DatasetSplitIndices:
    train: IntVector
    validation: IntVector
    test: IntVector


@dataclass(slots=True)
class CompiledProblemStore:
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


def tail_sample_indices(
    store: CompiledProblemStore,
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
    store: CompiledProblemStore,
    *,
    start_timestamp: int,
    end_timestamp: int,
) -> IntVector:
    sample_timestamps = store.timestamps[store.anchor_rows]
    mask = (sample_timestamps >= start_timestamp) & (sample_timestamps < end_timestamp)
    return np.flatnonzero(mask).astype(np.int64, copy=False)


def build_action_mask(
    store: CompiledProblemStore,
    sample_indices: IntVector,
) -> BoolMatrix:
    resolved_sample_indices = sample_indices.astype(np.int64, copy=False)
    candidate_counts = store.candidate_counts[resolved_sample_indices]
    if np.any(candidate_counts <= 0):
        raise ValueError("action mask requires at least one future candidate per sample")
    if np.any(candidate_counts > store.max_candidate_slots):
        raise ValueError("candidate counts exceed store.max_candidate_slots")
    slot_ids = np.arange(store.max_candidate_slots, dtype=np.int64)
    return (slot_ids[None, :] < candidate_counts[:, None]).astype(np.bool_, copy=False)


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
