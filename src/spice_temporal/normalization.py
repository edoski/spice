"""Feature normalization utilities."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatMatrix = NDArray[np.float32]
FloatVector = NDArray[np.float32]
IntVector = NDArray[np.int64]


@dataclass(slots=True)
class StandardScaler:
    means: list[float]
    stds: list[float]


def window_row_multiplicities(
    *,
    anchor_row_indices: IntVector,
    sample_indices: IntVector,
    lookback_steps: int,
    n_rows: int,
) -> IntVector:
    if lookback_steps <= 0:
        raise ValueError("lookback_steps must be positive")
    if n_rows <= 0:
        raise ValueError("n_rows must be positive")
    if sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")

    counts = np.zeros(n_rows + 1, dtype=np.int64)
    selected_anchor_rows = anchor_row_indices[sample_indices]
    starts = selected_anchor_rows - lookback_steps + 1
    ends = selected_anchor_rows + 1
    np.add.at(counts, starts, 1)
    np.add.at(counts, ends, -1)
    return np.cumsum(counts[:-1], dtype=np.int64)


def fit_standard_scaler(
    feature_matrix: FloatMatrix,
    *,
    anchor_row_indices: IntVector,
    sample_indices: IntVector,
    lookback_steps: int,
) -> StandardScaler:
    if feature_matrix.size == 0:
        raise ValueError("feature_matrix must be non-empty")

    multiplicities = window_row_multiplicities(
        anchor_row_indices=anchor_row_indices,
        sample_indices=sample_indices,
        lookback_steps=lookback_steps,
        n_rows=int(feature_matrix.shape[0]),
    )
    weights = multiplicities.astype(np.float64, copy=False)
    total_weight = float(weights.sum())
    if total_weight <= 0.0:
        raise ValueError("training windows did not cover any feature rows")

    weighted_matrix = feature_matrix.astype(np.float64, copy=False) * weights[:, None]
    totals = weighted_matrix.sum(axis=0)
    totals_sq = (feature_matrix.astype(np.float64, copy=False) ** 2 * weights[:, None]).sum(axis=0)
    means = totals / total_weight
    variances = np.maximum(totals_sq / total_weight - means * means, 0.0)
    stds = np.sqrt(variances)
    return StandardScaler(means=means.tolist(), stds=stds.tolist())


def transform_feature_matrix(feature_matrix: FloatMatrix, scaler: StandardScaler) -> FloatMatrix:
    means = np.asarray(scaler.means, dtype=np.float32)
    stds = np.asarray(scaler.stds, dtype=np.float32)
    centered = feature_matrix - means
    safe_stds = np.where(stds > 0.0, stds, np.float32(1.0))
    return (centered / safe_stds).astype(np.float32, copy=False)
