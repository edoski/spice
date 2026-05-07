# pyright: strict

"""Benchmark selection ledger models."""

from __future__ import annotations

from collections.abc import Mapping

from ...config.resolved_workflows import SUPPORTED_RESOLVED_WORKFLOWS
from ...config.selections import WorkflowSelection, workflow_selection_field_set
from ._models import BenchmarkSelectionLedger

_BENCHMARK_SELECTION_ROOT_FIELDS = frozenset({"dataset_id", "study_id", "artifact_id"})
_BENCHMARK_SELECTION_COORDINATE_FIELDS = (
    frozenset(
        field
        for workflow in SUPPORTED_RESOLVED_WORKFLOWS
        for field in workflow_selection_field_set(workflow)
    )
    - _BENCHMARK_SELECTION_ROOT_FIELDS
)


def materialize_selection_ledger(
    *,
    selection_row: Mapping[str, object],
    workflow_selection: WorkflowSelection,
) -> BenchmarkSelectionLedger:
    fields = _BENCHMARK_SELECTION_COORDINATE_FIELDS & set(BenchmarkSelectionLedger.model_fields)
    payload: dict[str, object] = {}
    for key, value in selection_row.items():
        if key in _BENCHMARK_SELECTION_ROOT_FIELDS or key not in fields:
            continue
        if value is not None:
            payload[key] = value
    for key in fields:
        if key in payload or not hasattr(workflow_selection, key):
            continue
        value = getattr(workflow_selection, key)
        if value is not None:
            payload[key] = value
    return BenchmarkSelectionLedger.model_validate(payload)
