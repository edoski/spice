"""Rolling local fee context features."""

from __future__ import annotations

from ...core import FeatureSpec
from ._transforms import rolling_stat

LOCAL_FEE_CONTEXT_OUTPUTS = (
    "roll25_mean_logfee",
    "roll25_std_logfee",
    "roll25_min_logfee",
    "roll100_mean_logfee",
    "roll100_std_logfee",
    "roll100_min_logfee",
)
EXTENDED_ROLLING_FEE_CONTEXT_OUTPUTS = (
    "roll10_mean_logfee",
    "roll10_std_logfee",
    "roll10_min_logfee",
    "roll50_mean_logfee",
    "roll50_std_logfee",
    "roll50_min_logfee",
    "roll200_mean_logfee",
    "roll200_std_logfee",
    "roll200_min_logfee",
)


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
