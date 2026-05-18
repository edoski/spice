from __future__ import annotations

import asyncio
import math
from typing import cast

from spice.acquisition import BlockPullPlan, BlockRange, TimestampRange
from spice.config import AcquireConfig, WorkflowTask
from spice.corpus.assembly import assemble_corpus, prepare_corpus_assembly_request
from spice.storage.workflow_root_materialization import materialize_acquire_roots


def _load_acquire_config(load_workflow_config, tmp_path) -> AcquireConfig:
    return cast(
        AcquireConfig,
        load_workflow_config(WorkflowTask.ACQUIRE, workspace=tmp_path),
    )


class _PlanningSource:
    def __init__(self) -> None:
        self.planned_windows: list[TimestampRange] = []

    async def close(self) -> None:
        return None

    async def estimate_recent_block_interval(self, sample_size: int = 128) -> float:
        del sample_size
        return 12.0

    async def plan_window(self, window: TimestampRange) -> BlockPullPlan:
        self.planned_windows.append(window)
        count = max(1, math.ceil((window.end - window.start) / 12))
        return BlockPullPlan(
            window=window,
            block_range=BlockRange(start=100, end=100 + count),
        )

    async def get_block_rows(self, start: int, end: int):
        del start, end
        raise AssertionError("dry run must not fetch rows")


def test_assemble_corpus_dry_run_returns_one_blocks_plan_without_writes(
    tmp_path,
    load_workflow_config,
) -> None:
    config = _load_acquire_config(load_workflow_config, tmp_path)
    config.acquisition.dry_run = True
    roots = materialize_acquire_roots(config)
    source = _PlanningSource()

    result = asyncio.run(
        assemble_corpus(
            prepare_corpus_assembly_request(config=config, roots=roots),
            source,
        )
    )

    expected = TimestampRange(
        start=config.corpus_window_start_timestamp,
        end=config.corpus_window_end_timestamp,
    )
    assert result.mode == "dry_run"
    assert result.blocks_plan.window == expected
    assert result.blocks_plan.block_range.count > 0
    assert source.planned_windows == [expected]
    assert roots.corpus.state_db_path.exists() is False
