"""Canonical surface frame and request overlays."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field

from ..core.errors import ConfigResolutionError
from ..modeling.families.base import ConfigModel
from .models import ArtifactConfig, StorageSpec, StudyConfig, WorkflowTask
from .registry import load_named_group


class SurfaceFrame(ConfigModel):
    chain: str
    dataset: str
    provider: str
    problem: str
    dataset_builder: str
    feature_set: str | None = None
    prediction: str
    objective: str | None = None
    evaluation: str | None = None
    model: str | None = None
    tuning_space: str | None = None
    acquisition: str
    training: str
    split: str
    delay_seconds: int | None = Field(default=None, gt=0)
    tuning: str
    storage: StorageSpec | None = None
    study: StudyConfig | None = None
    artifact: ArtifactConfig | None = None


def load_surface_frame(name: str) -> SurfaceFrame:
    return SurfaceFrame.model_validate(load_named_group(name, "surface"))


def apply_request_overrides(
    frame: SurfaceFrame,
    *,
    workflow: WorkflowTask,
    chain: str | None,
    problem: str | None,
    feature_set: str | None,
    objective: str | None,
    evaluation: str | None,
    model: str | None,
    tuning_space: str | None,
    acquisition: str | None,
    training: str | None,
    split: str | None,
    tuning: str | None,
    study: str | None,
    variant: str | None,
    delay_seconds: int | None,
    trial_count: int | None,
    storage_root: Path | None,
    dry_run: bool | None,
) -> SurfaceFrame:
    _reject_inapplicable_overrides(
        workflow=workflow,
        model=model,
        tuning_space=tuning_space,
        acquisition=acquisition,
        training=training,
        split=split,
        tuning=tuning,
        problem=problem,
        feature_set=feature_set,
        objective=objective,
        evaluation=evaluation,
        study=study,
        variant=variant,
        delay_seconds=delay_seconds,
        trial_count=trial_count,
        dry_run=dry_run,
    )
    updates: dict[str, object] = {}
    if chain is not None:
        updates["chain"] = chain
    if problem is not None:
        updates["problem"] = problem
    if feature_set is not None:
        updates["feature_set"] = feature_set
    if objective is not None:
        updates["objective"] = objective
    if evaluation is not None:
        updates["evaluation"] = evaluation
    if model is not None:
        updates["model"] = model
    if tuning_space is not None:
        updates["tuning_space"] = tuning_space
    if acquisition is not None:
        updates["acquisition"] = acquisition
    if training is not None:
        updates["training"] = training
    if split is not None:
        updates["split"] = split
    if tuning is not None:
        updates["tuning"] = tuning
    if storage_root is not None:
        base_storage = frame.storage or StorageSpec()
        updates["storage"] = _updated_model(base_storage, root=storage_root)
    if workflow is WorkflowTask.ACQUIRE:
        return frame.model_copy(update=updates)
    if study is not None:
        base_study = frame.study or StudyConfig()
        updates["study"] = _updated_model(base_study, name=study)
    if variant is not None:
        base_artifact = frame.artifact or ArtifactConfig()
        updates["artifact"] = _updated_model(base_artifact, variant=variant)
    if workflow is WorkflowTask.EVALUATE and delay_seconds is not None:
        updates["delay_seconds"] = delay_seconds
    return frame.model_copy(update=updates)


def _reject_inapplicable_overrides(
    *,
    workflow: WorkflowTask,
    model: str | None,
    tuning_space: str | None,
    acquisition: str | None,
    training: str | None,
    split: str | None,
    tuning: str | None,
    problem: str | None,
    feature_set: str | None,
    objective: str | None,
    evaluation: str | None,
    study: str | None,
    variant: str | None,
    delay_seconds: int | None,
    trial_count: int | None,
    dry_run: bool | None,
) -> None:
    invalid: list[str] = []
    if workflow is WorkflowTask.ACQUIRE:
        invalid.extend(
            label
            for label, value in (
                ("model", model),
                ("tuning_space", tuning_space),
                ("training", training),
                ("split", split),
                ("tuning", tuning),
                ("study", study),
                ("variant", variant),
                ("delay_seconds", delay_seconds),
                ("trial_count", trial_count),
                ("objective", objective),
                ("evaluation", evaluation),
            )
            if value is not None
        )
    elif workflow is WorkflowTask.TRAIN:
        if delay_seconds is not None:
            invalid.append("delay_seconds")
        if trial_count is not None:
            invalid.append("trial_count")
        if dry_run is not None:
            invalid.append("dry_run")
        if acquisition is not None:
            invalid.append("acquisition")
    elif workflow is WorkflowTask.TUNE:
        if variant is not None:
            invalid.append("variant")
        if delay_seconds is not None:
            invalid.append("delay_seconds")
        if dry_run is not None:
            invalid.append("dry_run")
        if acquisition is not None:
            invalid.append("acquisition")
    elif workflow is WorkflowTask.EVALUATE:
        if dry_run is not None:
            invalid.append("dry_run")
        if trial_count is not None:
            invalid.append("trial_count")
        if acquisition is not None:
            invalid.append("acquisition")
    if invalid:
        joined = ", ".join(invalid)
        raise ConfigResolutionError(
            f"{workflow.value} request does not accept override fields: {joined}"
        )


def _updated_model(model: ConfigModel, **updates: object) -> ConfigModel:
    return type(model).model_validate(
        {
            **model.model_dump(mode="json", exclude_none=True),
            **updates,
        }
    )
