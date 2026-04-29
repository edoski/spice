from __future__ import annotations

import asyncio
import math
from typing import cast

import pytest

from spice.acquisition import BlockPullPlan, BlockRange, TimestampRange
from spice.config import AcquireConfig, WorkflowTask
from spice.corpus.assembly import CorpusAssemblyRequest, assemble_corpus
from spice.storage.workflow_paths import resolve_workflow_paths


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
) -> BlockPullPlan:
    row_count = max(1, math.ceil((window.end - window.start) / block_interval_seconds))
    return BlockPullPlan(
        window=window,
        block_range=BlockRange(start=start_block, end=start_block + row_count),
        expected_rows=row_count,
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

    def plan_block_range(
        self,
        block_range: BlockRange,
        *,
        window: TimestampRange,
    ) -> BlockPullPlan:
        return BlockPullPlan(
            window=window,
            block_range=block_range,
            expected_rows=block_range.count,
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
    paths = resolve_workflow_paths(config)
    source = _PlanningSource(
        TimestampRange(
            start=config.evaluation_window_start_timestamp,
            end=config.evaluation_window_end_timestamp,
        )
    )

    result = asyncio.run(
        assemble_corpus(
            CorpusAssemblyRequest(config=config, paths=paths),
            source,
        )
    )

    assert result.mode == "dry_run"
    assert result.history_plan.expected_rows > 0
    assert result.evaluation_plan.expected_rows > 0
    assert result.manifest is None
    assert paths.corpus_state_db.exists() is False


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
    paths = resolve_workflow_paths(config)
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
                CorpusAssemblyRequest(config=config, paths=paths),
                source,
                status=messages.append,
            )
        )

    assert (paths.corpus_root.parent / f".{paths.corpus_id}.acquire-staging").is_dir()
    assert "history downloading" in messages
