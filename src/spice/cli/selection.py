"""CLI workflow-selection construction and dispatch planning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

from ..config.models import AcquireConfig, WorkflowTask
from ..config.resolution import WorkflowConfig, resolve_workflow_config
from ..config.selections import (
    AcquireWorkflowSelection,
    EvaluateWorkflowSelection,
    TrainWorkflowSelection,
    TuneWorkflowSelection,
    WorkflowSelection,
    workflow_selection_payload,
)
from ..core.errors import SpiceOperatorError

ModelWorkflowSelectionType: TypeAlias = type[TrainWorkflowSelection] | type[TuneWorkflowSelection]
ModelWorkflowSelection: TypeAlias = TrainWorkflowSelection | TuneWorkflowSelection


@dataclass(frozen=True, slots=True)
class WorkflowCommandPlan:
    task: WorkflowTask
    selection: WorkflowSelection
    config: WorkflowConfig
    submit: bool


def validate_submission_flags(
    *,
    submit: bool,
    dependency: str | None,
    detach: bool,
    storage_root: Path | None,
) -> None:
    if submit:
        if storage_root is not None:
            raise SpiceOperatorError("--storage-root cannot be combined with --submit")
        return
    if dependency is not None or detach:
        raise SpiceOperatorError("--dependency and --detach require --submit")


def resolve_selection_for_task(
    task: WorkflowTask,
    selection: WorkflowSelection,
) -> WorkflowConfig:
    return resolve_workflow_config(task, selection)


def build_acquire_workflow_config(
    *,
    surface: str | None,
    chain: str | None,
    problem: str | None,
    features: str | None,
    provider: str | None,
    storage_root: Path | None,
    dry_run: bool | None,
) -> AcquireConfig:
    config = resolve_selection_for_task(
        WorkflowTask.ACQUIRE,
        AcquireWorkflowSelection(
            surface=surface,
            chain=chain,
            problem=problem,
            features=features,
            provider=provider,
            storage_root=storage_root,
            dry_run=dry_run,
        ),
    )
    if not isinstance(config, AcquireConfig):
        raise TypeError("acquire selection resolved to non-acquire config")
    return config


def build_model_workflow_command_plan(
    *,
    task: WorkflowTask,
    selection_type: ModelWorkflowSelectionType,
    submit: bool,
    dependency: str | None,
    detach: bool,
    storage_root: Path | None,
    surface: str | None,
    chain: str | None,
    problem: str | None,
    features: str | None,
    objective: str | None,
    evaluation: str | None,
    model: str | None,
    tuning_space: str | None,
    training: str | None,
    split: str | None,
    tuning: str | None,
    study: str | None,
    dataset_id: str | None = None,
    study_id: str | None = None,
    variant: str | None = None,
    trial_count: int | None = None,
) -> WorkflowCommandPlan:
    validate_submission_flags(
        submit=submit,
        dependency=dependency,
        detach=detach,
        storage_root=storage_root,
    )
    selection = build_model_workflow_selection(
        task,
        selection_type=selection_type,
        storage_root=None if submit else storage_root,
        surface=surface,
        chain=chain,
        problem=problem,
        features=features,
        objective=objective,
        evaluation=evaluation,
        model=model,
        tuning_space=tuning_space,
        training=training,
        split=split,
        tuning=tuning,
        study=study,
        dataset_id=dataset_id,
        study_id=study_id,
        variant=variant,
        trial_count=trial_count,
    )
    return WorkflowCommandPlan(
        task=task,
        selection=selection,
        config=resolve_selection_for_task(task, selection),
        submit=submit,
    )


def build_model_workflow_selection(
    workflow: WorkflowTask,
    *,
    selection_type: ModelWorkflowSelectionType,
    storage_root: Path | None,
    surface: str | None,
    chain: str | None,
    problem: str | None,
    features: str | None,
    objective: str | None,
    evaluation: str | None,
    model: str | None,
    tuning_space: str | None,
    training: str | None,
    split: str | None,
    tuning: str | None,
    study: str | None,
    dataset_id: str | None = None,
    study_id: str | None = None,
    variant: str | None = None,
    trial_count: int | None = None,
) -> ModelWorkflowSelection:
    return selection_type.model_validate(
        workflow_selection_payload(
            workflow,
            {
                "surface": surface,
                "chain": chain,
                "problem": problem,
                "features": features,
                "objective": objective,
                "evaluation": evaluation,
                "model": model,
                "tuning_space": tuning_space,
                "training": training,
                "split": split,
                "tuning": tuning,
                "study": study,
                "dataset_id": dataset_id,
                "study_id": study_id,
                "variant": variant,
                "trial_count": trial_count,
                "storage_root": storage_root,
            },
        )
    )


def build_evaluate_workflow_command_plan(
    *,
    submit: bool,
    dependency: str | None,
    detach: bool,
    storage_root: Path | None,
    artifact_id: str | None,
    dataset_id: str | None,
    evaluation: str | None,
    delay_seconds: int | None,
    batch_size: int | None,
) -> WorkflowCommandPlan:
    validate_submission_flags(
        submit=submit,
        dependency=dependency,
        detach=detach,
        storage_root=storage_root,
    )
    selection = EvaluateWorkflowSelection(
        storage_root=None if submit else storage_root,
        artifact_id=artifact_id,
        dataset_id=dataset_id,
        evaluation=evaluation,
        delay_seconds=delay_seconds,
        batch_size=batch_size,
    )
    return WorkflowCommandPlan(
        task=WorkflowTask.EVALUATE,
        selection=selection,
        config=resolve_selection_for_task(WorkflowTask.EVALUATE, selection),
        submit=submit,
    )
