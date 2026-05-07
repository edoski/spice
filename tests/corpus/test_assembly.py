from __future__ import annotations

import asyncio
import math
from typing import cast

import pytest

from spice.acquisition import BlockPullPlan, BlockRange, TimestampRange
from spice.config import AcquireConfig, WorkflowTask
from spice.corpus.assembly import assemble_corpus, prepare_corpus_assembly_request
from spice.corpus.contract import CanonicalBlockRow
from spice.storage.workflow_root_materialization import materialize_acquire_roots
from tests.dataset_helpers import make_block_rows


def _load_acquire_config(
    load_workflow_config,
    tmp_path,
    *,
    override: dict[str, object] | None = None,
) -> AcquireConfig:
    return cast(
        AcquireConfig,
        load_workflow_config(
            WorkflowTask.ACQUIRE,
            workspace=tmp_path,
            surface="current_row_fee_dynamics",
            override=override,
        ),
    )


def _plan_for_window(
    window: TimestampRange,
    *,
    start_block: int,
    block_interval_seconds: int = 12,
    row_count: int | None = None,
) -> BlockPullPlan:
    resolved_row_count = (
        row_count
        if row_count is not None
        else max(1, math.ceil((window.end - window.start) / block_interval_seconds))
    )
    return BlockPullPlan(
        window=window,
        block_range=BlockRange(start=start_block, end=start_block + resolved_row_count),
    )


class _PlanningSource:
    def __init__(self, evaluation_window: TimestampRange) -> None:
        self.evaluation_window = evaluation_window
        self.planned_windows: list[TimestampRange] = []

    async def close(self) -> None:
        return None

    async def estimate_recent_block_interval(self, sample_size: int = 128) -> float:
        del sample_size
        return 12.0

    async def plan_window(self, window: TimestampRange) -> BlockPullPlan:
        self.planned_windows.append(window)
        return _plan_for_window(
            window,
            start_block=10_000 if window == self.evaluation_window else 100,
        )

    async def get_block_rows(self, start: int, end: int):
        del start, end
        raise AssertionError("dry run must not fetch rows")


def test_assemble_corpus_dry_run_returns_plan_without_writes(
    tmp_path,
    load_workflow_config,
    acquire_override,
) -> None:
    config = _load_acquire_config(
        load_workflow_config,
        tmp_path,
        override=acquire_override(),
    )
    config.acquisition.dry_run = True
    roots = materialize_acquire_roots(config)
    source = _PlanningSource(
        TimestampRange(
            start=config.evaluation_window_start_timestamp,
            end=config.evaluation_window_end_timestamp,
        )
    )

    result = asyncio.run(
        assemble_corpus(
            prepare_corpus_assembly_request(config=config, roots=roots),
            source,
        )
    )

    assert result.mode == "dry_run"
    assert result.history_plan.block_range.count > 0
    assert result.evaluation_plan.block_range.count > 0
    assert roots.corpus.state_db_path.exists() is False


def test_assemble_corpus_preserves_staging_on_failure(
    tmp_path,
    load_workflow_config,
    acquire_override,
) -> None:
    override = acquire_override()
    override["acquisition"] = {
        "chunk_size": 4,
        "rpc": {
            "batch_size": 4,
            "concurrency": 1,
            "min_batch_size": 4,
            "concurrency_rungs": [1],
        },
    }
    config = _load_acquire_config(load_workflow_config, tmp_path, override=override)
    roots = materialize_acquire_roots(config)
    source = _PlanningSource(
        TimestampRange(
            start=config.evaluation_window_start_timestamp,
            end=config.evaluation_window_end_timestamp,
        )
    )
    messages: list[str] = []

    with pytest.raises(AssertionError, match="dry run must not fetch rows"):
        asyncio.run(
            assemble_corpus(
                prepare_corpus_assembly_request(config=config, roots=roots),
                source,
                status=messages.append,
            )
        )

    assert (
        roots.corpus.root_path.parent / f".{roots.corpus.dataset_id}.acquire-staging"
    ).is_dir()
    assert "history downloading" in messages


def _exercise_short_history_refill(
    tmp_path,
    monkeypatch,
    load_workflow_config,
    acquire_override,
) -> list[tuple[int, int]]:
    override = acquire_override()
    override["acquisition"] = {
        "chunk_size": 128,
        "rpc": {
            "batch_size": 128,
            "concurrency": 1,
            "min_batch_size": 128,
            "concurrency_rungs": [1],
        },
    }
    config = _load_acquire_config(
        load_workflow_config,
        tmp_path,
        override=override,
    )
    roots = materialize_acquire_roots(config)
    evaluation_plan = _plan_for_window(
        TimestampRange(
            start=config.evaluation_window_start_timestamp,
            end=config.evaluation_window_end_timestamp,
        ),
        start_block=10_000
    )
    history_plans = [
        _plan_for_window(
            TimestampRange(
                start=config.history_window_end_timestamp - 50 * 12,
                end=config.history_window_end_timestamp,
            ),
            start_block=1_000
        ),
        _plan_for_window(
            TimestampRange(
                start=config.history_window_end_timestamp - 100 * 12,
                end=config.history_window_end_timestamp,
            ),
            start_block=950
        ),
        _plan_for_window(
            TimestampRange(
                start=config.history_window_end_timestamp - 150 * 12,
                end=config.history_window_end_timestamp,
            ),
            start_block=900
        ),
        _plan_for_window(
            TimestampRange(
                start=config.history_window_end_timestamp - 200 * 12,
                end=config.history_window_end_timestamp,
            ),
            start_block=850
        ),
    ]
    requested_ranges: list[tuple[int, int]] = []
    resolved_capability_samples = iter([1, config.problem.sample_count])
    history_plan_calls = 0

    class Source:
        async def close(self) -> None:
            return None

        async def estimate_recent_block_interval(self, sample_size: int = 128) -> float:
            del sample_size
            return 12.0

        async def plan_window(self, window: TimestampRange) -> BlockPullPlan:
            if window == evaluation_plan.window:
                return evaluation_plan
            nonlocal history_plan_calls
            template = history_plans[history_plan_calls]
            history_plan_calls += 1
            return BlockPullPlan(
                window=window,
                block_range=template.block_range
            )

        async def get_block_rows(self, start: int, end: int):
            requested_ranges.append((start, end))
            if start >= evaluation_plan.block_range.start:
                plan = evaluation_plan
            else:
                plan = next(
                    plan
                    for plan in reversed(history_plans)
                    if start >= plan.block_range.start
                )
            return cast(
                list[CanonicalBlockRow],
                make_block_rows(
                    end - start,
                    start_block=start,
                    start_timestamp=plan.window.start + (start - plan.block_range.start) * 12,
                    chain_id=config.chain.runtime.chain_id,
                    block_interval_seconds=12,
                ),
            )

    monkeypatch.setattr(
        "spice.corpus.planning.CorpusCapabilityPlanningContext.count_valid_history_samples",
        lambda _self, _history_dir: next(resolved_capability_samples),
    )

    request = prepare_corpus_assembly_request(config=config, roots=roots)
    asyncio.run(assemble_corpus(request, Source()))
    return requested_ranges


def test_assemble_corpus_refills_missing_history_prefix(
    tmp_path,
    monkeypatch,
    load_workflow_config,
    acquire_override,
) -> None:
    requested_ranges = _exercise_short_history_refill(
        tmp_path,
        monkeypatch,
        load_workflow_config,
        acquire_override,
    )

    assert (1_000, 1_050) in requested_ranges
    assert (950, 1_000) in requested_ranges
    assert (950, 1_050) not in requested_ranges
