# pyright: strict

"""Raw config group loading and file-edit helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import cast

import yaml
from pydantic import BaseModel

from ..core.errors import ConfigResolutionError
from .group_catalog import (
    group_spec,
    validate_named_group_payload,
)
from .group_catalog import (
    named_group_keys as catalog_named_group_keys,
)
from .group_catalog import (
    normalize_group_name as catalog_normalize_group_name,
)
from .group_catalog import (
    normalize_public_group_name as catalog_normalize_public_group_name,
)
from .group_catalog import (
    public_group_tokens as catalog_public_group_tokens,
)

_PACKAGE_CONF_ROOT = Path(__file__).resolve().parents[1] / "conf"
_CONF_ROOT = _PACKAGE_CONF_ROOT


def config_root() -> Path:
    return _CONF_ROOT


def named_group_keys() -> tuple[str, ...]:
    return catalog_named_group_keys()


def public_group_tokens() -> tuple[str, ...]:
    return catalog_public_group_tokens()


def public_group_help() -> str:
    return "One of: " + ", ".join(public_group_tokens()) + "."


def normalize_group_name(group: str) -> str:
    return catalog_normalize_group_name(group)


def normalize_public_group_name(group: str) -> str:
    return catalog_normalize_public_group_name(group)


def group_path(group: str) -> Path:
    return config_root() / normalize_group_name(group)


def spec_path(group: str, name: str) -> Path:
    return group_path(group) / f"{name}.yaml"


def load_yaml_mapping(path: Path) -> dict[str, object]:
    try:
        payload: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigResolutionError(f"Invalid YAML: {path}") from exc
    if payload is None:
        return {}
    if not isinstance(payload, Mapping):
        raise ConfigResolutionError(f"Configuration must be a mapping: {path}")
    return _mapping_payload(cast(Mapping[object, object], payload))


def _load_named_group_validated(name: str, group: str) -> BaseModel | dict[str, object]:
    normalized_group = normalize_group_name(group)
    path = spec_path(normalized_group, name)
    if not path.is_file():
        raise ConfigResolutionError(f"Unknown {normalized_group} spec: {name}")
    payload = load_yaml_mapping(path)
    return _validate_payload(normalized_group, name=name, payload=payload)


def load_named_group_payload(name: str, group: str) -> dict[str, object]:
    validated = _load_named_group_validated(name, group)
    if isinstance(validated, BaseModel):
        return _canonicalize_model(validated)
    return _canonicalize_mapping(validated)


def list_group_names(group: str) -> list[str]:
    return sorted(path.stem for path in group_path(group).glob("*.yaml"))


def show_named_group(group: str, name: str) -> str:
    return dump_canonical_yaml(load_named_group_payload(name, group))


def ensure_named_group_file(group: str, name: str) -> Path:
    normalized_group = normalize_group_name(group)
    path = spec_path(normalized_group, name)
    if path.is_file():
        return path
    payload = _seed_payload(normalized_group, name=name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_canonical_yaml(payload), encoding="utf-8")
    return path


def dump_canonical_yaml(value: BaseModel | dict[str, object]) -> str:
    payload = _canonicalize_value(value)
    if not isinstance(payload, dict):
        raise ConfigResolutionError("Canonical YAML root must be a mapping")
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)


def _seed_payload(group: str, *, name: str) -> dict[str, object]:
    spec = group_spec(group)
    template = _seed_template(group, name=name)
    identity_field = spec.identity_field
    if identity_field is not None:
        template[identity_field] = name
    validated = _validate_payload(group, name=name, payload=template)
    if isinstance(validated, BaseModel):
        return _canonicalize_model(validated)
    return _canonicalize_mapping(validated)


def _seed_template(group: str, *, name: str) -> dict[str, object]:
    spec = group_spec(group)
    package_group_root = _PACKAGE_CONF_ROOT / spec.directory
    candidates: list[Path] = []
    if spec.seed_from_requested_name:
        candidates.append(package_group_root / f"{name}.yaml")
    if spec.seed_name is not None:
        candidates.append(package_group_root / f"{spec.seed_name}.yaml")
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_file():
            return load_yaml_mapping(candidate)
    raise ConfigResolutionError(f"Missing seed template for config group: {group}")


def _validate_payload(
    group: str,
    *,
    name: str,
    payload: dict[str, object],
) -> BaseModel | dict[str, object]:
    return validate_named_group_payload(group, name=name, payload=payload)


def _canonicalize_model(model: BaseModel) -> dict[str, object]:
    payload: dict[str, object] = {}
    for field_name in type(model).model_fields:
        value = getattr(model, field_name)
        if value is None:
            continue
        payload[field_name] = _canonicalize_value(value)
    return payload


def _canonicalize_mapping(payload: dict[str, object]) -> dict[str, object]:
    return {
        str(key): _canonicalize_value(value)
        for key, value in payload.items()
        if value is not None
    }


def _canonicalize_value(value: object) -> object:
    if isinstance(value, BaseModel):
        return _canonicalize_model(value)
    if isinstance(value, Mapping):
        return _canonicalize_unknown_mapping(cast(Mapping[object, object], value))
    if isinstance(value, (list, tuple)):
        return [_canonicalize_value(item) for item in cast(Sequence[object], value)]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _mapping_payload(payload: Mapping[object, object]) -> dict[str, object]:
    return {str(key): value for key, value in payload.items()}


def _canonicalize_unknown_mapping(payload: Mapping[object, object]) -> dict[str, object]:
    return {
        str(key): _canonicalize_value(value)
        for key, value in sorted(payload.items(), key=lambda item: str(item[0]))
        if value is not None
    }
