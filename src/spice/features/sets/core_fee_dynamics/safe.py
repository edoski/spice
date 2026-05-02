"""Safe core fee-dynamics catalog."""

from __future__ import annotations

from pathlib import Path

from ...core import FeatureCatalog, FeatureSpec, SourceSpec
from ._shared import (
    COMMON_FINGERPRINT_SOURCES,
    base_fee_trend_features,
    cadence_calendar_features,
    compose_feature_outputs,
    core_fee_level_features,
    current_base_fee_sources,
    extended_rolling_fee_context_features,
    gas_utilization_rolling_features,
    gas_utilization_trend_features,
    local_fee_context_features,
    previous_block_fact_features,
    previous_block_fact_sources,
)

CORE_FEE_LEVEL_OUTPUTS = (
    "log_base_fee_per_gas",
)
PREVIOUS_BLOCK_FACT_OUTPUTS = (
    "log_prev_gas_used",
    "log_prev_gas_limit",
    "prev_gas_utilization",
    "log_prev_tx_count",
)
CADENCE_CALENDAR_OUTPUTS = (
    "seconds_since_previous_block",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
)
LOCAL_FEE_CONTEXT_OUTPUTS = (
    "roll25_mean_logfee",
    "roll25_std_logfee",
    "roll25_min_logfee",
    "roll100_mean_logfee",
    "roll100_std_logfee",
    "roll100_min_logfee",
)
BASE_FEE_TREND_OUTPUTS = (
    "dlog_base_fee",
    "base_fee_trend",
    *(f"dlog_base_fee_lag{lag}" for lag in range(1, 7)),
)
PREVIOUS_GAS_UTILIZATION_TREND_OUTPUTS = (
    *(f"prev_gas_utilization_lag{lag}" for lag in range(1, 7)),
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
PREVIOUS_GAS_UTILIZATION_ROLLING_OUTPUTS = (
    "roll10_mean_prev_gas_utilization",
    "roll10_std_prev_gas_utilization",
    "roll50_mean_prev_gas_utilization",
    "roll50_std_prev_gas_utilization",
    "roll200_mean_prev_gas_utilization",
    "roll200_std_prev_gas_utilization",
)

CORE_FEE_DYNAMICS_OUTPUTS = compose_feature_outputs(
    CORE_FEE_LEVEL_OUTPUTS,
    PREVIOUS_BLOCK_FACT_OUTPUTS,
    CADENCE_CALENDAR_OUTPUTS,
    LOCAL_FEE_CONTEXT_OUTPUTS,
    BASE_FEE_TREND_OUTPUTS,
    PREVIOUS_GAS_UTILIZATION_TREND_OUTPUTS,
    EXTENDED_ROLLING_FEE_CONTEXT_OUTPUTS,
    PREVIOUS_GAS_UTILIZATION_ROLLING_OUTPUTS,
)


def safe_sources() -> dict[str, SourceSpec]:
    return {
        **current_base_fee_sources(),
        **previous_block_fact_sources(),
    }


def safe_features() -> dict[str, FeatureSpec]:
    return {
        **core_fee_level_features(),
        **previous_block_fact_features(),
        **cadence_calendar_features(),
        **local_fee_context_features(),
        **base_fee_trend_features(),
        **gas_utilization_trend_features("prev_gas_utilization"),
        **extended_rolling_fee_context_features(),
        **gas_utilization_rolling_features("prev_gas_utilization"),
    }


CORE_FEE_DYNAMICS = FeatureCatalog(
    sources=safe_sources(),
    features=safe_features(),
    allowed_outputs=CORE_FEE_DYNAMICS_OUTPUTS,
    fingerprint_sources=(Path(__file__).resolve(), *COMMON_FINGERPRINT_SOURCES),
)
