"""Elapsed-position ablation catalog."""

from __future__ import annotations

from pathlib import Path

from ...core import FeatureCatalog
from ._shared import (
    COMMON_FINGERPRINT_SOURCES,
    compose_feature_outputs,
    elapsed_position_features,
)
from .safe import CORE_FEE_DYNAMICS_OUTPUTS, safe_features, safe_sources

ELAPSED_POSITION_OUTPUTS = (
    "elapsed_seconds",
)

CORE_FEE_DYNAMICS_ELAPSED_POSITION_OUTPUTS = compose_feature_outputs(
    CORE_FEE_DYNAMICS_OUTPUTS,
    ELAPSED_POSITION_OUTPUTS,
)

CORE_FEE_DYNAMICS_ELAPSED_POSITION = FeatureCatalog(
    sources=safe_sources(),
    features={
        **safe_features(),
        **elapsed_position_features(),
    },
    allowed_outputs=CORE_FEE_DYNAMICS_ELAPSED_POSITION_OUTPUTS,
    fingerprint_sources=(Path(__file__).resolve(), *COMMON_FINGERPRINT_SOURCES),
)
