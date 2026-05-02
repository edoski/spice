"""Unsafe same-block gas/tx comparator catalog."""

from __future__ import annotations

from pathlib import Path

from ...core import FeatureCatalog
from ._shared import (
    COMMON_FINGERPRINT_SOURCES,
    base_fee_trend_features,
    cadence_calendar_features,
    compose_feature_outputs,
    core_fee_level_features,
    current_base_fee_sources,
    current_row_block_fact_features,
    current_row_block_fact_sources,
    extended_rolling_fee_context_features,
    gas_utilization_rolling_features,
    gas_utilization_trend_features,
    local_fee_context_features,
)
from .safe import (
    BASE_FEE_TREND_OUTPUTS,
    CADENCE_CALENDAR_OUTPUTS,
    CORE_FEE_LEVEL_OUTPUTS,
    EXTENDED_ROLLING_FEE_CONTEXT_OUTPUTS,
    LOCAL_FEE_CONTEXT_OUTPUTS,
)

CURRENT_ROW_BLOCK_FACT_OUTPUTS = (
    "log_current_gas_used",
    "log_current_gas_limit",
    "current_gas_utilization",
    "log_current_tx_count",
)
CURRENT_ROW_GAS_UTILIZATION_TREND_OUTPUTS = (
    *(f"current_gas_utilization_lag{lag}" for lag in range(1, 7)),
)
CURRENT_ROW_GAS_UTILIZATION_ROLLING_OUTPUTS = (
    "roll10_mean_current_gas_utilization",
    "roll10_std_current_gas_utilization",
    "roll50_mean_current_gas_utilization",
    "roll50_std_current_gas_utilization",
    "roll200_mean_current_gas_utilization",
    "roll200_std_current_gas_utilization",
)

CORE_FEE_DYNAMICS_UNSAFE_OUTPUTS = compose_feature_outputs(
    CORE_FEE_LEVEL_OUTPUTS,
    CURRENT_ROW_BLOCK_FACT_OUTPUTS,
    CADENCE_CALENDAR_OUTPUTS,
    LOCAL_FEE_CONTEXT_OUTPUTS,
    BASE_FEE_TREND_OUTPUTS,
    CURRENT_ROW_GAS_UTILIZATION_TREND_OUTPUTS,
    EXTENDED_ROLLING_FEE_CONTEXT_OUTPUTS,
    CURRENT_ROW_GAS_UTILIZATION_ROLLING_OUTPUTS,
)

CORE_FEE_DYNAMICS_UNSAFE = FeatureCatalog(
    sources={
        **current_base_fee_sources(),
        **current_row_block_fact_sources(),
    },
    features={
        **core_fee_level_features(),
        **current_row_block_fact_features(),
        **cadence_calendar_features(),
        **local_fee_context_features(),
        **base_fee_trend_features(),
        **gas_utilization_trend_features("current_gas_utilization"),
        **extended_rolling_fee_context_features(),
        **gas_utilization_rolling_features("current_gas_utilization"),
    },
    allowed_outputs=CORE_FEE_DYNAMICS_UNSAFE_OUTPUTS,
    fingerprint_sources=(Path(__file__).resolve(), *COMMON_FINGERPRINT_SOURCES),
)
