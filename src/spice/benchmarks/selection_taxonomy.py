# pyright: strict

"""Benchmark selection taxonomy."""

from __future__ import annotations

from ..config.models import WorkflowTask
from ..config.resolved_workflows import SUPPORTED_RESOLVED_WORKFLOWS
from ..config.selections import workflow_selection_field_set

_BENCHMARK_WORKFLOWS = frozenset(SUPPORTED_RESOLVED_WORKFLOWS)
_BENCHMARK_DIMENSION_FIELDS = {
    "data": frozenset({"surface", "chain", "dataset_id"}),
    "features": frozenset({"features", "surface"}),
    "models": frozenset({"model", "tuning_space"}),
    "scoring": frozenset({"objective", "evaluation"}),
    "runtime": frozenset(
        {
            "dataset_id",
            "training",
            "split",
            "tuning",
            "study",
            "study_id",
            "artifact_id",
            "trial_count",
            "variant",
            "delay_seconds",
            "batch_size",
        }
    ),
}
_BENCHMARK_SELECTION_ROOT_FIELDS = frozenset({"dataset_id", "study_id", "artifact_id"})


def benchmark_workflows() -> frozenset[WorkflowTask]:
    return _BENCHMARK_WORKFLOWS


def benchmark_base_fields() -> frozenset[str]:
    return frozenset(
        field
        for workflow in _BENCHMARK_WORKFLOWS
        for field in workflow_selection_field_set(workflow)
    )


def benchmark_dimension_field_names() -> frozenset[str]:
    return frozenset(_BENCHMARK_DIMENSION_FIELDS)


def benchmark_dimension_fields(name: str) -> frozenset[str] | None:
    return _BENCHMARK_DIMENSION_FIELDS.get(name)


def benchmark_selection_root_fields() -> frozenset[str]:
    return _BENCHMARK_SELECTION_ROOT_FIELDS


def benchmark_selection_coordinate_fields() -> frozenset[str]:
    return benchmark_base_fields() - _BENCHMARK_SELECTION_ROOT_FIELDS
