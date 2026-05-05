"""Time and cadence features for core fee-dynamics catalogs."""

from __future__ import annotations

import math

import numpy as np

from ...core import CanonicalBlockSeries, FeatureSpec, FloatVector, IntVector

CADENCE_CALENDAR_OUTPUTS = (
    "seconds_since_previous_block",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
)
ELAPSED_POSITION_OUTPUTS = ("elapsed_seconds",)


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
