"""Paper-aligned block-native feature family."""

from __future__ import annotations

from ..base import FeatureFamilyConfig, FeatureFamilySpec, tagged_feature_prerequisites
from ..registry import register_feature_family_spec
from . import base, rolling, trend


class BlockNativeFeatureFamilyConfig(FeatureFamilyConfig):
    id: str = "block_native"


register_feature_family_spec(
    FeatureFamilySpec(
        id="block_native",
        config_type=BlockNativeFeatureFamilyConfig,
        modules=(base, rolling, trend),
        resolve_prerequisites=tagged_feature_prerequisites,
    )
)
