# pyright: strict

"""Benchmark matrix planning."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from pydantic import ValidationError

from ..config.models import WorkflowTask
from ..config.registry import load_named_group
from ..config.resolution import WorkflowConfig, resolve_workflow_config
from ..core.errors import ConfigResolutionError
from .planning import BenchmarkWorkflowSelection, plan_benchmark_workflow_selections
from .schema import BenchmarkSpec


@dataclass(frozen=True, slots=True)
class BenchmarkPlanEntry:
    run_id: str
    case_id: str
    step_id: str
    workflow: WorkflowTask
    depends_on: tuple[str, ...]
    external_dependencies: tuple[str, ...]
    selection: Mapping[str, object]
    config: WorkflowConfig

    def to_json_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "case_id": self.case_id,
            "step_id": self.step_id,
            "workflow": self.workflow.value,
            "depends_on": list(self.depends_on),
            "external_dependencies": list(self.external_dependencies),
            "selection": dict(self.selection),
            "config": self.config.model_dump(mode="json", exclude_none=True),
        }


def plan_benchmark(name: str) -> list[BenchmarkPlanEntry]:
    spec = _load_benchmark_spec(name)
    entries: list[BenchmarkPlanEntry] = []
    errors: list[str] = []
    for case_index, case in enumerate(spec.cases):
        try:
            selections = plan_benchmark_workflow_selections(BenchmarkSpec(cases=[case]))
            entries.extend(_compile_benchmark_selection(selection) for selection in selections)
        except ConfigResolutionError as exc:
            errors.append(
                _format_benchmark_error(
                    name,
                    case_index=case_index,
                    error=exc,
                )
            )
    if errors:
        raise ConfigResolutionError("\n".join(errors))
    return entries


def _load_benchmark_spec(name: str) -> BenchmarkSpec:
    try:
        return BenchmarkSpec.model_validate(load_named_group(name, "benchmark"))
    except ValidationError as exc:
        raise ConfigResolutionError(str(exc)) from exc


def _compile_benchmark_selection(selection: BenchmarkWorkflowSelection) -> BenchmarkPlanEntry:
    try:
        config = resolve_workflow_config(selection.workflow, selection.selection)
    except (ConfigResolutionError, ValidationError, ValueError, TypeError) as exc:
        raise ConfigResolutionError(
            f"case {selection.case_id} step {selection.step_id}: {exc}"
        ) from exc
    return BenchmarkPlanEntry(
        run_id=selection.run_id,
        case_id=selection.case_id,
        step_id=selection.step_id,
        workflow=selection.workflow,
        depends_on=selection.depends_on,
        external_dependencies=selection.external_dependencies,
        selection=selection.selection_payload,
        config=config,
    )


def _format_benchmark_error(
    benchmark: str,
    *,
    case_index: int,
    error: ConfigResolutionError,
) -> str:
    return f"benchmark {benchmark} case {case_index}: {error.message}"


from .collection import collect_benchmark_run  # noqa: E402
from .runs import (  # noqa: E402
    BenchmarkCollectionRecord,
    BenchmarkRunMetadata,
    BenchmarkSubmissionRecord,
    LoadedBenchmarkPlanEntry,
    append_submission_jsonl,
    create_benchmark_run_dir,
    latest_benchmark_run_dir,
    load_plan_jsonl,
    load_submission_jsonl,
    write_plan_jsonl,
)
from .submission import (  # noqa: E402
    SubmittedBenchmarkWorkflow,
    compose_dependency,
    submit_benchmark_plan,
    submit_benchmark_run,
)

__all__ = [
    "BenchmarkCollectionRecord",
    "BenchmarkPlanEntry",
    "BenchmarkRunMetadata",
    "BenchmarkSubmissionRecord",
    "BenchmarkWorkflowSelection",
    "LoadedBenchmarkPlanEntry",
    "SubmittedBenchmarkWorkflow",
    "append_submission_jsonl",
    "collect_benchmark_run",
    "compose_dependency",
    "create_benchmark_run_dir",
    "latest_benchmark_run_dir",
    "load_plan_jsonl",
    "load_submission_jsonl",
    "plan_benchmark",
    "plan_benchmark_workflow_selections",
    "submit_benchmark_plan",
    "submit_benchmark_run",
    "write_plan_jsonl",
]
