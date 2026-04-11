from __future__ import annotations

import asyncio
from pathlib import Path

from web3.exceptions import Web3RPCError

from spice.acquisition.datasets import ensure_block_dataset, ensure_history_dataset
from spice.acquisition.metadata import load_dataset_metadata
from spice.acquisition.rpc import BlockPullPlan, BlockRange, RpcController, TimestampRange, Web3BlockClient
from spice.acquisition.windowing import history_range_from_metadata, required_history_block_count
from spice.core.console import NullReporter
from spice.data.io import load_block_frame
from spice.workflows.acquire import run as run_acquire
from tests.support import (
    base_overrides,
    compose_experiment,
    make_block_rows,
    write_dataset_dir,
)


def _window_for_rows(
    rows: list[dict[str, int | None]],
    *,
    block_time_seconds: int = 12,
) -> TimestampRange:
    start_timestamp = int(rows[0]["timestamp"])
    end_timestamp = int(rows[-1]["timestamp"]) + block_time_seconds
    return TimestampRange(start=start_timestamp, end=end_timestamp)


def _rpc_controller(
    *,
    batch_size: int = 8,
    min_batch_size: int = 2,
    concurrency: int = 2,
    concurrency_rungs: tuple[int, ...] = (1, 2),
) -> RpcController:
    return RpcController(
        configured_batch_size=batch_size,
        min_batch_size=min_batch_size,
        concurrency_rungs=concurrency_rungs,
        configured_concurrency=concurrency,
    )


def test_ensure_block_dataset_reuses_clean_output_without_pull(tmp_path) -> None:
    output_dir = tmp_path / "history"
    rows = make_block_rows(
        4,
        start_block=100,
        start_timestamp=1_700_000_000,
        include_gas_limit=True,
    )
    write_dataset_dir(output_dir, rows)
    plan = BlockPullPlan(
        window=_window_for_rows(rows),
        block_range=BlockRange(start=100, end=104),
        expected_rows=4,
        expected_files=2,
    )

    class NoPullClient:
        async def pull_block_range(self, *_args, **_kwargs):
            raise AssertionError("clean dataset should be reused")

    pulled_plan, validation = asyncio.run(
        ensure_block_dataset(
            block_client=NoPullClient(),
            output_dir=output_dir,
            plan=plan,
            expected_chain_id=1,
            chunk_size=2,
            rpc_controller=_rpc_controller(),
            overwrite=False,
            reporter=NullReporter(),
        )
    )

    assert pulled_plan is None
    assert validation.status == "clean"
    assert validation.row_count == 4


def test_ensure_block_dataset_rebuilds_invalid_existing_output(tmp_path) -> None:
    output_dir = tmp_path / "history"
    invalid_rows = make_block_rows(
        4,
        start_block=100,
        start_timestamp=1_700_000_000,
        include_gas_limit=True,
    )
    write_dataset_dir(output_dir, invalid_rows[:3] + [invalid_rows[2]])

    rebuilt_rows = make_block_rows(
        4,
        start_block=200,
        start_timestamp=1_700_000_100,
        include_gas_limit=True,
    )
    plan = BlockPullPlan(
        window=_window_for_rows(rebuilt_rows),
        block_range=BlockRange(start=200, end=204),
        expected_rows=4,
        expected_files=2,
    )

    class RebuildingClient:
        def __init__(self) -> None:
            self.calls = 0

        async def pull_block_range(
            self,
            output_dir: Path,
            *,
            plan: BlockPullPlan,
            chunk_size: int,
            rpc_controller: RpcController,
            reporter,
        ) -> BlockPullPlan:
            del reporter
            assert chunk_size == 2
            assert rpc_controller.current_batch_size == 8
            assert plan.block_range == BlockRange(start=200, end=204)
            self.calls += 1
            write_dataset_dir(output_dir, rebuilt_rows)
            return plan

    client = RebuildingClient()
    pulled_plan, validation = asyncio.run(
        ensure_block_dataset(
            block_client=client,
            output_dir=output_dir,
            plan=plan,
            expected_chain_id=1,
            chunk_size=2,
            rpc_controller=_rpc_controller(batch_size=8),
            overwrite=False,
            reporter=NullReporter(),
        )
    )

    assert client.calls == 1
    assert pulled_plan == plan
    assert validation.status == "clean"
    assert load_block_frame(output_dir)["block_number"].to_list() == [200, 201, 202, 203]


def test_ensure_history_dataset_expands_by_block_count_until_requirement_met(tmp_path) -> None:
    config = compose_experiment(
        "acquire",
        overrides=base_overrides(tmp_path) + ["acquisition.chunk_size=2"],
    )
    output_dir = tmp_path / "history"
    initial_plan = BlockPullPlan(
        window=TimestampRange(start=1_700_000_000, end=1_700_000_120),
        block_range=BlockRange(start=10, end=16),
        expected_rows=6,
        expected_files=3,
    )

    class ExpandingHistoryClient:
        def __init__(self) -> None:
            self.plans: list[BlockPullPlan] = []

        async def pull_block_range(
            self,
            output_dir: Path,
            *,
            plan: BlockPullPlan,
            chunk_size: int,
            rpc_controller: RpcController,
            reporter,
        ) -> BlockPullPlan:
            del chunk_size, rpc_controller, reporter
            self.plans.append(plan)
            row_count = 4 if len(self.plans) == 1 else 6
            rows = make_block_rows(
                row_count,
                start_block=plan.block_range.start,
                start_timestamp=plan.window.start,
                include_gas_limit=True,
            )
            write_dataset_dir(output_dir, rows)
            return plan

        async def expand_history_plan(
            self,
            current: BlockPullPlan,
            *,
            observed_row_count: int,
            required_history_blocks: int,
            chunk_size: int,
        ) -> BlockPullPlan:
            assert observed_row_count == 4
            assert required_history_blocks == 6
            assert chunk_size == 2
            return BlockPullPlan(
                window=TimestampRange(start=current.window.start - 48, end=current.window.end),
                block_range=BlockRange(
                    start=current.block_range.start - 4,
                    end=current.block_range.end,
                ),
                expected_rows=10,
                expected_files=5,
            )

    client = ExpandingHistoryClient()
    pulled_plan, validation, resolved_plan = asyncio.run(
        ensure_history_dataset(
            config=config,
            block_client=client,
            output_dir=output_dir,
            history_plan=initial_plan,
            required_history_blocks=6,
            rpc_controller=_rpc_controller(batch_size=8),
            reporter=NullReporter(),
        )
    )

    assert pulled_plan == client.plans[1]
    assert validation.status == "clean"
    assert validation.row_count == 6
    assert len(client.plans) == 2
    assert client.plans[1].block_range.start == 6
    assert resolved_plan == client.plans[1]
    assert load_block_frame(output_dir).height == 6


def test_web3_block_client_pull_block_range_retries_oversized_batches_and_preserves_order(
    tmp_path,
    monkeypatch,
) -> None:
    timestamps = {block: 100 + block * 12 for block in range(6)}

    class FakeBatch:
        def __init__(self) -> None:
            self.requests: list[object] = []

        async def __aenter__(self) -> FakeBatch:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        def add(self, block: object) -> None:
            self.requests.append(block)

        async def async_execute(self) -> list[dict[str, int]]:
            blocks = [await request for request in self.requests]
            if len(blocks) > 2:
                raise Web3RPCError(
                    "response too large",
                    rpc_response={"error": {"code": -32003, "message": "response too large"}},
                )
            return blocks

    class FakeEth:
        async def get_block(
            self,
            block_number: int | str,
            _full_transactions: bool = False,
        ) -> dict[str, int]:
            number = int(block_number)
            return {
                "number": number,
                "timestamp": timestamps[number],
                "baseFeePerGas": 1_000_000_000 + number,
                "gasUsed": 20_000_000 + number,
                "gasLimit": 30_000_000 + number,
            }

    class FakeWeb3:
        eth = FakeEth()

        def batch_requests(self) -> FakeBatch:
            return FakeBatch()

    monkeypatch.setattr(
        "spice.acquisition.rpc.build_async_web3",
        lambda _provider, _chain: FakeWeb3(),
    )

    client = Web3BlockClient(
        provider=compose_experiment("acquire", overrides=base_overrides(tmp_path)).provider,
        chain=compose_experiment("acquire", overrides=base_overrides(tmp_path)).chain,
    )
    plan = BlockPullPlan(
        window=TimestampRange(start=112, end=172),
        block_range=BlockRange(start=1, end=6),
        expected_rows=5,
        expected_files=2,
    )
    controller = _rpc_controller(batch_size=4, min_batch_size=2, concurrency=2)

    pulled_plan = asyncio.run(
        client.pull_block_range(
            tmp_path / "history",
            plan=plan,
            chunk_size=3,
            rpc_controller=controller,
            reporter=NullReporter(),
        )
    )

    frame = load_block_frame(tmp_path / "history")

    assert pulled_plan == plan
    assert frame["block_number"].to_list() == [1, 2, 3, 4, 5]
    assert controller.current_batch_size == 2
    assert controller.oversize_error_count == 1
    assert controller.oversize_backoffs == 1


def test_web3_block_client_retries_single_transient_failure_without_concurrency_backoff(
    tmp_path,
    monkeypatch,
) -> None:
    attempts: dict[tuple[int, ...], int] = {}

    class FakeBatch:
        def __init__(self) -> None:
            self.requests: list[object] = []

        async def __aenter__(self) -> FakeBatch:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        def add(self, block: object) -> None:
            self.requests.append(block)

        async def async_execute(self) -> list[dict[str, int]]:
            blocks = [await request for request in self.requests]
            key = tuple(int(block["number"]) for block in blocks)
            attempts[key] = attempts.get(key, 0) + 1
            if key == (0, 1) and attempts[key] == 1:
                raise asyncio.TimeoutError("transient timeout")
            return blocks

    class FakeEth:
        async def get_block(
            self,
            block_number: int | str,
            _full_transactions: bool = False,
        ) -> dict[str, int]:
            number = int(block_number)
            return {
                "number": number,
                "timestamp": 100 + number * 12,
                "baseFeePerGas": 1_000_000_000 + number,
                "gasUsed": 20_000_000 + number,
                "gasLimit": 30_000_000 + number,
            }

    class FakeWeb3:
        eth = FakeEth()

        def batch_requests(self) -> FakeBatch:
            return FakeBatch()

    monkeypatch.setattr(
        "spice.acquisition.rpc.build_async_web3",
        lambda _provider, _chain: FakeWeb3(),
    )

    client = Web3BlockClient(
        provider=compose_experiment("acquire", overrides=base_overrides(tmp_path)).provider,
        chain=compose_experiment("acquire", overrides=base_overrides(tmp_path)).chain,
    )
    plan = BlockPullPlan(
        window=TimestampRange(start=100, end=148),
        block_range=BlockRange(start=0, end=4),
        expected_rows=4,
        expected_files=2,
    )
    controller = _rpc_controller(batch_size=2, min_batch_size=1, concurrency=2)

    asyncio.run(
        client.pull_block_range(
            tmp_path / "history",
            plan=plan,
            chunk_size=2,
            rpc_controller=controller,
            reporter=NullReporter(),
        )
    )

    assert controller.current_concurrency == 2
    assert controller.transient_error_count == 1
    assert controller.transient_backoffs == 0
    assert load_block_frame(tmp_path / "history")["block_number"].to_list() == [0, 1, 2, 3]


def test_acquire_workflow_writes_runtime_metadata(tmp_path, monkeypatch) -> None:
    config = compose_experiment(
        "acquire",
        overrides=base_overrides(tmp_path)
        + [
            "dataset.temporal.lookback_seconds=24",
            "dataset.temporal.max_delay_seconds=12",
            "dataset.sampling.anchor_count=4",
        ],
    )
    required_history_blocks = required_history_block_count(config)
    block_time_seconds = int(config.chain.block_time_seconds)
    expected_history_start = (
        config.dataset.window.start_timestamp - required_history_blocks * block_time_seconds
    )

    class FakeWorkflowBlockClient:
        history_requests: list[tuple[int, int, int]] = []

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
            self.__class__.history_requests.append(
                (end_timestamp, required_history_blocks, chunk_size)
            )
            return BlockPullPlan(
                window=TimestampRange(start=expected_history_start, end=end_timestamp),
                block_range=BlockRange(
                    start=100,
                    end=100 + required_history_blocks,
                ),
                expected_rows=required_history_blocks,
                expected_files=1,
            )

        async def plan_window(self, window: TimestampRange, *, chunk_size: int) -> BlockPullPlan:
            del chunk_size
            expected_rows = 32
            return BlockPullPlan(
                window=window,
                block_range=BlockRange(start=10_001, end=10_001 + expected_rows),
                expected_rows=expected_rows,
                expected_files=1,
            )

        async def pull_block_range(
            self,
            output_dir: Path,
            *,
            plan: BlockPullPlan,
            chunk_size: int,
            rpc_controller: RpcController,
            reporter,
        ) -> BlockPullPlan:
            del chunk_size, reporter
            rows = make_block_rows(
                plan.expected_rows,
                start_block=plan.block_range.start,
                start_timestamp=plan.window.start,
                block_time_seconds=block_time_seconds,
                include_gas_limit=True,
            )
            assert int(rows[-1]["timestamp"]) < plan.window.end
            assert rpc_controller.current_batch_size == config.acquisition.rpc_batch_size
            write_dataset_dir(output_dir, rows)
            return plan

    monkeypatch.setattr(
        "spice.workflows.acquire.Web3BlockClient",
        FakeWorkflowBlockClient,
    )

    run_acquire(config, reporter=NullReporter())

    metadata_path = config.paths.dataset_metadata_path
    history_dir = config.paths.history_dir
    evaluation_dir = config.paths.evaluation_dir
    metadata = load_dataset_metadata(metadata_path)

    assert metadata is not None
    assert FakeWorkflowBlockClient.history_requests == [
        (
            config.dataset.window.start_timestamp,
            required_history_blocks,
            config.acquisition.chunk_size,
        )
    ]
    assert metadata.paths.history == history_dir.as_posix()
    assert metadata.paths.evaluation == evaluation_dir.as_posix()
    assert metadata.validation.history.status == "clean"
    assert metadata.validation.evaluation.status == "clean"
    assert history_range_from_metadata(metadata).start == expected_history_start
    assert history_range_from_metadata(metadata).end == config.dataset.window.start_timestamp
    assert metadata.runtime.acquisition.configured_batch_size == config.acquisition.rpc_batch_size
    assert metadata.runtime.acquisition.final_batch_size == config.acquisition.rpc_batch_size
    assert metadata.runtime.acquisition.configured_concurrency == config.acquisition.rpc_concurrency
    assert metadata.runtime.acquisition.final_concurrency == config.acquisition.rpc_concurrency
    assert metadata.runtime.acquisition.transient_backoffs == 0
    assert load_block_frame(history_dir).height == required_history_blocks
    assert load_block_frame(evaluation_dir).height == 32
