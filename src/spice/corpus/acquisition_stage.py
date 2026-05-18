"""Corpus acquisition staging and commit."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ..acquisition import AcquisitionPullController, BlockPullPlan, BlockSource
from ..config.models import AcquireConfig
from ..core.files import remove_path, write_path_atomic
from ..storage.corpus import write_corpus_state
from ..storage.engine import RootKind
from ..storage.transactions import commit_corpus_acquisition
from ..storage.workflow_roots import AcquireWorkflowRoots
from .metadata import (
    AcquireRunRecord,
    CorpusManifest,
    build_acquire_run_record,
    build_dataset_manifest,
    provider_metadata,
)
from .planning import CorpusAcquisitionPlanningContext
from .split_materialization import (
    CorpusSplitIntent,
    CorpusSplitKind,
    CorpusSplitMaterializationResult,
    CorpusSplitMaterializationSession,
    CorpusSplitMaterializationSpec,
)

ACQUIRE_STAGE_DIR_NAME = ".acquire-staging"

StatusCallback = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class CorpusAcquisitionStageFulfillment:
    blocks_result: CorpusSplitMaterializationResult
    blocks_plan: BlockPullPlan
    requested_window_seconds: int


@dataclass(frozen=True, slots=True)
class CorpusAcquisitionPublication:
    mode: Literal["committed"]
    blocks_plan: BlockPullPlan
    requested_window_seconds: int
    manifest: CorpusManifest
    acquire_run: AcquireRunRecord
    committed_root_kind: RootKind


@dataclass(frozen=True, slots=True)
class CorpusAcquisitionStage:
    config: AcquireConfig
    roots: AcquireWorkflowRoots
    planning_context: CorpusAcquisitionPlanningContext
    materialization: CorpusSplitMaterializationSpec
    controller: AcquisitionPullController
    temp_root: Path

    @classmethod
    def open(
        cls,
        *,
        config: AcquireConfig,
        roots: AcquireWorkflowRoots,
        planning_context: CorpusAcquisitionPlanningContext,
        materialization: CorpusSplitMaterializationSpec,
        controller: AcquisitionPullController,
    ) -> CorpusAcquisitionStage:
        roots.corpus.root_path.parent.mkdir(parents=True, exist_ok=True)
        temp_root = acquire_stage_root(roots)
        temp_root.mkdir(parents=True, exist_ok=True)
        write_acquire_stage_record(
            temp_root / ".spice" / "acquire-stage.json",
            config=config,
            corpus_id=roots.corpus.corpus_id,
        )
        return cls(
            config=config,
            roots=roots,
            planning_context=planning_context,
            materialization=materialization,
            controller=controller,
            temp_root=temp_root,
        )

    async def fulfill(
        self,
        *,
        block_source: BlockSource,
        blocks_plan: BlockPullPlan,
        requested_window_seconds: int,
        status: StatusCallback,
    ) -> CorpusAcquisitionStageFulfillment:
        split_session = CorpusSplitMaterializationSession(
            materialization=self.materialization,
            block_source=block_source,
            controller=self.controller,
            status=status,
        )
        blocks_result = await split_session.fulfill(
            CorpusSplitIntent(
                kind=CorpusSplitKind.BLOCKS,
                output_dir=self.roots.corpus.blocks_dir,
                working_dir=self.temp_root,
                plan=blocks_plan,
            )
        )
        return CorpusAcquisitionStageFulfillment(
            blocks_result=blocks_result,
            blocks_plan=blocks_plan,
            requested_window_seconds=requested_window_seconds,
        )

    def publish(
        self,
        *,
        fulfillment: CorpusAcquisitionStageFulfillment,
    ) -> CorpusAcquisitionPublication:
        manifest = build_dataset_manifest(
            config=self.config,
            corpus_id=self.roots.corpus.corpus_id,
            blocks_plan=fulfillment.blocks_plan,
            blocks_validation=fulfillment.blocks_result.validation,
            blocks_outcome=fulfillment.blocks_result.outcome.value,
            blocks_file_count=fulfillment.blocks_result.file_count,
            source_requirements=self.planning_context.source_requirements,
        )
        acquire_run = build_acquire_run_record(
            config=self.config,
            provider=provider_metadata(self.config),
            acquisition_runtime=self.controller.snapshot(),
            requested_window_seconds=fulfillment.requested_window_seconds,
        )
        temp_state_db = self.temp_root / ".spice" / "state.sqlite"
        write_corpus_state(
            temp_state_db,
            manifest=manifest,
            acquire_run=acquire_run,
        )
        committed_root_kind = commit_corpus_acquisition(
            self.roots.corpus,
            blocks_dir=fulfillment.blocks_result.promote_dir,
            state_db=temp_state_db,
        ).root_kind
        remove_path(self.temp_root)
        return CorpusAcquisitionPublication(
            mode="committed",
            blocks_plan=fulfillment.blocks_plan,
            requested_window_seconds=fulfillment.requested_window_seconds,
            manifest=manifest,
            acquire_run=acquire_run,
            committed_root_kind=committed_root_kind,
        )


def acquire_stage_root(roots: AcquireWorkflowRoots) -> Path:
    return roots.corpus.root_path.parent / f".{roots.corpus.corpus_id}{ACQUIRE_STAGE_DIR_NAME}"


def write_acquire_stage_record(
    path: Path,
    *,
    config: AcquireConfig,
    corpus_id: str,
) -> None:
    record = {
        "chain": config.chain.name,
        "chain_id": config.chain.runtime.chain_id,
        "corpus": config.corpus.name,
        "window_start": config.corpus.window.start.isoformat(),
        "window_end_timestamp": config.corpus.window.end_timestamp,
        "corpus_id": corpus_id,
    }

    def write_record(temp_path: Path) -> None:
        temp_path.write_text(
            json.dumps(record, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

    write_path_atomic(path, write_record)
