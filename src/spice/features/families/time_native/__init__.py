"""Time-native alternate feature family."""

from __future__ import annotations

from ..base import FeatureFamilyConfig, FeatureFamilySpec, tagged_feature_prerequisites
from ..registry import register_feature_family_spec
from . import base, paper, rolling, trend


class TimeNativeFeatureFamilyConfig(FeatureFamilyConfig):
    id: str = "time_native"


register_feature_family_spec(
    FeatureFamilySpec[TimeNativeFeatureFamilyConfig](
        id="time_native",
        config_type=TimeNativeFeatureFamilyConfig,
        modules=(base, rolling, trend, paper),
        resolve_prerequisites=tagged_feature_prerequisites,
    )
)
