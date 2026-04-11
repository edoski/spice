from __future__ import annotations

import math
from pathlib import Path

from spice.acquisition.datasets import ensure_block_dataset, ensure_history_dataset
from spice.acquisition.metadata import load_dataset_metadata
from spice.acquisition.rpc import BlockPullPlan, BlockRange, TimestampRange, Web3BlockClient
from spice.acquisition.windowing import history_range_from_metadata
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


def test_ensure_block_dataset_reuses_clean_output_without_pull(tmp_path) -> None:
    output_dir = tmp_path / "history"
    rows = make_block_rows(
        4,
        start_block=100,
        start_timestamp=1_700_000_000,
        include_gas_limit=True,
    )
    write_dataset_dir(output_dir, rows)
    window = _window_for_rows(rows)

    class NoPullClient:
        def pull_timestamp_window(self, *_args, **_kwargs):
            raise AssertionError("clean dataset should be reused")

    plan, validation = ensure_block_dataset(
        block_client=NoPullClient(),
        output_dir=output_dir,
        window=window,
        expected_chain_id=1,
        chunk_size=2,
        rpc_batch_size=8,
        overwrite=False,
        reporter=NullReporter(),
    )

    assert plan is None
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
    window = _window_for_rows(rebuilt_rows)

    class RebuildingClient:
        def __init__(self) -> None:
            self.calls = 0

        def pull_timestamp_window(
            self,
            output_dir: Path,
            *,
            window: TimestampRange,
            chunk_size: int,
            rpc_batch_size: int,
            reporter,
        ) -> BlockPullPlan:
            assert chunk_size == 2
            assert rpc_batch_size == 8
            assert window == _window_for_rows(rebuilt_rows)
            self.calls += 1
            write_dataset_dir(output_dir, rebuilt_rows)
            return BlockPullPlan(
                window=window,
                block_range=BlockRange(start=200, end=204),
                expected_rows=4,
                expected_files=1,
            )

    client = RebuildingClient()
    plan, validation = ensure_block_dataset(
        block_client=client,
        output_dir=output_dir,
        window=window,
        expected_chain_id=1,
        chunk_size=2,
        rpc_batch_size=8,
        overwrite=False,
        reporter=NullReporter(),
    )

    assert client.calls == 1
    assert plan is not None
    assert validation.status == "clean"
    assert load_block_frame(output_dir)["block_number"].to_list() == [200, 201, 202, 203]


def test_ensure_history_dataset_expands_until_required_block_count(tmp_path) -> None:
    config = compose_experiment("acquire", overrides=base_overrides(tmp_path))
    initial_window = TimestampRange(start=1_700_000_000, end=1_700_000_120)
    output_dir = tmp_path / "history"

    class ExpandingHistoryClient:
        def __init__(self) -> None:
            self.windows: list[TimestampRange] = []

        def pull_timestamp_window(
            self,
            output_dir: Path,
            *,
            window: TimestampRange,
            chunk_size: int,
            rpc_batch_size: int,
            reporter,
        ) -> BlockPullPlan:
            self.windows.append(window)
            row_count = 4 if len(self.windows) == 1 else 6
            rows = make_block_rows(
                row_count,
                start_block=1 if len(self.windows) == 1 else 101,
                start_timestamp=window.start,
                include_gas_limit=True,
            )
            write_dataset_dir(output_dir, rows)
            return BlockPullPlan(
                window=window,
                block_range=BlockRange(
                    start=int(rows[0]["block_number"]),
                    end=int(rows[-1]["block_number"]) + 1,
                ),
                expected_rows=row_count,
                expected_files=1,
            )

    client = ExpandingHistoryClient()
    plan, validation, resolved_window = ensure_history_dataset(
        config=config,
        block_client=client,
        output_dir=output_dir,
        history_window=initial_window,
        required_history_blocks=6,
        reporter=NullReporter(),
    )

    assert plan is not None
    assert validation.status == "clean"
    assert validation.row_count == 6
    assert len(client.windows) == 2
    assert client.windows[1].start < client.windows[0].start
    assert resolved_window == client.windows[1]
    assert load_block_frame(output_dir).height == 6


def test_web3_block_client_pull_timestamp_window_writes_chunked_dataset(
    tmp_path,
    monkeypatch,
) -> None:
    timestamps = {
        0: 100,
        1: 112,
        2: 124,
        3: 136,
        4: 148,
        5: 160,
    }

    class FakeBatch:
        def __init__(self) -> None:
            self.requests: list[dict[str, int]] = []

        def __enter__(self) -> FakeBatch:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def add(self, block: dict[str, int]) -> None:
            self.requests.append(block)

        def execute(self) -> list[dict[str, int]]:
            return list(self.requests)

    class FakeEth:
        block_number = 5

        def get_block(
            self,
            block_number: int | str,
            _full_transactions: bool = False,
        ) -> dict[str, int]:
            if block_number == "latest":
                block_number = 5
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
        "spice.acquisition.rpc.build_web3",
        lambda _provider, _chain: FakeWeb3(),
    )

    config = compose_experiment("acquire", overrides=base_overrides(tmp_path))
    client = Web3BlockClient(provider=config.provider, chain=config.chain)
    plan = client.pull_timestamp_window(
        tmp_path / "history",
        window=TimestampRange(start=112, end=160),
        chunk_size=2,
        rpc_batch_size=3,
        reporter=NullReporter(),
    )

    frame = load_block_frame(tmp_path / "history")

    assert plan.expected_rows == 4
    assert plan.expected_files == 2
    assert frame["block_number"].to_list() == [1, 2, 3, 4]
    assert len(list((tmp_path / "history").glob("*.parquet"))) == 2


def test_acquire_workflow_writes_direct_block_datasets_and_metadata(
    tmp_path,
    monkeypatch,
) -> None:
    config = compose_experiment(
        "acquire",
        overrides=base_overrides(tmp_path)
        + [
            "dataset.temporal.lookback_seconds=24",
            "dataset.temporal.max_delay_seconds=12",
            "dataset.sampling.anchor_count=4",
        ],
    )

    class FakeWorkflowBlockClient:
        def __init__(self, provider, chain) -> None:
            del provider
            self.chain = chain

        def plan_window(self, window: TimestampRange, *, chunk_size: int) -> BlockPullPlan:
            expected_rows = max(
                1,
                math.ceil((window.end - window.start) / self.chain.block_time_seconds),
            )
            expected_files = math.ceil(expected_rows / chunk_size)
            return BlockPullPlan(
                window=window,
                block_range=BlockRange(start=0, end=expected_rows),
                expected_rows=expected_rows,
                expected_files=expected_files,
            )

        def pull_timestamp_window(
            self,
            output_dir: Path,
            *,
            window: TimestampRange,
            chunk_size: int,
            rpc_batch_size: int,
            reporter,
        ) -> BlockPullPlan:
            del chunk_size, rpc_batch_size, reporter
            row_count = 256 if output_dir.name == "history" else 32
            rows = make_block_rows(
                row_count,
                start_block=1 if output_dir.name == "history" else 10_001,
                start_timestamp=window.start,
                block_time_seconds=int(self.chain.block_time_seconds),
                include_gas_limit=True,
            )
            assert int(rows[-1]["timestamp"]) < window.end
            write_dataset_dir(output_dir, rows)
            return BlockPullPlan(
                window=window,
                block_range=BlockRange(
                    start=int(rows[0]["block_number"]),
                    end=int(rows[-1]["block_number"]) + 1,
                ),
                expected_rows=row_count,
                expected_files=1,
            )

    monkeypatch.setattr(
        "spice.workflows.acquire.Web3BlockClient",
        FakeWorkflowBlockClient,
    )

    run_acquire(config, reporter=NullReporter())

    metadata_path = Path(config.paths.dataset_metadata_path)
    history_dir = Path(config.paths.history_dir)
    evaluation_dir = Path(config.paths.evaluation_dir)
    metadata = load_dataset_metadata(metadata_path)

    assert metadata is not None
    assert metadata.paths.history == history_dir.as_posix()
    assert metadata.paths.evaluation == evaluation_dir.as_posix()
    assert metadata.validation.history.status == "clean"
    assert metadata.validation.evaluation.status == "clean"
    assert history_range_from_metadata(metadata).end == config.dataset.window.start_timestamp
    assert load_block_frame(history_dir).height == 256
    assert load_block_frame(evaluation_dir).height == 32
