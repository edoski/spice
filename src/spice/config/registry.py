# pyright: strict

"""Config registry helpers for query and direct file editing."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum, StrEnum
from pathlib import Path
from typing import cast

import yaml
from pydantic import BaseModel, ValidationError

from ..core.errors import ConfigResolutionError
from ..modeling.dataset_builders import coerce_dataset_builder_config
from ..modeling.families.registry import coerce_model_config
from .models import (
    ChainSpec,
    ConfigModel,
    DatasetSpec,
    ExecutionSpec,
    PresetSpec,
    ProviderSpec,
    coerce_feature_set_config,
    coerce_prediction_config,
    coerce_problem_spec,
)

_PACKAGE_CONF_ROOT = Path(__file__).resolve().parents[1] / "conf"
_CONF_ROOT = _PACKAGE_CONF_ROOT


class ConfigGroup(StrEnum):
    CHAIN = "chain"
    DATASET = "dataset"
    DATASET_BUILDER = "dataset-builder"
    EXECUTION = "execution"
    FEATURE_SET = "feature-set"
    MODEL = "model"
    PREDICTION = "prediction"
    PRESET = "preset"
    PROBLEM = "problem"
    PROVIDER = "provider"
    TUNING_SPACE = "tuning-space"


Validator = Callable[[dict[str, object]], BaseModel | dict[str, object]]


@dataclass(frozen=True, slots=True)
class ConfigGroupDefinition:
    token: str
    directory: str
    identity_field: str | None = None
    validator: Validator | None = None
    seed_template_name: str | None = None
    seed_from_requested_name: bool = False


def _identity_validator(model_type: type[ConfigModel]) -> Validator:
    def _validate(payload: dict[str, object]) -> BaseModel:
        return model_type.model_validate(payload)

    return _validate


_GROUP_DEFINITIONS = (
    ConfigGroupDefinition(
        token=ConfigGroup.CHAIN.value,
        directory="chain",
        identity_field="name",
        validator=_identity_validator(ChainSpec),
        seed_template_name="ethereum",
        seed_from_requested_name=True,
    ),
    ConfigGroupDefinition(
        token=ConfigGroup.DATASET.value,
        directory="dataset",
        identity_field="name",
        validator=_identity_validator(DatasetSpec),
        seed_template_name="icdcs_2026",
        seed_from_requested_name=True,
    ),
    ConfigGroupDefinition(
        token=ConfigGroup.DATASET_BUILDER.value,
        directory="dataset_builder",
        identity_field="id",
        validator=lambda payload: coerce_dataset_builder_config(payload),
        seed_template_name="standard_temporal",
        seed_from_requested_name=True,
    ),
    ConfigGroupDefinition(
        token=ConfigGroup.EXECUTION.value,
        directory="execution",
        identity_field="id",
        validator=_identity_validator(ExecutionSpec),
        seed_template_name="disi_l40",
        seed_from_requested_name=True,
    ),
    ConfigGroupDefinition(
        token=ConfigGroup.FEATURE_SET.value,
        directory="feature_set",
        identity_field="id",
        validator=lambda payload: coerce_feature_set_config(payload),
        seed_template_name="icdcs_2026",
        seed_from_requested_name=True,
    ),
    ConfigGroupDefinition(
        token=ConfigGroup.MODEL.value,
        directory="model",
        identity_field="id",
        validator=lambda payload: coerce_model_config(payload),
        seed_template_name="lstm",
        seed_from_requested_name=True,
    ),
    ConfigGroupDefinition(
        token=ConfigGroup.PREDICTION.value,
        directory="prediction",
        identity_field="id",
        validator=lambda payload: coerce_prediction_config(payload),
        seed_template_name="candidate_offset_selection",
        seed_from_requested_name=True,
    ),
    ConfigGroupDefinition(
        token=ConfigGroup.PRESET.value,
        directory="preset",
        validator=_identity_validator(PresetSpec),
        seed_template_name="icdcs_2026",
    ),
    ConfigGroupDefinition(
        token=ConfigGroup.PROBLEM.value,
        directory="problem",
        identity_field="id",
        validator=lambda payload: coerce_problem_spec(payload),
        seed_template_name="icdcs_2026",
        seed_from_requested_name=True,
    ),
    ConfigGroupDefinition(
        token=ConfigGroup.PROVIDER.value,
        directory="provider",
        identity_field="name",
        validator=_identity_validator(ProviderSpec),
        seed_template_name="publicnode",
        seed_from_requested_name=True,
    ),
    ConfigGroupDefinition(
        token=ConfigGroup.TUNING_SPACE.value,
        directory="tuning_space",
        validator=None,
        seed_template_name="lstm_default",
        seed_from_requested_name=True,
    ),
)
_GROUP_BY_TOKEN = {definition.token: definition for definition in _GROUP_DEFINITIONS}
_GROUP_BY_DIRECTORY = {definition.directory: definition for definition in _GROUP_DEFINITIONS}


def config_root() -> Path:
    return _CONF_ROOT


def named_group_keys() -> tuple[str, ...]:
    return tuple(
        definition.directory
        for definition in _GROUP_DEFINITIONS
        if definition.directory != ConfigGroup.PRESET.value
    )


def normalize_group_name(group: str) -> str:
    if group in _GROUP_BY_TOKEN:
        return _GROUP_BY_TOKEN[group].directory
    if group in _GROUP_BY_DIRECTORY:
        return group
    raise ConfigResolutionError(f"Unsupported config group: {group}")


def group_definition(group: str) -> ConfigGroupDefinition:
    normalized = normalize_group_name(group)
    if normalized in _GROUP_BY_DIRECTORY:
        return _GROUP_BY_DIRECTORY[normalized]
    raise ConfigResolutionError(f"Unsupported config group: {group}")


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


def load_named_group(name: str, group: str) -> dict[str, object]:
    path = spec_path(group, name)
    if not path.is_file():
        raise ConfigResolutionError(f"Unknown {normalize_group_name(group)} spec: {name}")
    return load_yaml_mapping(path)


def list_group_names(group: str) -> list[str]:
    directory = group_path(group)
    return sorted(path.stem for path in directory.glob("*.yaml"))


def show_named_group(group_token: str, name: str) -> str:
    definition = group_definition(group_token)
    payload = load_named_group(name, definition.directory)
    validated = _validate_payload(definition, name=name, payload=payload)
    return dump_canonical_yaml(validated)


def ensure_named_group_file(group_token: str, name: str) -> Path:
    definition = group_definition(group_token)
    path = spec_path(definition.directory, name)
    if path.is_file():
        return path
    payload = _seed_payload(definition, name=name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_canonical_yaml(payload), encoding="utf-8")
    return path


def dump_canonical_yaml(value: BaseModel | dict[str, object]) -> str:
    payload = _canonicalize_value(value)
    if not isinstance(payload, dict):
        raise ConfigResolutionError("Canonical YAML root must be a mapping")
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)


def _seed_payload(definition: ConfigGroupDefinition, *, name: str) -> dict[str, object]:
    template = _seed_template(definition, name=name)
    if definition.identity_field is not None:
        template[definition.identity_field] = name
    validated = _validate_payload(definition, name=name, payload=template)
    if isinstance(validated, BaseModel):
        return _canonicalize_model(validated)
    return _canonicalize_mapping(validated)


def _seed_template(definition: ConfigGroupDefinition, *, name: str) -> dict[str, object]:
    for candidate in _seed_candidate_paths(definition, name=name):
        if candidate.is_file():
            return load_yaml_mapping(candidate)
    raise ConfigResolutionError(f"Missing seed template for config group: {definition.directory}")


def _seed_candidate_paths(definition: ConfigGroupDefinition, *, name: str) -> tuple[Path, ...]:
    package_group_root = _PACKAGE_CONF_ROOT / definition.directory
    candidates: list[Path] = []
    if definition.seed_from_requested_name:
        candidates.append(package_group_root / f"{name}.yaml")
    if definition.seed_template_name is not None:
        candidates.append(package_group_root / f"{definition.seed_template_name}.yaml")
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return tuple(unique)


def _validate_payload(
    definition: ConfigGroupDefinition,
    *,
    name: str,
    payload: dict[str, object],
) -> BaseModel | dict[str, object]:
    if definition.validator is None:
        return _canonicalize_mapping(payload)
    try:
        validated = definition.validator(dict(payload))
    except ConfigResolutionError:
        raise
    except (ValidationError, ValueError, TypeError) as exc:
        raise ConfigResolutionError(str(exc)) from exc
    _validate_identity(definition, name=name, value=validated)
    return validated


def _validate_identity(
    definition: ConfigGroupDefinition,
    *,
    name: str,
    value: BaseModel | dict[str, object],
) -> None:
    if definition.identity_field is None:
        return
    if isinstance(value, BaseModel):
        identity_value = getattr(value, definition.identity_field)
    else:
        identity_value = value.get(definition.identity_field)
    if identity_value != name:
        raise ConfigResolutionError(
            f"{definition.token} {definition.identity_field} must match spec name: {name}"
        )


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
        str(key): _canonicalize_value(value) for key, value in payload.items() if value is not None
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
    items = sorted(payload.items(), key=lambda item: str(item[0]))
    return {
        str(key): _canonicalize_value(value)
        for key, value in items
        if value is not None
    }
