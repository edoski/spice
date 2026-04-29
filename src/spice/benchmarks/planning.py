# pyright: strict

"""Benchmark workflow-selection planning."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from typing import cast

from pydantic import ValidationError

from ..config.models import ProblemSpec, WorkflowTask, coerce_problem_spec
from ..config.registry import load_named_group
from ..config.selections import (
    WorkflowSelection,
    workflow_selection_fields,
    workflow_selection_type,
)
from ..core.errors import ConfigResolutionError
from .schema import (
    AfterDependency,
    BenchmarkCase,
    BenchmarkSpec,
    BenchmarkStep,
    ProblemDimensionEntry,
    SetDimensionEntry,
    SlurmAfterDependency,
)


@dataclass(frozen=True, slots=True)
class BenchmarkWorkflowSelection:
    run_id: str
    case_id: str
    step_id: str
    workflow: WorkflowTask
    depends_on: tuple[str, ...]
    external_dependencies: tuple[str, ...]
    dimension_labels: Mapping[str, str]
    selection: WorkflowSelection
    selection_payload: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class _DimensionVariant:
    dimension: str
    label: str
    patch: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class _ExpandedStep:
    case_id: str
    step_id: str
    workflow: WorkflowTask
    dimension_labels: Mapping[str, str]
    depends_on_steps: tuple[str, ...]
    external_dependencies: tuple[str, ...]
    row: Mapping[str, object]


def plan_benchmark_workflow_selections(
    spec: BenchmarkSpec,
) -> list[BenchmarkWorkflowSelection]:
    selections: list[BenchmarkWorkflowSelection] = []
    for case in spec.cases:
        selections.extend(_plan_case_workflow_selections(case))
    return selections


def _plan_case_workflow_selections(case: BenchmarkCase) -> list[BenchmarkWorkflowSelection]:
    _validate_step_graph(case.steps)
    expanded_steps = _expand_case(case)
    run_ids = _run_ids(expanded_steps)
    by_step = _entries_by_step(expanded_steps, run_ids)
    selections: list[BenchmarkWorkflowSelection] = []
    for index, expanded in enumerate(expanded_steps):
        try:
            depends_on = _resolve_dependencies(expanded, by_step)
            selection = _workflow_selection(expanded)
            selections.append(
                BenchmarkWorkflowSelection(
                    run_id=run_ids[index],
                    case_id=expanded.case_id,
                    step_id=expanded.step_id,
                    workflow=expanded.workflow,
                    depends_on=depends_on,
                    external_dependencies=expanded.external_dependencies,
                    dimension_labels=expanded.dimension_labels,
                    selection=selection,
                    selection_payload=_selection_payload(expanded.row),
                )
            )
        except ConfigResolutionError as exc:
            raise ConfigResolutionError(
                f"case {case.id} step {expanded.step_id}: {exc.message}"
            ) from exc
    return selections


def _expand_case(case: BenchmarkCase) -> list[_ExpandedStep]:
    global_combos = _dimension_combinations(_expand_dimensions(case.dimensions))
    rows: list[_ExpandedStep] = []
    for global_combo in global_combos:
        global_patch = _merge_patches([variant.patch for variant in global_combo])
        global_labels = {variant.dimension: variant.label for variant in global_combo}
        for step in case.steps:
            step_combos = _dimension_combinations(_expand_step_dimensions(step.dimensions))
            for step_combo in step_combos:
                step_patch = _merge_patches([variant.patch for variant in step_combo])
                step_labels = {
                    **global_labels,
                    **{variant.dimension: variant.label for variant in step_combo},
                }
                row = {
                    **case.base,
                    **global_patch,
                    **step.set,
                    **step_patch,
                }
                rows.append(
                    _ExpandedStep(
                        case_id=case.id,
                        step_id=step.id,
                        workflow=step.workflow,
                        dimension_labels=step_labels,
                        depends_on_steps=_local_after_steps(step.after),
                        external_dependencies=_external_after_dependencies(step.after),
                        row=row,
                    )
                )
    return rows


def _workflow_selection(expanded: _ExpandedStep) -> WorkflowSelection:
    workflow = expanded.workflow
    row = expanded.row
    workflow_fields = frozenset(workflow_selection_fields(workflow))
    unknown = sorted(set(row) - workflow_fields)
    if unknown:
        raise ConfigResolutionError(
            f"{workflow.value} benchmark step does not support fields: " + ", ".join(unknown)
        )
    try:
        selection = cast(
            WorkflowSelection,
            workflow_selection_type(workflow).model_validate(
                {key: value for key, value in row.items() if key in workflow_fields}
            ),
        )
        if selection.surface is None:
            raise ConfigResolutionError("surface is required")
        return selection
    except (ConfigResolutionError, ValidationError, ValueError, TypeError) as exc:
        raise ConfigResolutionError(str(exc)) from exc


def _selection_payload(row: Mapping[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, value in row.items():
        if isinstance(value, ProblemSpec):
            payload[key] = value.id
            continue
        payload[key] = value
    return payload


def _expand_dimensions(
    dimensions: Mapping[str, list[SetDimensionEntry] | list[ProblemDimensionEntry]],
) -> list[list[_DimensionVariant]]:
    expanded: list[list[_DimensionVariant]] = []
    for name, entries in dimensions.items():
        if name == "problems":
            variants: list[_DimensionVariant] = []
            for entry in cast(list[ProblemDimensionEntry], entries):
                variants.extend(_expand_problem_entry(entry))
            expanded.append(variants)
            continue
        expanded.append(
            [
                _DimensionVariant(
                    dimension=name,
                    label=_label_for_patch(entry.set),
                    patch=entry.set,
                )
                for entry in cast(list[SetDimensionEntry], entries)
            ]
        )
    return expanded


def _expand_step_dimensions(
    dimensions: Mapping[str, list[SetDimensionEntry]],
) -> list[list[_DimensionVariant]]:
    expanded: list[list[_DimensionVariant]] = []
    for name, entries in dimensions.items():
        expanded.append(
            [
                _DimensionVariant(
                    dimension=name,
                    label=_label_for_patch(entry.set),
                    patch=entry.set,
                )
                for entry in entries
            ]
        )
    return expanded


def _expand_problem_entry(entry: ProblemDimensionEntry) -> list[_DimensionVariant]:
    if entry.ref is not None:
        return [
            _DimensionVariant(
                dimension="problems",
                label=entry.ref,
                patch={"problem": entry.ref},
            )
        ]
    grid = entry.grid
    if grid is None:
        raise ConfigResolutionError("problem dimension entry is empty")
    base_problem = coerce_problem_spec(load_named_group(grid.base, "problem"))
    field_names = tuple(grid.fields)
    variants: list[_DimensionVariant] = []
    for values in product(*(grid.fields[field] for field in field_names)):
        updates = dict(zip(field_names, values, strict=True))
        problem_id = _problem_grid_id(grid.base, updates)
        problem = coerce_problem_spec(
            {
                **base_problem.model_dump(mode="json"),
                **updates,
                "id": problem_id,
            }
        )
        variants.append(
            _DimensionVariant(
                dimension="problems",
                label=problem_id,
                patch={"problem": problem},
            )
        )
    return variants


def _dimension_combinations(
    dimensions: Sequence[Sequence[_DimensionVariant]],
) -> list[tuple[_DimensionVariant, ...]]:
    if not dimensions:
        return [()]
    return list(product(*dimensions))


def _merge_patches(patches: Iterable[Mapping[str, object]]) -> dict[str, object]:
    merged: dict[str, object] = {}
    owners: dict[str, object] = {}
    for patch in patches:
        for key, value in patch.items():
            previous = owners.get(key)
            if previous is not None and merged[key] != value:
                raise ConfigResolutionError(f"field {key} is set by multiple dimensions")
            owners[key] = value
            merged[key] = value
    return merged


def _run_ids(entries: Sequence[_ExpandedStep]) -> list[str]:
    run_ids: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        parts = [entry.case_id]
        parts.extend(f"{name}-{label}" for name, label in entry.dimension_labels.items())
        parts.append(entry.step_id)
        run_id = ".".join(parts)
        if run_id in seen:
            raise ConfigResolutionError(f"duplicate benchmark run_id: {run_id}")
        seen.add(run_id)
        run_ids.append(run_id)
    return run_ids


def _entries_by_step(
    entries: Sequence[_ExpandedStep],
    run_ids: Sequence[str],
) -> Mapping[str, list[tuple[_ExpandedStep, str]]]:
    by_step: dict[str, list[tuple[_ExpandedStep, str]]] = defaultdict(list)
    for entry, run_id in zip(entries, run_ids, strict=True):
        by_step[entry.step_id].append((entry, run_id))
    return by_step


def _resolve_dependencies(
    entry: _ExpandedStep,
    by_step: Mapping[str, list[tuple[_ExpandedStep, str]]],
) -> tuple[str, ...]:
    run_ids: list[str] = []
    for step_id in entry.depends_on_steps:
        candidates = [
            run_id
            for candidate, run_id in by_step[step_id]
            if _labels_match(candidate.dimension_labels, entry.dimension_labels)
        ]
        if not candidates:
            raise ConfigResolutionError(f"dependency {step_id} has no matching expanded row")
        if len(candidates) > 1:
            raise ConfigResolutionError(f"dependency {step_id} is ambiguous")
        run_ids.append(candidates[0])
    return tuple(run_ids)


def _labels_match(upstream: Mapping[str, str], downstream: Mapping[str, str]) -> bool:
    return all(downstream.get(name) == label for name, label in upstream.items())


def _local_after_steps(after: Sequence[AfterDependency]) -> tuple[str, ...]:
    return tuple(value for value in after if isinstance(value, str))


def _external_after_dependencies(
    after: Sequence[AfterDependency],
) -> tuple[str, ...]:
    return tuple(value.slurm for value in after if isinstance(value, SlurmAfterDependency))


def _validate_step_graph(steps: Sequence[BenchmarkStep]) -> None:
    step_ids = [step.id for step in steps]
    if len(set(step_ids)) != len(step_ids):
        raise ConfigResolutionError("benchmark step ids must be unique")
    step_id_set = set(step_ids)
    positions = {step.id: index for index, step in enumerate(steps)}
    edges: dict[str, set[str]] = {step.id: set() for step in steps}
    for step in steps:
        for dependency in _local_after_steps(step.after):
            if dependency not in step_id_set:
                raise ConfigResolutionError(f"step {step.id} depends on unknown step {dependency}")
            if dependency == step.id:
                raise ConfigResolutionError(f"step {step.id} cannot depend on itself")
            if positions[dependency] > positions[step.id]:
                raise ConfigResolutionError(f"step {step.id} depends on future step {dependency}")
            edges[dependency].add(step.id)
    indegree = {step.id: 0 for step in steps}
    for dependents in edges.values():
        for dependent in dependents:
            indegree[dependent] += 1
    queue = deque(step_id for step_id, count in indegree.items() if count == 0)
    visited = 0
    while queue:
        step_id = queue.popleft()
        visited += 1
        for dependent in edges[step_id]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)
    if visited != len(steps):
        raise ConfigResolutionError("benchmark step dependencies contain a cycle")


def _label_for_patch(patch: Mapping[str, object]) -> str:
    return "__".join(f"{key}-{_label_value(value)}" for key, value in patch.items())


def _label_value(value: object) -> str:
    return str(value).replace(".", "_")


def _problem_grid_id(base: str, updates: Mapping[str, int]) -> str:
    suffix = "__".join(f"{field}-{value}" for field, value in updates.items())
    return f"{base}__{suffix}"
