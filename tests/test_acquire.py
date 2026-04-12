from __future__ import annotations

import asyncio
from concurrent.futures.thread import _threads_queues
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from spice.acquisition.provider import ManagedAsyncHTTPProvider
from spice.acquisition.rpc import BlockPullPlan, BlockRange, RpcController, TimestampRange, Web3BlockClient
from spice.core.console import NullReporter, PlainReporter
from spice.state.catalog import list_dataset_records
from spice.state.dataset import list_acquire_runs, load_dataset_summary
import spice.workflows.acquire as acquire_workflow
from spice.workflows.acquire import _DaemonThreadPoolExecutor
from spice.workflows.acquire import run as run_acquire
from tests.support import (
    acquire_override,
    load_test_acquire_config,
    make_block_rows,
    required_history_blocks,
    write_dataset_dir,
)


class CaptureReporter(NullReporter):
    def __init__(self) -> None:
        self.messages: list[str | None] = []

    def start_task(
        self,
        name: str,
        *,
        total: int | None = None,
        unit: str | None = None,
    ) -> int:
        del name, total, unit
        return 1

    def update_task(
        self,
        task_id: int,
        *,
        completed: int | None = None,
        advance: int | None = None,
        message: str | None = None,
    ) -> None:
        del task_id, completed, advance
        self.messages.append(message)


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
    assert summary.validation.history.rows == required_blocks
    assert summary.validation.evaluation.rows == evaluation_plan.expected_rows
    assert summary.provider.name == "publicnode"
    assert len(runs) == 1
    assert runs[0]["task_id"] == config.task.id
    assert runs[0]["feature_set_id"] == config.feature_set.id
    assert runs[0]["required_history_blocks"] == required_blocks
    assert config.paths.history_dir.is_dir()
    assert config.paths.evaluation_dir.is_dir()
    datasets = list_dataset_records(
        config.paths.catalog_db,
        chain_name=config.chain.name,
        dataset_name=config.dataset.name,
    )
    assert len(datasets) == 1
    assert datasets[0].dataset_id == config.paths.dataset_id


def test_acquire_run_swallows_keyboard_interrupt(tmp_path, monkeypatch) -> None:
    config = load_test_acquire_config(tmp_path, override=acquire_override())

    def _raise_keyboard_interrupt(coro) -> None:
        coro.close()
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        "spice.workflows.acquire._run_async_interruptibly",
        _raise_keyboard_interrupt,
    )

    run_acquire(config, reporter=NullReporter())


def test_acquire_cancellation_during_planning_logs_warning(tmp_path, monkeypatch) -> None:
    config = load_test_acquire_config(tmp_path, override=acquire_override())
    output = StringIO()
    reporter = PlainReporter(console=Console(file=output, force_terminal=False, width=160))

    history_plan = BlockPullPlan(
        window=TimestampRange(
            start=config.evaluation_window_start_timestamp - 120,
            end=config.evaluation_window_start_timestamp,
        ),
        block_range=BlockRange(start=100, end=110),
        expected_rows=10,
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
            del provider, chain

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
            await asyncio.sleep(0.2)
            return history_plan

        async def plan_window(self, window: TimestampRange, *, chunk_size: int) -> BlockPullPlan:
            del window, chunk_size
            await asyncio.sleep(0.2)
            return evaluation_plan

    monkeypatch.setattr("spice.workflows.acquire.Web3BlockClient", FakeAcquireClient)

    async def _exercise() -> None:
        task = asyncio.create_task(acquire_workflow._run_async(config, reporter=reporter))
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(_exercise())

    rendered = output.getvalue()
    assert "history [planning] - resolving window" in rendered
    assert "evaluation [planning] - resolving window" in rendered
    assert "warning: acquire cancelled; partial download removed" in rendered
    assert config.paths.dataset_state_db.exists() is False


def test_acquire_workflow_surfaces_planning_states(tmp_path, monkeypatch) -> None:
    config = load_test_acquire_config(tmp_path, override=acquire_override())
    required_blocks = required_history_blocks(config)
    block_time_seconds = int(round(config.chain.runtime.block_time_seconds))
    output = StringIO()
    reporter = PlainReporter(console=Console(file=output, force_terminal=False, width=160))

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

    run_acquire(config, reporter=reporter)

    rendered = output.getvalue()
    assert "history [planning] - resolving window" in rendered
    assert "history [planning] - 0/" in rendered
    assert "checking existing dataset" in rendered
    assert "validating dataset" in rendered
    assert "evaluation [pending] - 0/32 blocks - waiting for history" in rendered
    assert "evaluation [planning] - 0/32 blocks - checking existing dataset" in rendered
    assert "evaluation [planning] - 0/32 blocks - validating dataset" in rendered


def test_pull_block_range_emits_structured_progress_messages(tmp_path) -> None:
    config = load_test_acquire_config(tmp_path, override=acquire_override())
    reporter = CaptureReporter()
    controller = RpcController(
        configured_batch_size=16,
        min_batch_size=8,
        concurrency_rungs=(8,),
        configured_concurrency=8,
    )
    plan = BlockPullPlan(
        window=TimestampRange(
            start=config.evaluation_window_start_timestamp,
            end=config.evaluation_window_start_timestamp + 16 * 12,
        ),
        block_range=BlockRange(start=100, end=116),
        expected_rows=16,
        expected_files=1,
    )

    class FakeClient(Web3BlockClient):
        def __post_init__(self) -> None:
            self._calls = 0

        async def close(self) -> None:
            return None

        async def get_block_rows(self, block_numbers: list[int]):
            self._calls += 1
            if self._calls == 1:
                raise RuntimeError("response too large")
            return make_block_rows(
                len(block_numbers),
                start_block=block_numbers[0],
                start_timestamp=plan.window.start + (block_numbers[0] - plan.block_range.start) * 12,
                chain_id=config.chain.runtime.chain_id,
                block_time_seconds=12,
            )

    client = FakeClient(config.provider, config.chain)

    asyncio.run(
        client.pull_block_range(
            tmp_path / "history",
            plan=plan,
            chunk_size=64,
            rpc_controller=controller,
            reporter=reporter,
        )
    )

    assert reporter.messages[0] == "batch=16 conc=8"
    assert "oversize backoff batch=8 conc=8" in reporter.messages
    assert reporter.messages.count("batch=8 conc=8") == 2


def test_acquire_executor_threads_skip_python_exit_registry() -> None:
    executor = _DaemonThreadPoolExecutor(max_workers=1, thread_name_prefix="spice-test")
    try:
        future = executor.submit(lambda: None)
        future.result(timeout=1)
        assert executor._threads
        assert all(thread not in _threads_queues for thread in executor._threads)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def test_managed_async_http_provider_disconnect_closes_managed_session() -> None:
    provider = ManagedAsyncHTTPProvider("http://localhost:8545")

    async def _exercise() -> tuple[bool, bool]:
        session = await provider._request_session_manager.async_cache_and_return_session(
            "http://localhost:8545"
        )
        before = session.closed
        await provider.disconnect()
        return before, session.closed

    before_closed, after_closed = asyncio.run(_exercise())
    assert before_closed is False
    assert after_closed is True
