from __future__ import annotations

from pathlib import Path

from spice.acquisition.rpc import BlockPullPlan, BlockRange, TimestampRange
from spice.core.console import NullReporter
from spice.state.dataset import list_acquire_runs, load_dataset_summary
from spice.workflows.acquire import run as run_acquire
from tests.support import (
    acquire_override,
    load_test_acquire_config,
    make_block_rows,
    required_history_blocks,
    write_dataset_dir,
)


def test_acquire_workflow_writes_canonical_dataset_and_metadata(
    tmp_path,
    monkeypatch,
) -> None:
    config = load_test_acquire_config(tmp_path, override=acquire_override())
    required_blocks = required_history_blocks(config)
    block_time_seconds = int(round(config.chain.runtime.block_time_seconds))
    history_plan = BlockPullPlan(
        window=TimestampRange(
            start=config.evaluation_window_start_timestamp - required_blocks * block_time_seconds,
            end=config.evaluation_window_start_timestamp,
        ),
        block_range=BlockRange(start=100, end=100 + required_blocks),
        expected_rows=required_blocks,
        expected_files=1,
    )
    evaluation_plan = BlockPullPlan(
        window=TimestampRange(
            start=config.evaluation_window_start_timestamp,
            end=config.evaluation_window_end_timestamp,
        ),
        block_range=BlockRange(start=10_000, end=10_032),
        expected_rows=32,
        expected_files=1,
    )

    class FakeAcquireClient:
        def __init__(self, provider, chain) -> None:
            del provider
            self.chain = chain

        async def close(self) -> None:
            return None

        async def plan_history_window(
            self,
            *,
            end_timestamp: int,
            required_history_blocks: int,
            chunk_size: int,
        ) -> BlockPullPlan:
            del end_timestamp, required_history_blocks, chunk_size
            return history_plan

        async def plan_window(self, window: TimestampRange, *, chunk_size: int) -> BlockPullPlan:
            del chunk_size
            return evaluation_plan if window == evaluation_plan.window else history_plan

        def plan_block_range(
            self,
            block_range: BlockRange,
            *,
            window: TimestampRange,
            chunk_size: int,
        ) -> BlockPullPlan:
            return BlockPullPlan(
                window=window,
                block_range=block_range,
                expected_rows=block_range.count,
                expected_files=max(1, (block_range.count + chunk_size - 1) // chunk_size),
            )

        async def pull_block_range(
            self,
            output_dir: Path,
            *,
            plan: BlockPullPlan,
            chunk_size: int,
            rpc_controller,
            reporter,
        ) -> BlockPullPlan:
            del chunk_size, rpc_controller, reporter
            rows = make_block_rows(
                plan.expected_rows,
                start_block=plan.block_range.start,
                start_timestamp=plan.window.start,
                chain_id=config.chain.runtime.chain_id,
                block_time_seconds=block_time_seconds,
            )
            write_dataset_dir(output_dir, rows)
            return plan

    monkeypatch.setattr("spice.workflows.acquire.Web3BlockClient", FakeAcquireClient)

    run_acquire(config, reporter=NullReporter())

    summary = load_dataset_summary(config.paths.dataset_state_db)
    runs = list_acquire_runs(config.paths.dataset_state_db)
    assert config.paths.dataset_state_db.is_file()
    assert summary.settings.history_context_blocks == config.dataset.history_context_blocks
    assert summary.validation.history.rows == required_blocks
    assert summary.validation.evaluation.rows == evaluation_plan.expected_rows
    assert summary.provider.name == "publicnode"
    assert len(runs) == 1
    assert config.paths.history_dir.is_dir()
    assert config.paths.evaluation_dir.is_dir()
