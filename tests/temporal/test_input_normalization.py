from __future__ import annotations

import numpy as np

from spice.temporal.input_normalization import (
    ScalerStats,
    fit_row_standard_scaler,
    transform_feature_matrix,
)
from spice.temporal.problem_store import CompiledProblemStore


def _store() -> CompiledProblemStore:
    return CompiledProblemStore(
        feature_matrix=np.array([[0.0], [1.0], [2.0]], dtype=np.float32),
        log_base_fees=np.zeros(3, dtype=np.float32),
        timestamps=np.arange(3, dtype=np.int64),
        anchor_rows=np.array([0, 2], dtype=np.int64),
        context_start_rows=np.array([0, 0], dtype=np.int64),
        candidate_start_rows=np.array([0, 2], dtype=np.int64),
        candidate_end_rows=np.array([1, 3], dtype=np.int64),
        max_candidate_slots=1,
    )


def test_row_standard_scaler_fits_over_all_feature_rows() -> None:
    scaler = fit_row_standard_scaler(
        _store(),
        sample_indices=np.array([0, 1], dtype=np.int64),
    )

    assert scaler.means == [1.0]
    np.testing.assert_allclose(scaler.scales, [np.sqrt(2.0 / 3.0)])


def test_standard_scaler_stats_use_unit_scale_for_constant_features() -> None:
    store = _store()
    constant_store = CompiledProblemStore(
        feature_matrix=np.ones((3, 1), dtype=np.float32),
        log_base_fees=store.log_base_fees,
        timestamps=store.timestamps,
        anchor_rows=store.anchor_rows,
        context_start_rows=store.context_start_rows,
        candidate_start_rows=store.candidate_start_rows,
        candidate_end_rows=store.candidate_end_rows,
        max_candidate_slots=store.max_candidate_slots,
    )

    scaler = fit_row_standard_scaler(
        constant_store,
        sample_indices=np.array([0, 1], dtype=np.int64),
    )

    assert scaler.means == [1.0]
    assert scaler.scales == [1.0]


def test_transform_feature_matrix_uses_safe_scales_and_float32() -> None:
    transformed = transform_feature_matrix(
        np.array([[2.0, 4.0]], dtype=np.float32),
        ScalerStats(means=[1.0, 1.0], scales=[0.0, -2.0]),
    )

    assert transformed.dtype == np.float32
    np.testing.assert_allclose(transformed, np.array([[1.0, 3.0]], dtype=np.float32))
