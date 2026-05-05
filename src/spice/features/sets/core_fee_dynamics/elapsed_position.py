"""Elapsed-position ablation catalog."""

from __future__ import annotations

from pathlib import Path

from ...core import FeatureCatalog
from . import _base_fee, _block_facts, _fee_context, _time, _transforms
from ._base_fee import (
    BASE_FEE_TREND_OUTPUTS,
    CORE_FEE_LEVEL_OUTPUTS,
    base_fee_trend_features,
    core_fee_level_features,
    current_base_fee_sources,
)
from ._block_facts import (
    PREVIOUS_BLOCK_FACT_OUTPUTS,
    PREVIOUS_GAS_UTILIZATION_ROLLING_OUTPUTS,
    PREVIOUS_GAS_UTILIZATION_TREND_OUTPUTS,
    gas_utilization_rolling_features,
    gas_utilization_trend_features,
    previous_block_fact_features,
    previous_block_fact_sources,
)
from ._fee_context import (
    EXTENDED_ROLLING_FEE_CONTEXT_OUTPUTS,
    LOCAL_FEE_CONTEXT_OUTPUTS,
    extended_rolling_fee_context_features,
    local_fee_context_features,
)
from ._time import (
    CADENCE_CALENDAR_OUTPUTS,
    ELAPSED_POSITION_OUTPUTS,
    cadence_calendar_features,
    elapsed_position_features,
)

CORE_FEE_DYNAMICS_OUTPUTS = (
    *CORE_FEE_LEVEL_OUTPUTS,
    *PREVIOUS_BLOCK_FACT_OUTPUTS,
    *CADENCE_CALENDAR_OUTPUTS,
    *LOCAL_FEE_CONTEXT_OUTPUTS,
    *BASE_FEE_TREND_OUTPUTS,
    *PREVIOUS_GAS_UTILIZATION_TREND_OUTPUTS,
    *EXTENDED_ROLLING_FEE_CONTEXT_OUTPUTS,
    *PREVIOUS_GAS_UTILIZATION_ROLLING_OUTPUTS,
)
CORE_FEE_DYNAMICS_ELAPSED_POSITION_OUTPUTS = (
    *CORE_FEE_DYNAMICS_OUTPUTS,
    *ELAPSED_POSITION_OUTPUTS,
)
CORE_FEE_DYNAMICS_ELAPSED_POSITION_FINGERPRINT_SOURCES = (
    Path(__file__).resolve(),
    Path(_transforms.__file__).resolve(),
    Path(_time.__file__).resolve(),
    Path(_base_fee.__file__).resolve(),
    Path(_block_facts.__file__).resolve(),
    Path(_fee_context.__file__).resolve(),
    Path(__file__).resolve().parents[2] / "core.py",
)

CORE_FEE_DYNAMICS_ELAPSED_POSITION = FeatureCatalog(
    sources={
        **current_base_fee_sources(),
        **previous_block_fact_sources(),
    },
    features={
        **core_fee_level_features(),
        **previous_block_fact_features(),
        **cadence_calendar_features(),
        **local_fee_context_features(),
        **base_fee_trend_features(),
        **gas_utilization_trend_features(
            "prev_gas_utilization",
            base_warmup_rows=1,
        ),
        **extended_rolling_fee_context_features(),
        **gas_utilization_rolling_features(
            "prev_gas_utilization",
            base_warmup_rows=1,
        ),
        **elapsed_position_features(),
    },
    allowed_outputs=CORE_FEE_DYNAMICS_ELAPSED_POSITION_OUTPUTS,
    fingerprint_sources=CORE_FEE_DYNAMICS_ELAPSED_POSITION_FINGERPRINT_SOURCES,
)
