"""Shared formula helpers for core fee-dynamics catalogs."""

from __future__ import annotations

import math
from collections.abc import Mapping
from pathlib import Path

import numpy as np
import polars as pl

from ...core import (
    CanonicalBlockSeries,
    FeatureSpec,
    FloatVector,
    IntVector,
    SourceSpec,
)

COMMON_FINGERPRINT_SOURCES = (
    Path(__file__).resolve(),
    Path(__file__).resolve().parents[2] / "core.py",
)


def compose_feature_outputs(*groups: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(output for group in groups for output in group)


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


def elapsed_seconds(series: CanonicalBlockSeries) -> FloatVector:
    if series.timestamps.size == 0:
        return np.empty(0, dtype=np.float64)
    return series.timestamps.astype(np.float64, copy=False) - float(series.timestamps[0])


def dt_seconds(series: CanonicalBlockSeries) -> FloatVector:
    if series.timestamps.size == 0:
        return np.empty(0, dtype=np.float64)
    result = np.empty(series.timestamps.shape[0], dtype=np.float64)
    result[0] = 0.0
    if series.timestamps.size > 1:
        result[1:] = np.diff(series.timestamps.astype(np.float64, copy=False))
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


def hour_sin(timestamps: IntVector) -> FloatVector:
    hours = (timestamps // 3600) % 24
    return np.sin(2.0 * math.pi * hours.astype(np.float64, copy=False) / 24.0)


def hour_cos(timestamps: IntVector) -> FloatVector:
    hours = (timestamps // 3600) % 24
    return np.cos(2.0 * math.pi * hours.astype(np.float64, copy=False) / 24.0)


def dow_sin(timestamps: IntVector) -> FloatVector:
    days = ((timestamps // 86_400) + 4) % 7
    return np.sin(2.0 * math.pi * days.astype(np.float64, copy=False) / 7.0)


def dow_cos(timestamps: IntVector) -> FloatVector:
    days = ((timestamps // 86_400) + 4) % 7
    return np.cos(2.0 * math.pi * days.astype(np.float64, copy=False) / 7.0)


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


def current_base_fee_sources() -> dict[str, SourceSpec]:
    return {
        "current_base_fee_per_gas": SourceSpec(
            source_columns=("base_fee_per_gas",),
            warmup_rows=0,
            required_after_warmup=True,
            compute=lambda blocks: float_column(blocks, "base_fee_per_gas"),
        ),
    }


def previous_block_fact_sources() -> dict[str, SourceSpec]:
    return {
        "prev_gas_used": SourceSpec(
            source_columns=("gas_used",),
            warmup_rows=1,
            required_after_warmup=True,
            compute=lambda blocks: shifted_column(blocks, "gas_used"),
        ),
        "prev_gas_limit": SourceSpec(
            source_columns=("gas_limit",),
            warmup_rows=1,
            required_after_warmup=True,
            compute=lambda blocks: shifted_column(blocks, "gas_limit"),
        ),
        "prev_tx_count": SourceSpec(
            source_columns=("tx_count",),
            warmup_rows=1,
            required_after_warmup=True,
            compute=lambda blocks: shifted_column(blocks, "tx_count"),
        ),
    }


def current_row_block_fact_sources() -> dict[str, SourceSpec]:
    return {
        "current_gas_used": SourceSpec(
            source_columns=("gas_used",),
            warmup_rows=0,
            required_after_warmup=True,
            compute=lambda blocks: float_column(blocks, "gas_used"),
        ),
        "current_gas_limit": SourceSpec(
            source_columns=("gas_limit",),
            warmup_rows=0,
            required_after_warmup=True,
            compute=lambda blocks: float_column(blocks, "gas_limit"),
        ),
        "current_tx_count": SourceSpec(
            source_columns=("tx_count",),
            warmup_rows=0,
            required_after_warmup=True,
            compute=lambda blocks: float_column(blocks, "tx_count"),
        ),
    }


def priority_fee_sources() -> dict[str, SourceSpec]:
    return {
        "prev_priority_fee_p10": SourceSpec(
            source_columns=("priority_fee_p10",),
            warmup_rows=1,
            required_after_warmup=True,
            compute=lambda blocks: shifted_column(blocks, "priority_fee_p10"),
        ),
        "prev_priority_fee_p50": SourceSpec(
            source_columns=("priority_fee_p50",),
            warmup_rows=1,
            required_after_warmup=True,
            compute=lambda blocks: shifted_column(blocks, "priority_fee_p50"),
        ),
        "prev_priority_fee_p90": SourceSpec(
            source_columns=("priority_fee_p90",),
            warmup_rows=1,
            required_after_warmup=True,
            compute=lambda blocks: shifted_column(blocks, "priority_fee_p90"),
        ),
        "prev_priority_fee_spread": SourceSpec(
            source_columns=("priority_fee_spread",),
            warmup_rows=1,
            required_after_warmup=True,
            compute=lambda blocks: shifted_column(blocks, "priority_fee_spread"),
        ),
    }


def core_fee_level_features() -> dict[str, FeatureSpec]:
    return {
        "log_base_fee_per_gas": FeatureSpec(
            source_dependencies=("current_base_fee_per_gas",),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=0,
            compute=lambda blocks, series, sources, features: log_source(
                sources,
                "current_base_fee_per_gas",
            ),
        ),
    }


def previous_block_fact_features() -> dict[str, FeatureSpec]:
    return {
        "log_prev_gas_used": FeatureSpec(
            source_dependencies=("prev_gas_used",),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=1,
            compute=lambda blocks, series, sources, features: log1p(sources["prev_gas_used"]),
        ),
        "log_prev_gas_limit": FeatureSpec(
            source_dependencies=("prev_gas_limit",),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=1,
            compute=lambda blocks, series, sources, features: log1p(sources["prev_gas_limit"]),
        ),
        "prev_gas_utilization": FeatureSpec(
            source_dependencies=("prev_gas_used", "prev_gas_limit"),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=1,
            compute=lambda blocks, series, sources, features: gas_utilization(
                sources["prev_gas_used"],
                sources["prev_gas_limit"],
            ),
        ),
        "log_prev_tx_count": FeatureSpec(
            source_dependencies=("prev_tx_count",),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=1,
            compute=lambda blocks, series, sources, features: log1p(sources["prev_tx_count"]),
        ),
    }


def current_row_block_fact_features() -> dict[str, FeatureSpec]:
    return {
        "log_current_gas_used": FeatureSpec(
            source_dependencies=("current_gas_used",),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=0,
            compute=lambda blocks, series, sources, features: log1p(
                sources["current_gas_used"]
            ),
        ),
        "log_current_gas_limit": FeatureSpec(
            source_dependencies=("current_gas_limit",),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=0,
            compute=lambda blocks, series, sources, features: log1p(
                sources["current_gas_limit"]
            ),
        ),
        "current_gas_utilization": FeatureSpec(
            source_dependencies=("current_gas_used", "current_gas_limit"),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=0,
            compute=lambda blocks, series, sources, features: gas_utilization(
                sources["current_gas_used"],
                sources["current_gas_limit"],
            ),
        ),
        "log_current_tx_count": FeatureSpec(
            source_dependencies=("current_tx_count",),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=0,
            compute=lambda blocks, series, sources, features: log1p(
                sources["current_tx_count"]
            ),
        ),
    }


def cadence_calendar_features() -> dict[str, FeatureSpec]:
    return {
        "seconds_since_previous_block": FeatureSpec(
            source_dependencies=(),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=1,
            compute=lambda blocks, series, sources, features: dt_seconds(series),
        ),
        "hour_sin": FeatureSpec(
            source_dependencies=(),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=0,
            compute=lambda blocks, series, sources, features: hour_sin(series.timestamps),
        ),
        "hour_cos": FeatureSpec(
            source_dependencies=(),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=0,
            compute=lambda blocks, series, sources, features: hour_cos(series.timestamps),
        ),
        "dow_sin": FeatureSpec(
            source_dependencies=(),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=0,
            compute=lambda blocks, series, sources, features: dow_sin(series.timestamps),
        ),
        "dow_cos": FeatureSpec(
            source_dependencies=(),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=0,
            compute=lambda blocks, series, sources, features: dow_cos(series.timestamps),
        ),
    }


def elapsed_position_features() -> dict[str, FeatureSpec]:
    return {
        "elapsed_seconds": FeatureSpec(
            source_dependencies=(),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=0,
            compute=lambda blocks, series, sources, features: elapsed_seconds(series),
        ),
    }


def local_fee_context_features() -> dict[str, FeatureSpec]:
    features: dict[str, FeatureSpec] = {}
    for window in (25, 100):
        features[f"roll{window}_mean_logfee"] = FeatureSpec(
            source_dependencies=(),
            feature_dependencies=("log_base_fee_per_gas",),
            history_seconds=0,
            warmup_rows=window - 1,
            compute=lambda blocks, series, sources, features, window=window: rolling_stat(
                features["log_base_fee_per_gas"],
                window=window,
                stat="mean",
            ),
        )
        features[f"roll{window}_std_logfee"] = FeatureSpec(
            source_dependencies=(),
            feature_dependencies=("log_base_fee_per_gas",),
            history_seconds=0,
            warmup_rows=window - 1,
            compute=lambda blocks, series, sources, features, window=window: rolling_stat(
                features["log_base_fee_per_gas"],
                window=window,
                stat="std",
            ),
        )
        features[f"roll{window}_min_logfee"] = FeatureSpec(
            source_dependencies=(),
            feature_dependencies=("log_base_fee_per_gas",),
            history_seconds=0,
            warmup_rows=window - 1,
            compute=lambda blocks, series, sources, features, window=window: rolling_stat(
                features["log_base_fee_per_gas"],
                window=window,
                stat="min",
            ),
        )
    return features


def extended_rolling_fee_context_features() -> dict[str, FeatureSpec]:
    features: dict[str, FeatureSpec] = {}
    for window in (10, 50, 200):
        features[f"roll{window}_mean_logfee"] = FeatureSpec(
            source_dependencies=(),
            feature_dependencies=("log_base_fee_per_gas",),
            history_seconds=0,
            warmup_rows=window - 1,
            compute=lambda blocks, series, sources, features, window=window: rolling_stat(
                features["log_base_fee_per_gas"],
                window=window,
                stat="mean",
            ),
        )
        features[f"roll{window}_std_logfee"] = FeatureSpec(
            source_dependencies=(),
            feature_dependencies=("log_base_fee_per_gas",),
            history_seconds=0,
            warmup_rows=window - 1,
            compute=lambda blocks, series, sources, features, window=window: rolling_stat(
                features["log_base_fee_per_gas"],
                window=window,
                stat="std",
                ddof=1,
            ),
        )
        features[f"roll{window}_min_logfee"] = FeatureSpec(
            source_dependencies=(),
            feature_dependencies=("log_base_fee_per_gas",),
            history_seconds=0,
            warmup_rows=window - 1,
            compute=lambda blocks, series, sources, features, window=window: rolling_stat(
                features["log_base_fee_per_gas"],
                window=window,
                stat="min",
            ),
        )
    return features


def base_fee_trend_features() -> dict[str, FeatureSpec]:
    features = {
        "dlog_base_fee": FeatureSpec(
            source_dependencies=(),
            feature_dependencies=("log_base_fee_per_gas",),
            history_seconds=0,
            warmup_rows=1,
            compute=lambda blocks, series, sources, features: delta(
                features["log_base_fee_per_gas"]
            ),
        ),
        "base_fee_trend": FeatureSpec(
            source_dependencies=(),
            feature_dependencies=("dlog_base_fee",),
            history_seconds=0,
            warmup_rows=1,
            compute=lambda blocks, series, sources, features: binary_trend(
                features["dlog_base_fee"]
            ),
        ),
    }
    for lag in range(1, 7):
        features[f"dlog_base_fee_lag{lag}"] = FeatureSpec(
            source_dependencies=(),
            feature_dependencies=("dlog_base_fee",),
            history_seconds=0,
            warmup_rows=lag + 1,
            compute=lambda blocks, series, sources, features, lag=lag: shift(
                features["dlog_base_fee"],
                lag=lag,
            ),
        )
    return features


def gas_utilization_trend_features(feature_name: str) -> dict[str, FeatureSpec]:
    return {
        f"{feature_name}_lag{lag}": FeatureSpec(
            source_dependencies=(),
            feature_dependencies=(feature_name,),
            history_seconds=0,
            warmup_rows=lag + (1 if feature_name == "prev_gas_utilization" else 0),
            compute=lambda blocks, series, sources, features, lag=lag: shift(
                features[feature_name],
                lag=lag,
            ),
        )
        for lag in range(1, 7)
    }


def gas_utilization_rolling_features(feature_name: str) -> dict[str, FeatureSpec]:
    features: dict[str, FeatureSpec] = {}
    warmup_offset = 1 if feature_name == "prev_gas_utilization" else 0
    for window in (10, 50, 200):
        features[f"roll{window}_mean_{feature_name}"] = FeatureSpec(
            source_dependencies=(),
            feature_dependencies=(feature_name,),
            history_seconds=0,
            warmup_rows=window - 1 + warmup_offset,
            compute=lambda blocks, series, sources, features, window=window: rolling_stat(
                features[feature_name],
                window=window,
                stat="mean",
            ),
        )
        features[f"roll{window}_std_{feature_name}"] = FeatureSpec(
            source_dependencies=(),
            feature_dependencies=(feature_name,),
            history_seconds=0,
            warmup_rows=window - 1 + warmup_offset,
            compute=lambda blocks, series, sources, features, window=window: rolling_stat(
                features[feature_name],
                window=window,
                stat="std",
                ddof=1,
            ),
        )
    return features


def priority_fee_features() -> dict[str, FeatureSpec]:
    features: dict[str, FeatureSpec] = {
        "prev_priority_fee_p10": FeatureSpec(
            source_dependencies=("prev_priority_fee_p10",),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=1,
            compute=lambda blocks, series, sources, features: sources["prev_priority_fee_p10"],
        ),
        "prev_priority_fee_p50": FeatureSpec(
            source_dependencies=("prev_priority_fee_p50",),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=1,
            compute=lambda blocks, series, sources, features: sources["prev_priority_fee_p50"],
        ),
        "prev_priority_fee_p90": FeatureSpec(
            source_dependencies=("prev_priority_fee_p90",),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=1,
            compute=lambda blocks, series, sources, features: sources["prev_priority_fee_p90"],
        ),
        "prev_priority_fee_spread": FeatureSpec(
            source_dependencies=("prev_priority_fee_spread",),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=1,
            compute=lambda blocks, series, sources, features: sources[
                "prev_priority_fee_spread"
            ],
        ),
        "log_prev_priority_fee_p50": FeatureSpec(
            source_dependencies=("prev_priority_fee_p50",),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=1,
            compute=lambda blocks, series, sources, features: log1p(
                sources["prev_priority_fee_p50"]
            ),
        ),
        "log_prev_priority_fee_spread": FeatureSpec(
            source_dependencies=("prev_priority_fee_spread",),
            feature_dependencies=(),
            history_seconds=0,
            warmup_rows=1,
            compute=lambda blocks, series, sources, features: log1p(
                sources["prev_priority_fee_spread"]
            ),
        ),
        "dlog_prev_priority_fee_p50": FeatureSpec(
            source_dependencies=(),
            feature_dependencies=("log_prev_priority_fee_p50",),
            history_seconds=0,
            warmup_rows=2,
            compute=lambda blocks, series, sources, features: delta(
                features["log_prev_priority_fee_p50"]
            ),
        ),
        "dlog_prev_priority_fee_spread": FeatureSpec(
            source_dependencies=(),
            feature_dependencies=("log_prev_priority_fee_spread",),
            history_seconds=0,
            warmup_rows=2,
            compute=lambda blocks, series, sources, features: delta(
                features["log_prev_priority_fee_spread"]
            ),
        ),
    }
    for window in (10, 50, 200):
        for priority_name in ("p50", "spread"):
            log_feature = f"log_prev_priority_fee_{priority_name}"
            features[f"roll{window}_mean_{log_feature}"] = FeatureSpec(
                source_dependencies=(),
                feature_dependencies=(log_feature,),
                history_seconds=0,
                warmup_rows=window,
                compute=rolling_feature(log_feature, window=window, stat="mean"),
            )
            features[f"roll{window}_std_{log_feature}"] = FeatureSpec(
                source_dependencies=(),
                feature_dependencies=(log_feature,),
                history_seconds=0,
                warmup_rows=window,
                compute=rolling_feature(log_feature, window=window, stat="std", ddof=1),
            )
    for lag in range(1, 7):
        for priority_name in ("p50", "spread"):
            dlog_feature = f"dlog_prev_priority_fee_{priority_name}"
            features[f"{dlog_feature}_lag{lag}"] = FeatureSpec(
                source_dependencies=(),
                feature_dependencies=(dlog_feature,),
                history_seconds=0,
                warmup_rows=lag + 2,
                compute=shift_feature(dlog_feature, lag=lag),
            )
    return features
