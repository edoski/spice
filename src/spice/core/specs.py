"""Small helpers for local implementation spec tables."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeVar

from .errors import ConfigResolutionError

SpecIdT = TypeVar("SpecIdT")
SpecT = TypeVar("SpecT")
ConfigT = TypeVar("ConfigT")


def require_mapping_id(payload: Mapping[str, object], field_label: str) -> str:
    value = payload.get("id")
    if not isinstance(value, str):
        raise ConfigResolutionError(f"{field_label} is required")
    if not value:
        raise ConfigResolutionError(f"{field_label} must be a non-empty string")
    return value


def lookup_local_spec(
    specs: Mapping[SpecIdT, SpecT],
    spec_id: SpecIdT,
    field_label: str,
) -> SpecT:
    spec = specs.get(spec_id)
    if spec is not None:
        return spec
    known = ", ".join(sorted(str(key) for key in specs))
    raise ConfigResolutionError(
        f"Unknown {field_label}: {spec_id}. Known values: {known}"
    )


def require_spec_config(config: object, config_type: type[ConfigT], label: str) -> ConfigT:
    if isinstance(config, config_type):
        return config
    raise ConfigResolutionError(f"{label} must be {config_type.__name__}")
