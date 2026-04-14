"""Open registry for feature family specs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ...core.components import ComponentCatalog
from ...core.errors import ConfigResolutionError
from .base import FeatureFamilyConfig, FeatureFamilySpec

_FEATURE_FAMILY_SPECS = ComponentCatalog[FeatureFamilySpec[Any]](
    kind_label="feature family",
    entry_point_group="spice.feature_families",
)


def register_feature_family_spec(spec: FeatureFamilySpec[Any]) -> None:
    _FEATURE_FAMILY_SPECS.register(spec.id, spec)


def _load_builtin_feature_families() -> None:
    from . import block_native, time_native  # noqa: F401


_FEATURE_FAMILY_SPECS.configure_builtin_loader(_load_builtin_feature_families)


def feature_family_spec(family_id: str) -> FeatureFamilySpec[Any]:
    try:
        return _FEATURE_FAMILY_SPECS.get(family_id)
    except ConfigResolutionError as exc:
        raise ConfigResolutionError(
            str(exc).replace("feature family", "feature_set.family.id")
        ) from exc


def coerce_feature_family_config(
    raw_config: Mapping[str, object] | FeatureFamilyConfig,
) -> FeatureFamilyConfig:
    if isinstance(raw_config, FeatureFamilyConfig):
        family_id = raw_config.id
        payload = raw_config.model_dump(mode="json")
    elif isinstance(raw_config, Mapping):
        if "id" not in raw_config:
            raise ConfigResolutionError("feature_set.family.id is required")
        family_id = str(raw_config["id"])
        payload = dict(raw_config)
    else:
        raise ConfigResolutionError("feature_set.family must be a mapping")
    return feature_family_spec(family_id).config_type.model_validate(payload)
