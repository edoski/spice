"""Numeric transforms for core fee-dynamics feature formulas."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import polars as pl

from ...core import CanonicalBlockSeries, FloatVector


def float_column(blocks: pl.DataFrame, column: str) -> FloatVector:
    return blocks[column].cast(pl.Float64).to_numpy().astype(np.float64, copy=False)


def log1p(values: FloatVector) -> FloatVector:
    return np.log1p(np.clip(values, 0.0, None))


def log_source(sources: Mapping[str, FloatVector], name: str) -> FloatVector:
    return np.log(np.clip(sources[name], 1.0, None))


def delta(values: FloatVector) -> FloatVector:
    result = np.full(values.shape[0], np.nan, dtype=np.float64)
    if values.size > 1:
        result[1:] = np.diff(values)
    return result


def binary_trend(values: FloatVector) -> FloatVector:
    result = np.full(values.shape[0], np.nan, dtype=np.float64)
    valid = np.isfinite(values)
    result[valid] = np.where(values[valid] >= 0.0, 1.0, -1.0)
    return result


def gas_utilization(values_used: FloatVector, values_limit: FloatVector) -> FloatVector:
    result = np.full(values_used.shape[0], np.nan, dtype=np.float64)
    valid = values_limit > 0.0
    result[valid] = values_used[valid] / values_limit[valid]
    return result


def shifted_column(blocks: pl.DataFrame, column: str, *, lag: int = 1) -> FloatVector:
    return shift(float_column(blocks, column), lag=lag)


def shift(values: FloatVector, *, lag: int = 1) -> FloatVector:
    if lag <= 0:
        raise ValueError("lag must be positive")
    result = np.full(values.shape[0], np.nan, dtype=np.float64)
    if values.size > lag:
        result[lag:] = values[:-lag]
    return result


def rolling_stat(values: FloatVector, *, window: int, stat: str, ddof: int = 0) -> FloatVector:
    if values.size == 0:
        return np.empty(0, dtype=np.float64)
    series = pl.Series(values)
    if stat == "mean":
        result = series.rolling_mean(window_size=window, min_samples=window)
    elif stat == "std":
        result = series.rolling_std(window_size=window, min_samples=window, ddof=ddof)
    elif stat == "min":
        result = series.rolling_min(window_size=window, min_samples=window)
    else:  # pragma: no cover
        raise ValueError(f"Unsupported rolling stat: {stat}")
    return result.to_numpy().astype(np.float64, copy=False)


def rolling_feature(
    feature_name: str,
    *,
    window: int,
    stat: str,
    ddof: int = 0,
):
    def _compute(
        blocks: pl.DataFrame,
        series: CanonicalBlockSeries,
        sources: Mapping[str, FloatVector],
        features: Mapping[str, FloatVector],
    ) -> FloatVector:
        return rolling_stat(features[feature_name], window=window, stat=stat, ddof=ddof)

    return _compute


def shift_feature(feature_name: str, *, lag: int):
    def _compute(
        blocks: pl.DataFrame,
        series: CanonicalBlockSeries,
        sources: Mapping[str, FloatVector],
        features: Mapping[str, FloatVector],
    ) -> FloatVector:
        return shift(features[feature_name], lag=lag)

    return _compute
