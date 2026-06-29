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
from ..storage.workflow_roots import AcquireWorkflowRoots
from .acquisition_stage import CorpusAcquisitionPublication, CorpusAcquisitionStage
from .planning import (
    CorpusAcquisitionPlanningContext,
    CorpusAcquisitionPlanningSpec,
    CorpusAcquisitionSourceRequirements,
    build_corpus_acquisition_planning_context,
)
from .split_materialization import CorpusSplitMaterializationSpec

StatusCallback = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class CorpusAssemblyRequest:
    config: AcquireConfig
    roots: AcquireWorkflowRoots
    planning_context: CorpusAcquisitionPlanningContext
    materialization: CorpusSplitMaterializationSpec

    @property
    def source_requirements(self) -> CorpusAcquisitionSourceRequirements:
        return self.planning_context.source_requirements


@dataclass(frozen=True, slots=True)
class CorpusAssemblyDryRunResult:
    mode: Literal["dry_run"]
    blocks_plan: BlockPullPlan
    requested_window_seconds: int


CorpusAssemblyResult = CorpusAssemblyDryRunResult | CorpusAcquisitionPublication


def _noop_status(message: str) -> None:
    del message


def _planning_spec(config: AcquireConfig) -> CorpusAcquisitionPlanningSpec:
    return CorpusAcquisitionPlanningSpec(
        features=config.features,
        problem=config.problem,
        chain_runtime=config.chain.runtime,
        window_start_timestamp=config.corpus_window_start_timestamp,
        window_end_timestamp=config.corpus_window_end_timestamp,
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


def prepare_corpus_assembly_request(
    *,
    config: AcquireConfig,
    roots: AcquireWorkflowRoots,
) -> CorpusAssemblyRequest:
    planning_context = build_corpus_acquisition_planning_context(_planning_spec(config))
    return CorpusAssemblyRequest(
        config=config,
        roots=roots,
        planning_context=planning_context,
        materialization=_split_materialization_spec(
            config,
            required_columns=planning_context.source_requirements.required_columns,
        ),
    )


async def assemble_corpus(
    request: CorpusAssemblyRequest,
    block_source: BlockSource,
    *,
    status: StatusCallback | None = None,
) -> CorpusAssemblyResult:
    config = request.config
    roots = request.roots
    emit = status or _noop_status
    planning_context = request.planning_context
    initial_plan = await planning_context.initial_plan(block_source)
    blocks_plan = initial_plan.blocks_plan
    requested_window_seconds = initial_plan.requested_window_seconds

    if config.acquisition.dry_run:
        return CorpusAssemblyDryRunResult(
            mode="dry_run",
            blocks_plan=blocks_plan,
            requested_window_seconds=requested_window_seconds,
        )

    controller = AcquisitionPullController.from_config(config.acquisition)
    stage = CorpusAcquisitionStage.open(
        config=config,
        roots=roots,
        planning_context=planning_context,
        materialization=request.materialization,
        controller=controller,
    )
    fulfillment = await stage.fulfill(
        block_source=block_source,
        blocks_plan=blocks_plan,
        requested_window_seconds=requested_window_seconds,
        status=emit,
    )
    return stage.publish(fulfillment=fulfillment)
