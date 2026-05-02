# pyright: strict

"""Benchmark Plan Materialization."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from itertools import product
from typing import cast

from pydantic import ValidationError

from ..config.models import (
    ArtifactVariant,
    EvaluateConfig,
    ProblemSpec,
    TrainConfig,
    TuneConfig,
    WorkflowTask,
    coerce_problem_spec,
)
from ..config.registry import load_named_group_payload, load_problem_spec
from ..config.resolution import resolve_workflow_config
from ..config.selections import (
    EvaluateWorkflowSelection,
    TrainWorkflowSelection,
    WorkflowSelection,
    workflow_selection_from_values,
)
from ..config.workflow_snapshots import ResolvedWorkflowConfig
from ..core.errors import ConfigResolutionError, SelectorResolutionError
from ..storage.catalog.index import resolve_study_record
from ..storage.selectors import StudySelector
from ..storage.workflow_roots import produced_artifact_id, produced_study_id
from .models import BenchmarkPlanEntry
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
class _PlanSeed:
    case_id: str
    step_id: str
    workflow: WorkflowTask
    dimension_labels: Mapping[str, str]
    depends_on_steps: tuple[str, ...]
    external_dependencies: tuple[str, ...]
    artifact_from_step: str | None
    row: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class _DimensionVariant:
    dimension: str
    label: str
    patch: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class _MaterializedArtifactRoot:
    artifact_id: str
    dataset_id: str


def _config_state() -> dict[str, ResolvedWorkflowConfig]:
    return {}


def _study_dataset_state() -> dict[str, str]:
    return {}


def _artifact_root_state() -> dict[str, _MaterializedArtifactRoot]:
    return {}


@dataclass(slots=True)
class _MaterializedPlanState:
    configs_by_run_id: dict[str, ResolvedWorkflowConfig] = dataclass_field(
        default_factory=_config_state
    )
    study_dataset_by_study_id: dict[str, str] = dataclass_field(
        default_factory=_study_dataset_state
    )
    artifact_roots_by_run_id: dict[str, _MaterializedArtifactRoot] = dataclass_field(
        default_factory=_artifact_root_state
    )


def plan_benchmark(name: str) -> list[BenchmarkPlanEntry]:
    spec = _load_benchmark_spec(name)
    entries: list[BenchmarkPlanEntry] = []
    errors: list[str] = []
    for case_index, case in enumerate(spec.cases):
        try:
            entries.extend(_materialize_benchmark_case(case))
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


def materialize_benchmark_plan(spec: BenchmarkSpec) -> list[BenchmarkPlanEntry]:
    entries: list[BenchmarkPlanEntry] = []
    for case in spec.cases:
        entries.extend(_materialize_benchmark_case(case))
    return entries


def _load_benchmark_spec(name: str) -> BenchmarkSpec:
    try:
        return BenchmarkSpec.model_validate(load_named_group_payload(name, "benchmark"))
    except ValidationError as exc:
        raise ConfigResolutionError(str(exc)) from exc


def _format_benchmark_error(
    benchmark: str,
    *,
    case_index: int,
    error: ConfigResolutionError,
) -> str:
    return f"benchmark {benchmark} case {case_index}: {error.message}"


def _materialize_benchmark_case(case: BenchmarkCase) -> list[BenchmarkPlanEntry]:
    _validate_step_graph(case.steps)
    seeds = _expand_case(case)
    run_ids = _run_ids(seeds)
    by_step = _seeds_by_step(seeds, run_ids)
    state = _MaterializedPlanState()
    entries: list[BenchmarkPlanEntry] = []
    for index, seed in enumerate(seeds):
        try:
            artifact_from_run_id = _resolve_artifact_from_run_id(seed, by_step)
            depends_on = _resolve_dependencies(
                seed,
                by_step,
                artifact_from_run_id=artifact_from_run_id,
            )
            workflow_selection = _selection_for_seed(seed)
            workflow_selection = _materialized_selection(
                seed,
                workflow_selection,
                depends_on=depends_on,
                artifact_from_run_id=artifact_from_run_id,
                state=state,
            )
            config = _resolve_benchmark_config(seed.workflow, workflow_selection)
            entry = BenchmarkPlanEntry(
                run_id=run_ids[index],
                case_id=seed.case_id,
                step_id=seed.step_id,
                workflow=seed.workflow,
                depends_on=depends_on,
                external_dependencies=seed.external_dependencies,
                dimension_labels=dict(seed.dimension_labels),
                selection=_materialized_selection_payload(seed, workflow_selection),
                artifact_from_run_id=artifact_from_run_id,
                config=config,
            )
            entries.append(entry)
            _record_materialized_config(entry.run_id, config, state)
        except ConfigResolutionError as exc:
            raise ConfigResolutionError(
                f"case {case.id} step {seed.step_id}: {exc.message}"
            ) from exc
        except (ValidationError, ValueError, TypeError) as exc:
            raise ConfigResolutionError(
                f"case {case.id} step {seed.step_id}: {exc}"
            ) from exc
    return entries


def _materialized_selection(
    seed: _PlanSeed,
    workflow_selection: WorkflowSelection,
    *,
    depends_on: Sequence[str],
    artifact_from_run_id: str | None,
    state: _MaterializedPlanState,
) -> WorkflowSelection:
    if (
        seed.workflow is WorkflowTask.TRAIN
        and isinstance(workflow_selection, TrainWorkflowSelection)
        and workflow_selection.variant == ArtifactVariant.TUNED.value
        and workflow_selection.study_id is None
    ):
        study_id = _dependency_study_id(depends_on, state)
        return workflow_selection.model_copy(update={"study_id": study_id, "dataset_id": None})
    if (
        seed.workflow is WorkflowTask.EVALUATE
        and isinstance(workflow_selection, EvaluateWorkflowSelection)
        and artifact_from_run_id is not None
    ):
        materialized = _dependency_artifact_root(artifact_from_run_id, state)
        updates: dict[str, object] = {"artifact_id": materialized.artifact_id}
        if workflow_selection.dataset_id is None:
            updates["dataset_id"] = materialized.dataset_id
        return workflow_selection.model_copy(update=updates)
    return workflow_selection


def _materialized_selection_payload(
    seed: _PlanSeed,
    workflow_selection: WorkflowSelection,
) -> dict[str, object]:
    payload = _selection_ledger_payload(seed.row)
    if isinstance(workflow_selection, TrainWorkflowSelection):
        if workflow_selection.study_id is not None:
            payload["study_id"] = workflow_selection.study_id
    if isinstance(workflow_selection, EvaluateWorkflowSelection):
        if workflow_selection.artifact_id is not None:
            payload["artifact_id"] = workflow_selection.artifact_id
        if workflow_selection.dataset_id is not None:
            payload["dataset_id"] = workflow_selection.dataset_id
    return payload


def _resolve_benchmark_config(
    workflow: WorkflowTask,
    selection: WorkflowSelection,
) -> ResolvedWorkflowConfig:
    config = resolve_workflow_config(workflow, selection)
    if isinstance(config, (TrainConfig, TuneConfig, EvaluateConfig)):
        return config
    raise ConfigResolutionError("benchmark plans support train, tune, and evaluate workflows")


def _record_materialized_config(
    run_id: str,
    config: ResolvedWorkflowConfig,
    state: _MaterializedPlanState,
) -> None:
    state.configs_by_run_id[run_id] = config
    if isinstance(config, TuneConfig):
        state.study_dataset_by_study_id[produced_study_id(config)] = config.dataset_id


def _dependency_study_id(
    depends_on: Sequence[str],
    state: _MaterializedPlanState,
) -> str:
    for run_id in depends_on:
        config = state.configs_by_run_id[run_id]
        if isinstance(config, TuneConfig):
            return produced_study_id(config)
    raise ConfigResolutionError("tuned train requires a tune dependency or explicit study_id")


def _dependency_artifact_root(
    artifact_from_run_id: str,
    state: _MaterializedPlanState,
) -> _MaterializedArtifactRoot:
    cached = state.artifact_roots_by_run_id.get(artifact_from_run_id)
    if cached is not None:
        return cached
    source = state.configs_by_run_id[artifact_from_run_id]
    if not isinstance(source, TrainConfig):
        raise ConfigResolutionError("artifact_from may reference train steps only")
    dataset_id = _train_dataset_id(source, state)
    root = _MaterializedArtifactRoot(
        artifact_id=produced_artifact_id(source, dataset_id=dataset_id),
        dataset_id=dataset_id,
    )
    state.artifact_roots_by_run_id[artifact_from_run_id] = root
    return root


def _train_dataset_id(
    config: TrainConfig,
    state: _MaterializedPlanState,
) -> str:
    if config.dataset_id is not None:
        return config.dataset_id
    if config.study_id is None:
        raise ConfigResolutionError("train artifact source did not declare dataset_id or study_id")
    cached = state.study_dataset_by_study_id.get(config.study_id)
    if cached is not None:
        return cached
    try:
        study = resolve_study_record(
            config.storage.root,
            selector=StudySelector(study_id=config.study_id),
        )
    except SelectorResolutionError as exc:
        raise ConfigResolutionError(str(exc)) from exc
    state.study_dataset_by_study_id[config.study_id] = study.dataset_id
    return study.dataset_id


def _expand_case(case: BenchmarkCase) -> list[_PlanSeed]:
    global_combos = _dimension_combinations(_expand_dimensions(case.dimensions))
    seeds: list[_PlanSeed] = []
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
                seeds.append(
                    _PlanSeed(
                        case_id=case.id,
                        step_id=step.id,
                        workflow=step.workflow,
                        dimension_labels=step_labels,
                        depends_on_steps=_local_after_steps(step.after),
                        external_dependencies=_external_after_dependencies(step.after),
                        artifact_from_step=step.artifact_from,
                        row=row,
                    )
                )
    return seeds


def _selection_for_seed(seed: _PlanSeed) -> WorkflowSelection:
    try:
        selection = workflow_selection_from_values(seed.workflow, seed.row)
        if (
            seed.workflow is not WorkflowTask.EVALUATE
            and getattr(selection, "surface", None) is None
        ):
            raise ConfigResolutionError("surface is required")
        return selection
    except (ConfigResolutionError, ValidationError, ValueError, TypeError) as exc:
        raise ConfigResolutionError(str(exc)) from exc


def _selection_ledger_payload(row: Mapping[str, object]) -> dict[str, object]:
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
    return [
        [
            _DimensionVariant(
                dimension=name,
                label=_label_for_patch(entry.set),
                patch=entry.set,
            )
            for entry in entries
        ]
        for name, entries in dimensions.items()
    ]


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
    base_problem = load_problem_spec(grid.base)
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


def _run_ids(seeds: Sequence[_PlanSeed]) -> list[str]:
    run_ids: list[str] = []
    seen: set[str] = set()
    for seed in seeds:
        parts = [seed.case_id]
        parts.extend(f"{name}-{label}" for name, label in seed.dimension_labels.items())
        parts.append(seed.step_id)
        run_id = ".".join(parts)
        if run_id in seen:
            raise ConfigResolutionError(f"duplicate benchmark run_id: {run_id}")
        seen.add(run_id)
        run_ids.append(run_id)
    return run_ids


def _seeds_by_step(
    seeds: Sequence[_PlanSeed],
    run_ids: Sequence[str],
) -> Mapping[str, list[tuple[_PlanSeed, str]]]:
    by_step: dict[str, list[tuple[_PlanSeed, str]]] = defaultdict(list)
    for seed, run_id in zip(seeds, run_ids, strict=True):
        by_step[seed.step_id].append((seed, run_id))
    return by_step


def _resolve_dependencies(
    seed: _PlanSeed,
    by_step: Mapping[str, list[tuple[_PlanSeed, str]]],
    *,
    artifact_from_run_id: str | None,
) -> tuple[str, ...]:
    run_ids: list[str] = []
    for step_id in seed.depends_on_steps:
        candidates = [
            run_id
            for candidate, run_id in by_step[step_id]
            if _labels_match(candidate.dimension_labels, seed.dimension_labels)
        ]
        if not candidates:
            raise ConfigResolutionError(f"dependency {step_id} has no matching plan row")
        if len(candidates) > 1:
            raise ConfigResolutionError(f"dependency {step_id} is ambiguous")
        run_ids.append(candidates[0])
    if artifact_from_run_id is not None and artifact_from_run_id not in run_ids:
        run_ids.append(artifact_from_run_id)
    return tuple(run_ids)


def _resolve_artifact_from_run_id(
    seed: _PlanSeed,
    by_step: Mapping[str, list[tuple[_PlanSeed, str]]],
) -> str | None:
    step_id = seed.artifact_from_step
    if step_id is None:
        return None
    candidates = [
        (candidate, run_id)
        for candidate, run_id in by_step[step_id]
        if _labels_match(candidate.dimension_labels, seed.dimension_labels)
    ]
    if not candidates:
        raise ConfigResolutionError(f"artifact_from {step_id} has no matching plan row")
    if len(candidates) > 1:
        raise ConfigResolutionError(f"artifact_from {step_id} is ambiguous")
    candidate, run_id = candidates[0]
    if candidate.workflow is not WorkflowTask.TRAIN:
        raise ConfigResolutionError("artifact_from may reference train steps only")
    return run_id


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
        for dependency in _local_dependency_steps(step):
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


def _local_dependency_steps(step: BenchmarkStep) -> tuple[str, ...]:
    dependencies = list(_local_after_steps(step.after))
    if step.artifact_from is not None and step.artifact_from not in dependencies:
        dependencies.append(step.artifact_from)
    return tuple(dependencies)


def _label_for_patch(patch: Mapping[str, object]) -> str:
    return "__".join(f"{key}-{_label_value(value)}" for key, value in patch.items())


def _label_value(value: object) -> str:
    return str(value).replace(".", "_")


def _problem_grid_id(base: str, updates: Mapping[str, int]) -> str:
    suffix = "__".join(f"{field}-{value}" for field, value in updates.items())
    return f"{base}__{suffix}"
