"""Preset authoring models and overlay resolution."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import cast

from pydantic import Field, field_validator

from ..core.errors import ConfigResolutionError
from ..modeling.families.base import ConfigModel
from ._mapping import mapping_copy, require_mapping
from .models import (
    AcquisitionConfig,
    AcquisitionRpcConfig,
    ArtifactConfig,
    EarlyStoppingConfig,
    SplitConfig,
    StorageSpec,
    StudyConfig,
    TrainingConfig,
    TuningConfig,
    WorkflowTask,
)
from .registry import load_named_group, spec_path

PresetOverlayMapping = dict[str, object]
ValidateParentPreset = Callable[[str, dict[str, object]], None]

_PRESET_DEEP_MERGE_KEYS = frozenset(
    {
        "acquisition",
        "training",
        "split",
        "tuning",
        "storage",
        "study",
        "artifact",
    }
)


def _partial_overlay_mapping(
    value: object,
    *,
    label: str,
    model_type: type[ConfigModel],
) -> PresetOverlayMapping:
    if isinstance(value, ConfigModel):
        payload = value.model_dump(mode="json", exclude_none=True)
    elif isinstance(value, Mapping):
        payload = {str(key): child for key, child in value.items()}
    else:
        raise TypeError(f"{label} must be a mapping or config model")
    _validate_partial_overlay_mapping(
        payload,
        label=label,
        model_type=model_type,
    )
    return payload


def _validate_partial_overlay_mapping(
    payload: Mapping[str, object],
    *,
    label: str,
    model_type: type[ConfigModel],
) -> None:
    unknown = sorted(set(payload) - set(model_type.model_fields))
    if unknown:
        raise ConfigResolutionError(f"Unknown {label} preset fields: {', '.join(unknown)}")
    nested_models = _PRESET_OVERLAY_NESTED_MODELS.get(model_type, {})
    for key, value in payload.items():
        nested_model = nested_models.get(key)
        if nested_model is None:
            continue
        if not isinstance(value, Mapping) and not isinstance(value, ConfigModel):
            raise ConfigResolutionError(f"{label}.{key} must be provided as a mapping")
        _partial_overlay_mapping(value, label=f"{label}.{key}", model_type=nested_model)


_PRESET_OVERLAY_NESTED_MODELS: dict[type[ConfigModel], dict[str, type[ConfigModel]]] = {
    AcquisitionConfig: {"rpc": AcquisitionRpcConfig},
    TrainingConfig: {"early_stopping": EarlyStoppingConfig},
    SplitConfig: {},
    TuningConfig: {},
}


class PresetOverlay(ConfigModel):
    extends: str | None = None
    dataset: str | None = None
    problem: str | None = None
    delay_seconds: int | None = Field(default=None, gt=0)
    chain: str | None = None
    provider: str | None = None
    model: str | None = None
    dataset_builder: str | None = None
    feature_set: str | None = None
    prediction: str | None = None
    objective: str | dict[str, object] | None = None
    acquisition: PresetOverlayMapping | None = None
    training: PresetOverlayMapping | None = None
    split: PresetOverlayMapping | None = None
    evaluation: str | dict[str, object] | None = None
    tuning: PresetOverlayMapping | None = None
    tuning_space: str | dict[str, object] | None = None
    storage: StorageSpec | None = None
    study: StudyConfig | None = None
    artifact: ArtifactConfig | None = None

    @classmethod
    def _validate_merge_overlay(
        cls,
        value: object,
        *,
        label: str,
        model_type: type[ConfigModel],
    ) -> PresetOverlayMapping | None:
        if value is None:
            return None
        return _partial_overlay_mapping(
            value,
            label=label,
            model_type=model_type,
        )

    @field_validator("acquisition", mode="before")
    @classmethod
    def validate_acquisition_overlay(cls, value: object) -> PresetOverlayMapping | None:
        return cls._validate_merge_overlay(
            value,
            label="acquisition",
            model_type=AcquisitionConfig,
        )

    @field_validator("training", mode="before")
    @classmethod
    def validate_training_overlay(cls, value: object) -> PresetOverlayMapping | None:
        return cls._validate_merge_overlay(
            value,
            label="training",
            model_type=TrainingConfig,
        )

    @field_validator("split", mode="before")
    @classmethod
    def validate_split_overlay(cls, value: object) -> PresetOverlayMapping | None:
        return cls._validate_merge_overlay(
            value,
            label="split",
            model_type=SplitConfig,
        )

    @field_validator("tuning", mode="before")
    @classmethod
    def validate_tuning_overlay(cls, value: object) -> PresetOverlayMapping | None:
        return cls._validate_merge_overlay(
            value,
            label="tuning",
            model_type=TuningConfig,
        )


def known_top_level_config_keys() -> frozenset[str]:
    return frozenset(PresetOverlay.model_fields)


def load_named_preset_payload(
    name: str,
    *,
    validate_parent: ValidateParentPreset,
) -> dict[str, object]:
    return _resolve_preset_overlay_payload(name, stack=(), validate_parent=validate_parent)


def workflow_payload(
    *,
    workflow: WorkflowTask,
    preset: str | None,
    chain: str | None,
    study: str | None,
    variant: str | None,
    delay_seconds: int | None,
    trial_count: int | None,
    storage_root: Path | None,
    dry_run: bool | None,
    validate_parent: ValidateParentPreset,
) -> dict[str, object]:
    payload = (
        load_named_preset_payload(preset, validate_parent=validate_parent)
        if preset is not None
        else {}
    )
    apply_request_overlays(
        payload,
        workflow=workflow,
        chain=chain,
        study=study,
        variant=variant,
        delay_seconds=delay_seconds,
        trial_count=trial_count,
        storage_root=storage_root,
        dry_run=dry_run,
    )
    reject_unknown_top_level_keys(payload)
    return payload


def apply_request_overlays(
    payload: dict[str, object],
    *,
    workflow: WorkflowTask,
    chain: str | None,
    study: str | None,
    variant: str | None,
    delay_seconds: int | None,
    trial_count: int | None,
    storage_root: Path | None,
    dry_run: bool | None,
) -> None:
    if chain is not None:
        payload["chain"] = chain
    if storage_root is not None:
        payload["storage"] = overlay_mapping(
            payload.get("storage"),
            {"root": storage_root},
            label="storage",
        )
    if workflow is WorkflowTask.ACQUIRE:
        if dry_run is not None:
            payload["acquisition"] = overlay_mapping(
                payload.get("acquisition"),
                {"dry_run": dry_run},
                label="acquisition",
            )
        return
    if study is not None:
        payload["study"] = study
    if variant is not None:
        payload["artifact"] = overlay_mapping(
            payload.get("artifact"),
            {"variant": variant},
            label="artifact",
        )
    if workflow is WorkflowTask.TUNE and trial_count is not None:
        payload["tuning"] = overlay_mapping(
            payload.get("tuning"),
            {"trial_count": trial_count},
            label="tuning",
        )
    if workflow is WorkflowTask.EVALUATE and delay_seconds is not None:
        payload["delay_seconds"] = delay_seconds


def overlay_mapping(
    current: object,
    overlay: Mapping[str, object],
    *,
    label: str,
) -> dict[str, object]:
    if current is None:
        return dict(overlay)
    if not isinstance(current, Mapping):
        raise ConfigResolutionError(f"{label} must be provided as a mapping")
    return {
        **mapping_copy(cast(Mapping[object, object], current)),
        **overlay,
    }


def reject_unknown_top_level_keys(payload: Mapping[str, object]) -> None:
    unknown = sorted(set(payload) - known_top_level_config_keys())
    if unknown:
        raise ConfigResolutionError(f"Unknown top-level config fields: {', '.join(unknown)}")


def _load_direct_preset_overlay_payload(name: str) -> dict[str, object]:
    if not spec_path("preset", name).is_file():
        raise ConfigResolutionError(f"Unknown preset: {name}")
    return load_named_group(name, "preset")


def _resolve_preset_overlay_payload(
    name: str,
    *,
    stack: tuple[str, ...],
    validate_parent: ValidateParentPreset,
) -> dict[str, object]:
    if name in stack:
        cycle = " -> ".join((*stack, name))
        raise ConfigResolutionError(f"Preset extends cycle: {cycle}")
    raw_payload = _load_direct_preset_overlay_payload(name)
    parent_name = raw_payload.get("extends")
    if parent_name is None:
        return _preset_overlay_without_extends(raw_payload)
    if not isinstance(parent_name, str):
        raise ConfigResolutionError(f"preset {name} extends must be a preset name")
    parent_payload = _resolve_preset_overlay_payload(
        parent_name,
        stack=(*stack, name),
        validate_parent=validate_parent,
    )
    validate_parent(parent_name, parent_payload)
    child_payload = _preset_overlay_without_extends(raw_payload)
    return _merge_preset_overlay_payloads(parent_payload, child_payload)


def _preset_overlay_without_extends(payload: Mapping[str, object]) -> dict[str, object]:
    return {key: value for key, value in payload.items() if key != "extends"}


def _merge_preset_overlay_payloads(
    parent: Mapping[str, object],
    child: Mapping[str, object],
) -> dict[str, object]:
    merged = dict(parent)
    for key, value in child.items():
        if key in _PRESET_DEEP_MERGE_KEYS and key in merged:
            merged[key] = _deep_merge_known_block(merged[key], value, label=key)
            continue
        merged[key] = value
    return merged


def _deep_merge_known_block(parent: object, child: object, *, label: str) -> dict[str, object]:
    parent_payload = require_mapping(parent, label=label)
    child_payload = require_mapping(child, label=label)
    merged = dict(parent_payload)
    for key, value in child_payload.items():
        parent_value = merged.get(key)
        if isinstance(parent_value, Mapping) and isinstance(value, Mapping):
            merged[key] = _deep_merge_known_block(
                cast(Mapping[object, object], parent_value),
                cast(Mapping[object, object], value),
                label=f"{label}.{key}",
            )
            continue
        merged[key] = value
    return merged
