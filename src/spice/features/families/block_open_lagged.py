"""Block-open-lagged feature family."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import numpy as np
import polars as pl

from ..core import CanonicalBlockSeries
from . import helpers
from .base import FeatureDefinition, FeatureFamily, FeatureFamilyConfig

FloatVector = helpers.FloatVector


class BlockOpenLaggedFeatureFamilyConfig(FeatureFamilyConfig):
    id: str = "block_open_lagged"


def _rolling_stat(
    resolved_dependencies: Mapping[str, FloatVector],
    *,
    dependency_name: str,
    window: int,
    stat: str,
    ddof: int = 0,
) -> FloatVector:
    return helpers.block_rolling_stat(
        resolved_dependencies[dependency_name],
        window=window,
        stat=stat,
        ddof=ddof,
    )


def _lagged_elapsed_seconds(
    blocks: pl.DataFrame,
    series: CanonicalBlockSeries,
    resolved_dependencies: Mapping[str, FloatVector],
) -> FloatVector:
    del blocks, resolved_dependencies
    if series.timestamps.size == 0:
        return np.empty(0, dtype=np.float64)
    elapsed = series.timestamps.astype(np.float64, copy=False) - float(series.timestamps[0])
    return helpers.shift(elapsed)


def _lagged_dt_seconds(
    blocks: pl.DataFrame,
    series: CanonicalBlockSeries,
    resolved_dependencies: Mapping[str, FloatVector],
) -> FloatVector:
    del blocks, resolved_dependencies
    if series.timestamps.size == 0:
        return np.empty(0, dtype=np.float64)
    result = np.empty(series.timestamps.shape[0], dtype=np.float64)
    deltas = np.diff(series.timestamps.astype(np.float64, copy=False))
    positive_deltas = deltas[deltas > 0]
    median_delta = float(np.median(positive_deltas)) if positive_deltas.size else 0.0
    result[0] = median_delta
    if series.timestamps.size > 1:
        result[1:] = deltas
    return helpers.shift(result)


def _lagged_calendar_feature(
    blocks: pl.DataFrame,
    series: CanonicalBlockSeries,
    resolved_dependencies: Mapping[str, FloatVector],
    *,
    compute,
) -> FloatVector:
    del blocks, resolved_dependencies
    return helpers.shift(compute(series.timestamps))


def _log_base_fee_per_gas(
    blocks: pl.DataFrame,
    series: CanonicalBlockSeries,
    resolved_dependencies: Mapping[str, FloatVector],
) -> FloatVector:
    del series, resolved_dependencies
    return helpers.log1p_column(blocks, "base_fee_per_gas")


def _lagged_log_gas_used(
    blocks: pl.DataFrame,
    series: CanonicalBlockSeries,
    resolved_dependencies: Mapping[str, FloatVector],
) -> FloatVector:
    del series, resolved_dependencies
    return helpers.shift(helpers.log1p_column(blocks, "gas_used"))


def _lagged_log_gas_limit(
    blocks: pl.DataFrame,
    series: CanonicalBlockSeries,
    resolved_dependencies: Mapping[str, FloatVector],
) -> FloatVector:
    del series, resolved_dependencies
    return helpers.shift(helpers.log1p_column(blocks, "gas_limit"))


def _lagged_gas_ratio(
    blocks: pl.DataFrame,
    series: CanonicalBlockSeries,
    resolved_dependencies: Mapping[str, FloatVector],
) -> FloatVector:
    del series, resolved_dependencies
    ratio = helpers.gas_utilization(blocks) * 100.0
    return helpers.shift(ratio)


def _feature_definitions() -> dict[str, FeatureDefinition]:
    features: dict[str, FeatureDefinition] = {
        "log_base_fee_per_gas": FeatureDefinition(
            (),
            0,
            0,
            ("base_fee_per_gas",),
            _log_base_fee_per_gas,
        ),
        "log_gas_used": FeatureDefinition(
            (),
            0,
            1,
            ("gas_used",),
            _lagged_log_gas_used,
        ),
        "log_gas_limit": FeatureDefinition(
            (),
            0,
            1,
            ("gas_limit",),
            _lagged_log_gas_limit,
        ),
        "gas_ratio": FeatureDefinition(
            (),
            0,
            1,
            ("gas_used", "gas_limit"),
            _lagged_gas_ratio,
        ),
        "dt_seconds": FeatureDefinition(
            (),
            0,
            1,
            ("timestamp",),
            _lagged_dt_seconds,
        ),
        "hour_sin": FeatureDefinition(
            (),
            0,
            1,
            ("timestamp",),
            lambda blocks, series, resolved_dependencies: _lagged_calendar_feature(
                blocks,
                series,
                resolved_dependencies,
                compute=helpers.hour_sin,
            ),
        ),
        "hour_cos": FeatureDefinition(
            (),
            0,
            1,
            ("timestamp",),
            lambda blocks, series, resolved_dependencies: _lagged_calendar_feature(
                blocks,
                series,
                resolved_dependencies,
                compute=helpers.hour_cos,
            ),
        ),
        "weekday_sin": FeatureDefinition(
            (),
            0,
            1,
            ("timestamp",),
            lambda blocks, series, resolved_dependencies: _lagged_calendar_feature(
                blocks,
                series,
                resolved_dependencies,
                compute=helpers.weekday_sin,
            ),
        ),
        "weekday_cos": FeatureDefinition(
            (),
            0,
            1,
            ("timestamp",),
            lambda blocks, series, resolved_dependencies: _lagged_calendar_feature(
                blocks,
                series,
                resolved_dependencies,
                compute=helpers.weekday_cos,
            ),
        ),
        "time_since_start": FeatureDefinition(
            (),
            0,
            1,
            ("timestamp",),
            _lagged_elapsed_seconds,
        ),
        "dlog_base_fee": FeatureDefinition(
            ("log_base_fee_per_gas",),
            0,
            1,
            (),
            lambda blocks, series, resolved_dependencies: helpers.delta(
                resolved_dependencies["log_base_fee_per_gas"]
            ),
        ),
        "base_fee_trend": FeatureDefinition(
            ("dlog_base_fee",),
            0,
            1,
            (),
            lambda blocks, series, resolved_dependencies: helpers.binary_trend(
                resolved_dependencies["dlog_base_fee"]
            ),
        ),
    }
    rolling_specs = (
        ("roll{}_mean_logfee", "log_base_fee_per_gas", "mean", 0, 0),
        ("roll{}_std_logfee", "log_base_fee_per_gas", "std", 1, 0),
        ("roll{}_min_logfee", "log_base_fee_per_gas", "min", 0, 0),
        ("roll{}_mean_gr", "gas_ratio", "mean", 0, 1),
        ("roll{}_std_gr", "gas_ratio", "std", 1, 1),
    )
    for window in (10, 50, 200):
        for prefix, dependency_name, stat, ddof, extra_warmup in rolling_specs:
            features[prefix.format(window)] = FeatureDefinition(
                (dependency_name,),
                0,
                window - 1 + extra_warmup,
                (),
                lambda blocks,
                series,
                resolved_dependencies,
                dependency_name=dependency_name,
                window=window,
                stat=stat,
                ddof=ddof: _rolling_stat(
                    resolved_dependencies,
                    dependency_name=dependency_name,
                    window=window,
                    stat=stat,
                    ddof=ddof,
                ),
            )
    for lag in range(1, 7):
        features[f"gas_ratio_lag{lag}"] = FeatureDefinition(
            ("gas_ratio",),
            0,
            lag + 1,
            (),
            lambda blocks, series, resolved_dependencies, lag=lag: helpers.shift(
                resolved_dependencies["gas_ratio"],
                lag=lag,
            ),
        )
        features[f"dlogfee_lag{lag}"] = FeatureDefinition(
            ("dlog_base_fee",),
            0,
            lag + 1,
            (),
            lambda blocks, series, resolved_dependencies, lag=lag: helpers.shift(
                resolved_dependencies["dlog_base_fee"],
                lag=lag,
            ),
        )
    return features


BLOCK_OPEN_LAGGED_FAMILY = FeatureFamily(
    features=_feature_definitions(),
    fingerprint_sources=(Path(__file__).resolve(), Path(helpers.__file__).resolve()),
    build_series=helpers.build_canonical_series,
)
