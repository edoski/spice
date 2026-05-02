# pyright: strict

"""Benchmark plan data models."""

from __future__ import annotations

from dataclasses import dataclass

from ..config.models import WorkflowTask
from ..config.workflow_snapshots import ResolvedWorkflowConfig


@dataclass(frozen=True, slots=True)
class BenchmarkPlanEntry:
    run_id: str
    case_id: str
    step_id: str
    workflow: WorkflowTask
    depends_on: tuple[str, ...]
    external_dependencies: tuple[str, ...]
    dimension_labels: dict[str, str]
    selection: dict[str, object]
    artifact_from_run_id: str | None
    config: ResolvedWorkflowConfig
