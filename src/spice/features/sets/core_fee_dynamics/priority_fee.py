"""Priority-fee extended core fee-dynamics catalog."""

from __future__ import annotations

from pathlib import Path

from ...core import FeatureCatalog
from ._shared import COMMON_FINGERPRINT_SOURCES, compose_feature_outputs, priority_fee_sources
from ._shared import priority_fee_features as build_priority_fee_features
from .safe import CORE_FEE_DYNAMICS_OUTPUTS, safe_features, safe_sources

PRIORITY_FEE_OUTPUTS = (
    "prev_priority_fee_p10",
    "prev_priority_fee_p50",
    "prev_priority_fee_p90",
    "prev_priority_fee_spread",
    "log_prev_priority_fee_p50",
    "dlog_prev_priority_fee_p50",
    *(f"dlog_prev_priority_fee_p50_lag{lag}" for lag in range(1, 7)),
    "roll10_mean_log_prev_priority_fee_p50",
    "roll10_std_log_prev_priority_fee_p50",
    "roll50_mean_log_prev_priority_fee_p50",
    "roll50_std_log_prev_priority_fee_p50",
    "roll200_mean_log_prev_priority_fee_p50",
    "roll200_std_log_prev_priority_fee_p50",
    "log_prev_priority_fee_spread",
    "dlog_prev_priority_fee_spread",
    *(f"dlog_prev_priority_fee_spread_lag{lag}" for lag in range(1, 7)),
    "roll10_mean_log_prev_priority_fee_spread",
    "roll10_std_log_prev_priority_fee_spread",
    "roll50_mean_log_prev_priority_fee_spread",
    "roll50_std_log_prev_priority_fee_spread",
    "roll200_mean_log_prev_priority_fee_spread",
    "roll200_std_log_prev_priority_fee_spread",
)

CORE_FEE_DYNAMICS_PRIORITY_FEE_OUTPUTS = compose_feature_outputs(
    CORE_FEE_DYNAMICS_OUTPUTS,
    PRIORITY_FEE_OUTPUTS,
)

CORE_FEE_DYNAMICS_PRIORITY_FEE = FeatureCatalog(
    sources={
        **safe_sources(),
        **priority_fee_sources(),
    },
    features={
        **safe_features(),
        **build_priority_fee_features(),
    },
    allowed_outputs=CORE_FEE_DYNAMICS_PRIORITY_FEE_OUTPUTS,
    fingerprint_sources=(Path(__file__).resolve(), *COMMON_FINGERPRINT_SOURCES),
)
