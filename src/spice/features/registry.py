"""Feature-family lookup for the fixed in-repo families."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..core.errors import ConfigResolutionError
from ..core.specs import lookup_local_spec, require_mapping_id
from .core import validate_feature_names
from .families.base import FeatureFamily, FeatureFamilyConfig
from .families.block_open_lagged import (
    BLOCK_OPEN_LAGGED_FAMILY,
    BlockOpenLaggedFeatureFamilyConfig,
)
from .families.same_block_closed import (
    SAME_BLOCK_CLOSED_FAMILY,
    SameBlockClosedFeatureFamilyConfig,
)
from .families.timestamp_features import (
    TIMESTAMP_FEATURES_FAMILY,
    TimestampFeaturesFeatureFamilyConfig,
)


@dataclass(frozen=True, slots=True)
class _FeatureFamilyEntry:
    config_type: type[FeatureFamilyConfig]
    family: FeatureFamily


_FEATURE_FAMILIES: dict[str, _FeatureFamilyEntry] = {
    "same_block_closed": _FeatureFamilyEntry(
        config_type=SameBlockClosedFeatureFamilyConfig,
        family=SAME_BLOCK_CLOSED_FAMILY,
    ),
    "block_open_lagged": _FeatureFamilyEntry(
        config_type=BlockOpenLaggedFeatureFamilyConfig,
        family=BLOCK_OPEN_LAGGED_FAMILY,
    ),
    "timestamp_features": _FeatureFamilyEntry(
        config_type=TimestampFeaturesFeatureFamilyConfig,
        family=TIMESTAMP_FEATURES_FAMILY,
    ),
}


def feature_family(family_id: str) -> FeatureFamily:
    return lookup_local_spec(_FEATURE_FAMILIES, family_id, "feature_set.family.id").family


def coerce_feature_family_config(
    raw_config: Mapping[str, object] | FeatureFamilyConfig,
) -> FeatureFamilyConfig:
    if isinstance(raw_config, FeatureFamilyConfig):
        family_id = raw_config.id
        payload = raw_config.model_dump(mode="json")
    elif isinstance(raw_config, Mapping):
        payload = dict(raw_config)
        family_id = require_mapping_id(payload, "feature_set.family.id")
    else:
        raise ConfigResolutionError("feature_set.family must be a mapping")
    entry = lookup_local_spec(_FEATURE_FAMILIES, family_id, "feature_set.family.id")
    return entry.config_type.model_validate(payload)


def validate_feature_selection(
    feature_set_id: str,
    feature_family_id: str,
    feature_names: tuple[str, ...],
) -> None:
    family = feature_family(feature_family_id)
    validate_feature_names(
        feature_set_id,
        feature_names,
        known_feature_names=tuple(family.features),
    )
