"""Base-fee source and trend features."""

from __future__ import annotations

from ...core import FeatureSpec, SourceSpec
from ._transforms import binary_trend, delta, float_column, log_source, shift

CORE_FEE_LEVEL_OUTPUTS = ("log_base_fee_per_gas",)
BASE_FEE_TREND_OUTPUTS = (
    "dlog_base_fee",
    "base_fee_trend",
    *(f"dlog_base_fee_lag{lag}" for lag in range(1, 7)),
)


def current_base_fee_sources() -> dict[str, SourceSpec]:
    return {
        "current_base_fee_per_gas": SourceSpec(
            source_columns=("base_fee_per_gas",),
            warmup_rows=0,
            required_after_warmup=True,
            compute=lambda blocks: float_column(blocks, "base_fee_per_gas"),
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
