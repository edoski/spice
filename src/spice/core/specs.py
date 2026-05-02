"""Small helpers for local implementation spec tables."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeVar, cast

from pydantic import BaseModel, ValidationError

from .errors import ConfigResolutionError

SpecIdT = TypeVar("SpecIdT")
SpecT = TypeVar("SpecT")
ConfigT = TypeVar("ConfigT")
ConfigModelT = TypeVar("ConfigModelT", bound=BaseModel)


def require_mapping_id(payload: Mapping[str, object], field_label: str) -> str:
    value = payload.get("id")
    if not isinstance(value, str):
        raise ConfigResolutionError(f"{field_label} is required")
    if not value:
        raise ConfigResolutionError(f"{field_label} must be a non-empty string")
    return value


def owner_payload(
    payload: object,
    *,
    owner: str,
    config_type: type[ConfigModelT],
) -> dict[str, object]:
    if isinstance(payload, config_type):
        return cast(dict[str, object], payload.model_dump(mode="json"))
    if isinstance(payload, BaseModel):
        raise ConfigResolutionError(
            f"{owner} must be a mapping or {config_type.__name__}"
        )
    if isinstance(payload, Mapping):
        return dict(payload)
    raise ConfigResolutionError(f"{owner} must be a mapping or {config_type.__name__}")


def owner_payload_id(
    payload: object,
    *,
    owner: str,
    config_type: type[ConfigModelT],
    id_label: str,
) -> tuple[dict[str, object], str]:
    raw_payload = owner_payload(payload, owner=owner, config_type=config_type)
    return raw_payload, require_mapping_id(raw_payload, id_label)


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


def validate_owner_config(
    payload: Mapping[str, object],
    config_type: type[ConfigModelT],
) -> ConfigModelT:
    try:
        return config_type.model_validate(payload)
    except (ValidationError, ValueError, TypeError) as exc:
        raise ConfigResolutionError(str(exc)) from exc
