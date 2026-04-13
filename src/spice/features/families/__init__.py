"""Feature family registry package."""

from .base import (
    FEATURE_HISTORY_SECONDS_TAG,
    FEATURE_KIND_TAG,
    FEATURE_KIND_VALUE,
    FEATURE_WARMUP_ROWS_TAG,
    FeatureFamilyConfig,
    FeatureFamilySpec,
    FeaturePrerequisites,
    tagged_feature_prerequisites,
)
from .registry import (
    coerce_feature_family_config,
    feature_family_spec,
    register_feature_family_spec,
)

__all__ = [
    "FEATURE_HISTORY_SECONDS_TAG",
    "FEATURE_KIND_TAG",
    "FEATURE_KIND_VALUE",
    "FEATURE_WARMUP_ROWS_TAG",
    "FeatureFamilyConfig",
    "FeatureFamilySpec",
    "FeaturePrerequisites",
    "coerce_feature_family_config",
    "feature_family_spec",
    "register_feature_family_spec",
    "tagged_feature_prerequisites",
]
