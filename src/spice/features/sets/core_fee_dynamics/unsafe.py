"""Unsafe same-block gas/tx comparator catalog."""

from __future__ import annotations

from pathlib import Path

from ...core import FeatureCatalog
from . import _base_fee, _block_facts, _fee_context, _time, _transforms
from ._base_fee import (
    BASE_FEE_TREND_OUTPUTS,
    base_fee_trend_features,
    core_fee_level_features,
    current_base_fee_sources,
)
from ._block_facts import (
    CURRENT_ROW_BLOCK_FACT_OUTPUTS,
    CURRENT_ROW_GAS_UTILIZATION_ROLLING_OUTPUTS,
    CURRENT_ROW_GAS_UTILIZATION_TREND_OUTPUTS,
    current_row_block_fact_features,
    current_row_block_fact_sources,
    gas_utilization_rolling_features,
    gas_utilization_trend_features,
)
from ._fee_context import (
    EXTENDED_ROLLING_FEE_CONTEXT_OUTPUTS,
    LOCAL_FEE_CONTEXT_OUTPUTS,
    extended_rolling_fee_context_features,
    local_fee_context_features,
)
from ._time import CADENCE_CALENDAR_OUTPUTS, cadence_calendar_features

CORE_FEE_LEVEL_OUTPUTS = _base_fee.CORE_FEE_LEVEL_OUTPUTS
CORE_FEE_DYNAMICS_UNSAFE_OUTPUTS = (
    *CORE_FEE_LEVEL_OUTPUTS,
    *CURRENT_ROW_BLOCK_FACT_OUTPUTS,
    *CADENCE_CALENDAR_OUTPUTS,
    *LOCAL_FEE_CONTEXT_OUTPUTS,
    *BASE_FEE_TREND_OUTPUTS,
    *CURRENT_ROW_GAS_UTILIZATION_TREND_OUTPUTS,
    *EXTENDED_ROLLING_FEE_CONTEXT_OUTPUTS,
    *CURRENT_ROW_GAS_UTILIZATION_ROLLING_OUTPUTS,
)
CORE_FEE_DYNAMICS_UNSAFE_FINGERPRINT_SOURCES = (
    Path(__file__).resolve(),
    Path(_transforms.__file__).resolve(),
    Path(_time.__file__).resolve(),
    Path(_base_fee.__file__).resolve(),
    Path(_block_facts.__file__).resolve(),
    Path(_fee_context.__file__).resolve(),
    Path(__file__).resolve().parents[2] / "core.py",
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
        **gas_utilization_trend_features(
            "current_gas_utilization",
            base_warmup_rows=0,
        ),
        **extended_rolling_fee_context_features(),
        **gas_utilization_rolling_features(
            "current_gas_utilization",
            base_warmup_rows=0,
        ),
    },
    allowed_outputs=CORE_FEE_DYNAMICS_UNSAFE_OUTPUTS,
    fingerprint_sources=CORE_FEE_DYNAMICS_UNSAFE_FINGERPRINT_SOURCES,
)
