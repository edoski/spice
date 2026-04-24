# pyright: strict

"""Benchmark case expansion."""

from __future__ import annotations

import shlex
from itertools import product
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..core.errors import ConfigResolutionError
from .models import WorkflowTask
from .registry import load_named_group
from .resolution import WorkflowRequest, resolve_workflow_config

_COMMAND_FIELD_ORDER = (
    "surface",
    "chain",
    "problem",
    "feature_set",
    "objective",
    "evaluation",
    "model",
    "tuning_space",
    "acquisition",
    "training",
    "split",
    "tuning",
    "study",
    "variant",
    "delay_seconds",
    "trial_count",
)
_REQUEST_FIELDS = frozenset(WorkflowRequest.model_fields)
_CASE_FIELDS = frozenset((*_COMMAND_FIELD_ORDER, "workflow"))


class BenchmarkSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cases: list[dict[str, Any]] = Field(min_length=1)


def expand_benchmark_commands(name: str) -> list[str]:
    """Expand one benchmark into validated shell commands."""

    rows = expand_benchmark_rows(name)
    return [_row_to_command(row) for row in rows]


def expand_benchmark_rows(name: str) -> list[dict[str, object]]:
    spec = _load_benchmark_spec(name)
    rows: list[dict[str, object]] = []
    errors: list[str] = []
    for case_index, case in enumerate(spec.cases):
        try:
            expanded_rows = _expand_case(case)
        except ConfigResolutionError as exc:
            errors.append(
                _format_benchmark_error(
                    name,
                    case_index=case_index,
                    expanded_row_index=0,
                    error=exc,
                )
            )
            continue
        for expanded_row_index, row in enumerate(expanded_rows):
            try:
                _validate_expanded_row(row)
            except ConfigResolutionError as exc:
                errors.append(
                    _format_benchmark_error(
                        name,
                        case_index=case_index,
                        expanded_row_index=expanded_row_index,
                        error=exc,
                    )
                )
                continue
            rows.append(row)
    if errors:
        raise ConfigResolutionError("\n".join(errors))
    return rows


def _load_benchmark_spec(name: str) -> BenchmarkSpec:
    try:
        return BenchmarkSpec.model_validate(load_named_group(name, "benchmark"))
    except ValidationError as exc:
        raise ConfigResolutionError(str(exc)) from exc


def _expand_case(case: dict[str, Any]) -> list[dict[str, object]]:
    unknown = sorted(set(case) - _CASE_FIELDS)
    if unknown:
        raise ConfigResolutionError("unknown benchmark case fields: " + ", ".join(unknown))
    workflow = case.get("workflow")
    if isinstance(workflow, list):
        raise ConfigResolutionError("benchmark case workflow must be scalar")
    if workflow is None:
        raise ConfigResolutionError("benchmark case workflow is required")

    scalar_items: dict[str, object] = {}
    axes: list[tuple[str, list[object]]] = []
    scalar_items["workflow"] = workflow
    for key in _COMMAND_FIELD_ORDER:
        if key not in case:
            continue
        value = case[key]
        if isinstance(value, list):
            if not value:
                raise ConfigResolutionError(f"benchmark case field {key} cannot be an empty list")
            axes.append((key, cast(list[object], value)))
        else:
            scalar_items[key] = value
    if not axes:
        return [dict(scalar_items)]

    rows: list[dict[str, object]] = []
    axis_names = [name for name, _values in axes]
    axis_values = [values for _name, values in axes]
    for values in product(*axis_values):
        row = dict(scalar_items)
        row.update(zip(axis_names, values, strict=True))
        rows.append(row)
    return rows


def _validate_expanded_row(row: dict[str, object]) -> None:
    workflow_value = row.get("workflow")
    if not isinstance(workflow_value, str):
        raise ConfigResolutionError("benchmark expanded row workflow must be a string")
    try:
        workflow = WorkflowTask(workflow_value)
    except ValueError as exc:
        raise ConfigResolutionError(f"unsupported benchmark workflow: {workflow_value}") from exc

    if workflow in {WorkflowTask.TRAIN, WorkflowTask.EVALUATE} and "variant" not in row:
        raise ConfigResolutionError(f"{workflow.value} benchmark rows must declare variant")
    if workflow is WorkflowTask.TUNE and "variant" in row:
        raise ConfigResolutionError("tune benchmark rows must not declare variant")

    request_payload = {key: value for key, value in row.items() if key in _REQUEST_FIELDS}
    try:
        request = WorkflowRequest.model_validate(request_payload)
        resolve_workflow_config(workflow, request)
    except (ConfigResolutionError, ValidationError, ValueError, TypeError) as exc:
        raise ConfigResolutionError(str(exc)) from exc


def _row_to_command(row: dict[str, object]) -> str:
    workflow = row["workflow"]
    if not isinstance(workflow, str):
        raise ConfigResolutionError("benchmark expanded row workflow must be a string")
    parts = ["spice", workflow]
    for field in _COMMAND_FIELD_ORDER:
        if field not in row:
            continue
        value = row[field]
        if value is None:
            continue
        parts.append("--" + field.replace("_", "-"))
        parts.append(shlex.quote(str(value)))
    return " ".join(parts)


def _format_benchmark_error(
    benchmark: str,
    *,
    case_index: int,
    expanded_row_index: int,
    error: ConfigResolutionError,
) -> str:
    return (
        f"benchmark {benchmark} case {case_index} expanded row {expanded_row_index}: "
        f"{error.message}"
    )
