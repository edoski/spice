"""Corpus Assembly from acquisition output."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from ..acquisition import (
    AcquisitionPullController,
    BlockPullPlan,
    BlockSource,
)
from ..config.models import AcquireConfig
from ..storage.engine import RootKind
from ..storage.workflow_roots import AcquireWorkflowRoots
from .acquisition_stage import CorpusAcquisitionStage
from .metadata import (
    AcquireRunRecord,
    DatasetManifest,
)
from .planning import (
    CorpusAcquisitionSourceRequirements,
    CorpusCapabilityPlanningSpec,
    build_corpus_capability_planning_context,
)
from .split_materialization import CorpusSplitMaterializationSpec

StatusCallback = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class CorpusAssemblyRequest:
    config: AcquireConfig
    roots: AcquireWorkflowRoots


@dataclass(frozen=True, slots=True)
class CorpusAssemblyDryRunResult:
    mode: Literal["dry_run"]
    history_plan: BlockPullPlan
    evaluation_plan: BlockPullPlan
    requested_history_window_seconds: int


@dataclass(frozen=True, slots=True)
class CorpusAssemblyCommittedResult:
    mode: Literal["committed"]
    history_plan: BlockPullPlan
    evaluation_plan: BlockPullPlan
    requested_history_window_seconds: int
    resolved_capability_samples: int
    manifest: DatasetManifest
    acquire_run: AcquireRunRecord
    committed_root_kind: RootKind


CorpusAssemblyResult = CorpusAssemblyDryRunResult | CorpusAssemblyCommittedResult


def _noop_status(message: str) -> None:
    del message


def _planning_spec(config: AcquireConfig) -> CorpusCapabilityPlanningSpec:
    return CorpusCapabilityPlanningSpec(
        features=config.features,
        problem=config.problem,
        chain_runtime=config.chain.runtime,
        history_window_end_timestamp=config.history_window_end_timestamp,
        evaluation_window_start_timestamp=config.evaluation_window_start_timestamp,
        evaluation_window_end_timestamp=config.evaluation_window_end_timestamp,
    )


def _split_materialization_spec(
    config: AcquireConfig,
    *,
    required_columns: frozenset[str],
) -> CorpusSplitMaterializationSpec:
    return CorpusSplitMaterializationSpec(
        chain_name=config.chain.name,
        expected_chain_id=config.chain.runtime.chain_id,
        chunk_size=config.acquisition.chunk_size,
        required_columns=required_columns,
    )


def acquisition_source_requirements(
    config: AcquireConfig,
) -> CorpusAcquisitionSourceRequirements:
    return build_corpus_capability_planning_context(_planning_spec(config)).source_requirements


async def assemble_corpus(
    request: CorpusAssemblyRequest,
    block_source: BlockSource,
    *,
    status: StatusCallback | None = None,
) -> CorpusAssemblyResult:
    config = request.config
    roots = request.roots
    emit = status or _noop_status
    planning_context = build_corpus_capability_planning_context(_planning_spec(config))
    materialization = _split_materialization_spec(
        config,
        required_columns=planning_context.source_requirements.required_columns,
    )
    initial_plan = await planning_context.initial_plan(block_source)
    history_plan = initial_plan.history_plan
    evaluation_plan = initial_plan.evaluation_plan
    requested_history_window_seconds = initial_plan.requested_history_window_seconds

    if config.acquisition.dry_run:
        return CorpusAssemblyDryRunResult(
            mode="dry_run",
            history_plan=history_plan,
            evaluation_plan=evaluation_plan,
            requested_history_window_seconds=requested_history_window_seconds,
        )

    controller = AcquisitionPullController.from_config(config.acquisition)
    stage = CorpusAcquisitionStage.open(
        config=config,
        roots=roots,
        planning_context=planning_context,
        materialization=materialization,
        controller=controller,
    )
    fulfillment = await stage.fulfill(
        block_source=block_source,
        initial_history_plan=history_plan,
        evaluation_plan=evaluation_plan,
        requested_history_window_seconds=requested_history_window_seconds,
        status=emit,
    )
    publication = stage.publish(fulfillment=fulfillment)
    return CorpusAssemblyCommittedResult(
        mode="committed",
        history_plan=publication.history_plan,
        evaluation_plan=publication.evaluation_plan,
        requested_history_window_seconds=publication.requested_history_window_seconds,
        resolved_capability_samples=publication.resolved_capability_samples,
        manifest=publication.manifest,
        acquire_run=publication.acquire_run,
        committed_root_kind=publication.committed_root_kind,
    )
