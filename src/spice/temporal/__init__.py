"""Timestamp-native sample geometry ownership."""

from .contracts import ResolvedTaskContract, resolve_feature_contract, resolve_task_contract
from .scaling import ScalerStats, fit_standard_scaler, transform_feature_matrix
from .store import (
    DatasetSplitIndices,
    TemporalDatasetStore,
    build_temporal_store,
    chronological_split_indices,
    filter_sample_indices_by_timestamp_window,
    tail_sample_indices,
)
from .window import DelayWindow

__all__ = [
    "DatasetSplitIndices",
    "DelayWindow",
    "ResolvedTaskContract",
    "ScalerStats",
    "TemporalDatasetStore",
    "build_temporal_store",
    "chronological_split_indices",
    "filter_sample_indices_by_timestamp_window",
    "fit_standard_scaler",
    "resolve_feature_contract",
    "resolve_task_contract",
    "tail_sample_indices",
    "transform_feature_matrix",
]
