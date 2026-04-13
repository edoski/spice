"""Open registry for feature family specs."""

from __future__ import annotations

from collections.abc import Mapping

from .base import FeatureFamilyConfig, FeatureFamilySpec

_FEATURE_FAMILY_SPECS: dict[str, FeatureFamilySpec[FeatureFamilyConfig]] = {}
_BUILTINS_LOADED = False


def register_feature_family_spec(spec: FeatureFamilySpec[FeatureFamilyConfig]) -> None:
    existing = _FEATURE_FAMILY_SPECS.get(spec.id)
    if existing is not None:
        raise ValueError(f"Duplicate feature family spec id: {spec.id}")
    _FEATURE_FAMILY_SPECS[spec.id] = spec


def _ensure_builtin_feature_families_loaded() -> None:
    global _BUILTINS_LOADED
    if _BUILTINS_LOADED:
        return
    from . import block_native, time_native  # noqa: F401

    _BUILTINS_LOADED = True


def feature_family_spec(family_id: str) -> FeatureFamilySpec[FeatureFamilyConfig]:
    _ensure_builtin_feature_families_loaded()
    try:
        return _FEATURE_FAMILY_SPECS[family_id]
    except KeyError as exc:
        known = ", ".join(sorted(_FEATURE_FAMILY_SPECS)) or "<none>"
        raise ValueError(
            f"Unknown feature_set.family.id: {family_id}. Known families: {known}"
        ) from exc


def coerce_feature_family_config(
    raw_config: Mapping[str, object] | FeatureFamilyConfig,
) -> FeatureFamilyConfig:
    _ensure_builtin_feature_families_loaded()
    if isinstance(raw_config, FeatureFamilyConfig):
        family_id = raw_config.id
        payload = raw_config.model_dump(mode="json")
    elif isinstance(raw_config, Mapping):
        if "id" not in raw_config:
            raise ValueError("feature_set.family.id is required")
        family_id = str(raw_config["id"])
        payload = dict(raw_config)
    else:
        raise TypeError("feature_set.family must be a mapping")
    return feature_family_spec(family_id).config_type.model_validate(payload)
