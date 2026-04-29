"""Corpus Assembly from acquisition output."""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ..acquisition import (
    AcquisitionPullController,
    BlockPullPlan,
    BlockSource,
    TimestampRange,
    evaluation_range,
)
from ..config.models import AcquireConfig
from ..core.files import remove_path
from ..features import compile_feature_contract
from ..storage.corpus import write_dataset_state
from ..storage.engine import RootKind
from ..storage.lifecycle import PartialRootCommit
from ..storage.workflow_paths import WorkflowPaths
from ..temporal.contracts import compile_problem_contract
from ._assembly_splits import (
    CorpusSplitOutcome,
    DatasetBuildResult,
    ensure_evaluation_split,
    ensure_history_split,
)
from .io import load_block_frame
from .metadata import (
    AcquireRunRecord,
    DatasetManifest,
    build_acquire_run_record,
    build_dataset_manifest,
    provider_metadata,
)

HISTORY_WINDOW_CUSHION_RATIO = 0.10
HISTORY_REFILL_CUSHION_RATIO = 0.10
HISTORY_REFILL_ATTEMPT_LIMIT = 3
ACQUIRE_STAGE_DIR_NAME = ".acquire-staging"

StatusCallback = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class CorpusAssemblyRequest:
    config: AcquireConfig
    paths: WorkflowPaths


@dataclass(frozen=True, slots=True)
class CorpusAssemblyResult:
    mode: Literal["dry_run", "committed"]
    history_plan: BlockPullPlan
    evaluation_plan: BlockPullPlan
    requested_history_window_seconds: int
    resolved_capability_samples: int | None
    history_outcome: CorpusSplitOutcome | None
    history_row_count: int | None
    evaluation_outcome: CorpusSplitOutcome | None
    evaluation_row_count: int | None
    manifest: DatasetManifest | None
    acquire_run: AcquireRunRecord | None
    committed_root_kind: RootKind | None


def _noop_status(message: str) -> None:
    del message


def _with_cushion(value: float, ratio: float) -> int:
    return max(1, math.ceil(value * (1.0 + ratio)))


def _history_window(config: AcquireConfig, window_seconds: int) -> TimestampRange:
    return TimestampRange(
        start=max(0, config.history_window_end_timestamp - window_seconds),
        end=config.history_window_end_timestamp,
    )


def _acquire_stage_root(paths: WorkflowPaths) -> Path:
    return paths.corpus_root.parent / f".{paths.corpus_id}{ACQUIRE_STAGE_DIR_NAME}"


def _write_acquire_stage_record(
    path: Path,
    *,
    config: AcquireConfig,
    corpus_id: str,
) -> None:
    record = {
        "chain": config.chain.name,
        "chain_id": config.chain.runtime.chain_id,
        "dataset": config.dataset.name,
        "evaluation_date": config.dataset.evaluation_date.isoformat(),
        "corpus_id": corpus_id,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")


def _count_valid_history_samples(
    *,
    history_dir: Path,
    config: AcquireConfig,
) -> int:
    feature_contract = compile_feature_contract(features=config.features)
    problem_contract = compile_problem_contract(
        problem=config.problem,
        feature_contract=feature_contract,
        chain_runtime=config.chain.runtime,
    )
    blocks = load_block_frame(history_dir).sort("block_number")
    feature_table = feature_contract.build_table(blocks)
    return problem_contract.count_valid_capability_samples(feature_table)


async def _initial_plans(
    request: CorpusAssemblyRequest,
    block_source: BlockSource,
) -> tuple[BlockPullPlan, BlockPullPlan, int]:
    config = request.config
    feature_contract = compile_feature_contract(features=config.features)
    problem_contract = compile_problem_contract(
        problem=config.problem,
        feature_contract=feature_contract,
        chain_runtime=config.chain.runtime,
    )
    evaluation_window = evaluation_range(
        config.evaluation_window_start_timestamp,
        config.evaluation_window_end_timestamp,
    )
    evaluation_plan = await block_source.plan_window(evaluation_window)
    recent_block_interval_seconds = await block_source.estimate_recent_block_interval()
    bootstrap_history_window_seconds = problem_contract.initial_history_window_seconds(
        recent_block_interval_seconds,
    )
    requested_history_window_seconds = _with_cushion(
        bootstrap_history_window_seconds,
        HISTORY_WINDOW_CUSHION_RATIO,
    )
    history_plan = await block_source.plan_window(
        _history_window(config, requested_history_window_seconds),
    )
    return history_plan, evaluation_plan, requested_history_window_seconds


async def _ensure_sufficient_history(
    *,
    request: CorpusAssemblyRequest,
    block_source: BlockSource,
    controller: AcquisitionPullController,
    temp_root: Path,
    initial_history_plan: BlockPullPlan,
    requested_history_window_seconds: int,
    status: StatusCallback,
) -> tuple[DatasetBuildResult, int, BlockPullPlan, int]:
    config = request.config
    paths = request.paths
    history_plan = initial_history_plan
    history_output_dir = paths.history_dir
    working_dir = temp_root / "history-initial"
    history_result = await ensure_history_split(
        config=config,
        block_source=block_source,
        output_dir=history_output_dir,
        working_dir=working_dir,
        history_plan=history_plan,
        controller=controller,
        status=status,
    )
    resolved_capability_samples = _count_valid_history_samples(
        history_dir=history_result.path,
        config=config,
    )

    for refill_attempt in range(1, HISTORY_REFILL_ATTEMPT_LIMIT + 1):
        if resolved_capability_samples >= config.problem.sample_count:
            break
        validation = history_result.validation
        if (
            validation.first_timestamp is None
            or validation.last_timestamp is None
            or validation.row_count <= 1
        ):
            raise RuntimeError("Cannot compute observed history cadence from validation report")
        sample_shortfall = config.problem.sample_count - resolved_capability_samples
        observed_seconds_per_block = max(
            1.0,
            (validation.last_timestamp - validation.first_timestamp)
            / (validation.row_count - 1),
        )
        next_requested_history_window_seconds = max(
            requested_history_window_seconds,
            config.history_window_end_timestamp - validation.first_timestamp,
        ) + _with_cushion(
            sample_shortfall * observed_seconds_per_block,
            HISTORY_REFILL_CUSHION_RATIO,
        )
        if next_requested_history_window_seconds <= requested_history_window_seconds:
            raise RuntimeError(
                "History sizing policy stopped expanding before capability samples were met: "
                f"valid={resolved_capability_samples}, required={config.problem.sample_count}"
            )
        requested_history_window_seconds = next_requested_history_window_seconds
        history_plan = await block_source.plan_window(
            _history_window(config, requested_history_window_seconds),
        )
        status(
            "history refilling "
            f"samples={resolved_capability_samples}/{config.problem.sample_count}"
        )
        history_result = await ensure_history_split(
            config=config,
            block_source=block_source,
            output_dir=history_result.path,
            working_dir=temp_root / f"history-refill-{refill_attempt}",
            history_plan=history_plan,
            controller=controller,
            status=status,
        )
        resolved_capability_samples = _count_valid_history_samples(
            history_dir=history_result.path,
            config=config,
        )

    if resolved_capability_samples < config.problem.sample_count:
        raise RuntimeError(
            "History sizing policy under-requested capability samples: "
            f"valid={resolved_capability_samples}, "
            f"required={config.problem.sample_count}, "
            f"refill_attempts={HISTORY_REFILL_ATTEMPT_LIMIT}"
        )
    return (
        history_result,
        resolved_capability_samples,
        history_plan,
        requested_history_window_seconds,
    )


async def assemble_corpus(
    request: CorpusAssemblyRequest,
    block_source: BlockSource,
    *,
    status: StatusCallback | None = None,
) -> CorpusAssemblyResult:
    config = request.config
    paths = request.paths
    emit = status or _noop_status
    history_plan, evaluation_plan, requested_history_window_seconds = await _initial_plans(
        request,
        block_source,
    )

    if config.acquisition.dry_run:
        return CorpusAssemblyResult(
            mode="dry_run",
            history_plan=history_plan,
            evaluation_plan=evaluation_plan,
            requested_history_window_seconds=requested_history_window_seconds,
            resolved_capability_samples=None,
            history_outcome=None,
            history_row_count=None,
            evaluation_outcome=None,
            evaluation_row_count=None,
            manifest=None,
            acquire_run=None,
            committed_root_kind=None,
        )

    controller = AcquisitionPullController.from_config(config.acquisition)
    current_provider = provider_metadata(config)
    paths.corpus_root.parent.mkdir(parents=True, exist_ok=True)
    temp_root = _acquire_stage_root(paths)
    temp_root.mkdir(parents=True, exist_ok=True)
    _write_acquire_stage_record(
        temp_root / ".spice" / "acquire-stage.json",
        config=config,
        corpus_id=paths.corpus_id,
    )

    history_result, resolved_capability_samples, history_plan, requested_history_window_seconds = (
        await _ensure_sufficient_history(
            request=request,
            block_source=block_source,
            controller=controller,
            temp_root=temp_root,
            initial_history_plan=history_plan,
            requested_history_window_seconds=requested_history_window_seconds,
            status=emit,
        )
    )

    evaluation_result = await ensure_evaluation_split(
        config=config,
        block_source=block_source,
        output_dir=paths.evaluation_dir,
        working_dir=temp_root,
        evaluation_plan=evaluation_plan,
        controller=controller,
        status=emit,
    )
    manifest = build_dataset_manifest(
        config=config,
        dataset_id=paths.corpus_id,
        history_request_start_timestamp=history_plan.window.start,
        history_request_end_timestamp=history_plan.window.end,
        evaluation_request_start_timestamp=evaluation_plan.window.start,
        evaluation_request_end_timestamp=evaluation_plan.window.end,
        history_validation=history_result.validation,
        evaluation_validation=evaluation_result.validation,
    )
    acquire_run = build_acquire_run_record(
        config=config,
        provider=current_provider,
        acquisition_runtime=controller.snapshot(),
        requested_history_window_seconds=requested_history_window_seconds,
        resolved_capability_samples=resolved_capability_samples,
    )
    temp_state_db = temp_root / ".spice" / "state.sqlite"
    write_dataset_state(
        temp_state_db,
        manifest=manifest,
        acquire_run=acquire_run,
    )
    commit = PartialRootCommit(
        storage_root=paths.output_root,
        root_path=paths.corpus_root,
    )
    commit.add(paths.history_dir, history_result.promote_dir)
    commit.add(paths.evaluation_dir, evaluation_result.promote_dir)
    commit.add(paths.corpus_state_db, temp_state_db)
    committed_root_kind = commit.commit()
    remove_path(temp_root)
    return CorpusAssemblyResult(
        mode="committed",
        history_plan=history_plan,
        evaluation_plan=evaluation_plan,
        requested_history_window_seconds=requested_history_window_seconds,
        resolved_capability_samples=resolved_capability_samples,
        history_outcome=history_result.outcome,
        history_row_count=history_result.validation.row_count,
        evaluation_outcome=evaluation_result.outcome,
        evaluation_row_count=evaluation_result.validation.row_count,
        manifest=manifest,
        acquire_run=acquire_run,
        committed_root_kind=committed_root_kind,
    )
