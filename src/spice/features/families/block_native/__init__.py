"""Paper-aligned block-native feature family."""

from __future__ import annotations

from typing import Literal, cast

from ...contracts import compile_feature_contract_for_family
from ..base import FeatureFamilyConfig, FeatureFamilySpec, tagged_feature_prerequisites
from ..registry import register_feature_family_spec
from . import base, rolling, trend


class BlockNativeFeatureFamilyConfig(FeatureFamilyConfig):
    id: Literal["block_native"] = "block_native"


register_feature_family_spec(
    FeatureFamilySpec[BlockNativeFeatureFamilyConfig](
        id="block_native",
        config_type=BlockNativeFeatureFamilyConfig,
        modules=(base, rolling, trend),
        compile_contract=cast(object, compile_feature_contract_for_family),
        resolve_prerequisites=cast(object, tagged_feature_prerequisites),
    )
)
