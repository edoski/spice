# pyright: strict

"""Public benchmark planning models."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Literal, cast

from pydantic import Field, field_serializer, field_validator, model_validator

from ...config.models import ArtifactVariant, WorkflowTask
from ...config.resolved_workflows import ResolvedWorkflowConfig
from ...config.workflow_snapshots import (
    hydrate_workflow_config_snapshot,
    workflow_config_snapshot_payload,
)
from ...core.config_model import ConfigModel

BenchmarkRootRole = Literal["consumed", "produced", "source"]
BenchmarkRootKind = Literal["dataset", "study", "artifact"]


class BenchmarkDependencyLedger(ConfigModel):
    local_run_ids: tuple[str, ...]
    external_slurm_dependencies: tuple[str, ...]
    artifact_from_run_id: str | None

    @field_validator("local_run_ids", "external_slurm_dependencies", mode="before")
    @classmethod
    def coerce_json_arrays(cls, value: object) -> object:
        if isinstance(value, list):
            return tuple(cast("list[object]", value))
        return value


class BenchmarkSelectionLedger(ConfigModel):
    surface: str | None = None
    chain: str | None = None
    problem: str | None = None
    features: str | None = None
    model: str | None = None
    tuning_space: str | None = None
    objective: str | None = None
    evaluation: str | None = None
    training: str | None = None
    split: str | None = None
    tuning: str | None = None
    study: str | None = None
    variant: ArtifactVariant | None = None
    trial_count: int | None = Field(default=None, gt=0)
    delay_seconds: int | None = Field(default=None, gt=0)
    batch_size: int | None = Field(default=None, gt=0)
    storage_root: Path | None = None


class BenchmarkRootLedgerEntry(ConfigModel):
    run_id: str
    workflow: WorkflowTask
    role: BenchmarkRootRole
    root_kind: BenchmarkRootKind
    root_id: str
    source_run_id: str | None = None
    dataset_id: str | None = None
    study_id: str | None = None
    artifact_id: str | None = None


class BenchmarkRootLedger(ConfigModel):
    entries: tuple[BenchmarkRootLedgerEntry, ...] = ()

    @field_validator("entries", mode="before")
    @classmethod
    def coerce_json_arrays(cls, value: object) -> object:
        if isinstance(value, list):
            return tuple(cast("list[object]", value))
        return value


class BenchmarkRootFacts(ConfigModel):
    consumed_dataset_id: str | None = None
    consumed_study_id: str | None = None
    consumed_study_dataset_id: str | None = None
    consumed_artifact_id: str | None = None
    consumed_artifact_dataset_id: str | None = None
    produced_study_id: str | None = None
    produced_study_dataset_id: str | None = None
    produced_artifact_id: str | None = None
    produced_artifact_dataset_id: str | None = None
    artifact_source_dataset_id: str | None = None


class BenchmarkPlanEntry(ConfigModel):
    run_id: str
    case_id: str
    step_id: str
    workflow: WorkflowTask
    dependencies: BenchmarkDependencyLedger
    dimension_labels: dict[str, str]
    selection: BenchmarkSelectionLedger
    root_facts: BenchmarkRootFacts
    root_ledger: BenchmarkRootLedger
    config: ResolvedWorkflowConfig

    @model_validator(mode="before")
    @classmethod
    def hydrate_snapshot_config(cls, payload: object) -> object:
        if not isinstance(payload, Mapping):
            return payload
        raw = dict(cast("Mapping[str, object]", payload))
        config = raw.get("config")
        if not isinstance(config, Mapping):
            return raw
        workflow = raw.get("workflow")
        raw["config"] = hydrate_workflow_config_snapshot(
            workflow if isinstance(workflow, WorkflowTask) else WorkflowTask(str(workflow)),
            cast("Mapping[str, object]", config),
        )
        return raw

    @field_serializer("config")
    def serialize_config(self, config: ResolvedWorkflowConfig) -> dict[str, object]:
        return workflow_config_snapshot_payload(config)
