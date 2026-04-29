from __future__ import annotations

import asyncio

import polars as pl
import pytest

from spice.acquisition.errors import (
    OversizedAcquisitionRequestError,
    TransientAcquisitionError,
)
from spice.acquisition.pull import AcquisitionPullController, pull_block_range
from spice.acquisition.types import BlockPullPlan, BlockRange, TimestampRange
from spice.corpus.contract import canonicalize_block_frame
from spice.corpus.io import load_block_frame, write_block_file
from tests.dataset_helpers import make_block_rows


def _plan(start: int, end: int) -> BlockPullPlan:
    return BlockPullPlan(
        window=TimestampRange(start=1_000, end=2_000),
        block_range=BlockRange(start=start, end=end),
        expected_rows=end - start,
    )


class _FakeBlockSource:
    def __init__(self, *, chain_id: int = 1) -> None:
        self.chain_id = chain_id
        self.requests: list[tuple[int, int]] = []

    async def get_block_rows(self, start: int, end: int):
        self.requests.append((start, end))
        return make_block_rows(
            end - start,
            start_block=start,
            start_timestamp=1_000 + (start - 100) * 12,
            chain_id=self.chain_id,
        )


def test_pull_writes_ordered_chunks_with_out_of_order_completion(tmp_path) -> None:
    class DelayedSource(_FakeBlockSource):
        async def get_block_rows(self, start: int, end: int):
            await asyncio.sleep(0.02 if start == 100 else 0)
            return await super().get_block_rows(start, end)

    source = DelayedSource()
    asyncio.run(
        pull_block_range(
            source,
            tmp_path,
            plan=_plan(100, 104),
            chunk_size=2,
            controller=AcquisitionPullController(
                configured_batch_size=2,
                min_batch_size=1,
                concurrency_rungs=(1, 2),
                configured_concurrency=2,
            ),
            chain_name="ethereum",
            expected_chain_id=1,
        )
    )

    frame = load_block_frame(tmp_path)
    assert frame["block_number"].to_list() == [100, 101, 102, 103]
    assert [path.name for path in sorted(tmp_path.glob("*.parquet"))] == [
        "ethereum__blocks__100_to_101.parquet",
        "ethereum__blocks__102_to_103.parquet",
    ]


def test_pull_resumes_completed_prefix(tmp_path) -> None:
    frame = canonicalize_block_frame(
        pl.DataFrame(
            make_block_rows(
                2,
                start_block=100,
                start_timestamp=1_000,
                chain_id=1,
            )
        )
    )
    write_block_file(tmp_path / "ethereum__blocks__100_to_101.parquet", frame)
    source = _FakeBlockSource()

    asyncio.run(
        pull_block_range(
            source,
            tmp_path,
            plan=_plan(100, 104),
            chunk_size=2,
            controller=AcquisitionPullController(
                configured_batch_size=2,
                min_batch_size=1,
                concurrency_rungs=(1,),
                configured_concurrency=1,
            ),
            chain_name="ethereum",
            expected_chain_id=1,
        )
    )

    assert source.requests == [(102, 104)]
    assert load_block_frame(tmp_path)["block_number"].to_list() == [100, 101, 102, 103]


def test_pull_splits_oversized_requests_and_backs_off(tmp_path) -> None:
    class OversizeOnceSource(_FakeBlockSource):
        async def get_block_rows(self, start: int, end: int):
            self.requests.append((start, end))
            if (start, end) == (100, 104):
                raise OversizedAcquisitionRequestError("batch too large")
            return make_block_rows(
                end - start,
                start_block=start,
                start_timestamp=1_000 + (start - 100) * 12,
                chain_id=1,
            )

    source = OversizeOnceSource()
    controller = AcquisitionPullController(
        configured_batch_size=4,
        min_batch_size=2,
        concurrency_rungs=(1,),
        configured_concurrency=1,
    )

    asyncio.run(
        pull_block_range(
            source,
            tmp_path,
            plan=_plan(100, 104),
            chunk_size=2,
            controller=controller,
            chain_name="ethereum",
            expected_chain_id=1,
        )
    )

    assert source.requests == [(100, 104), (100, 102), (102, 104)]
    assert controller.current_batch_size == 2
    assert controller.oversize_backoffs == 1


def test_pull_fails_after_transient_retry_limit(tmp_path) -> None:
    class AlwaysTransientSource(_FakeBlockSource):
        async def get_block_rows(self, start: int, end: int):
            self.requests.append((start, end))
            raise TransientAcquisitionError("timeout")

    source = AlwaysTransientSource()
    with pytest.raises(RuntimeError, match="exceeded 8 transient retry attempts"):
        asyncio.run(
            pull_block_range(
                source,
                tmp_path,
                plan=_plan(100, 101),
                chunk_size=1,
                controller=AcquisitionPullController(
                    configured_batch_size=1,
                    min_batch_size=1,
                    concurrency_rungs=(1,),
                    configured_concurrency=1,
                ),
                chain_name="ethereum",
                expected_chain_id=1,
            )
        )
    assert len(source.requests) == 8


def test_pull_cancellation_cancels_in_flight_tasks(tmp_path) -> None:
    started = asyncio.Event()
    cancelled = asyncio.Event()

    class HangingSource(_FakeBlockSource):
        async def get_block_rows(self, start: int, end: int):
            self.requests.append((start, end))
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                raise

    async def exercise() -> None:
        source = HangingSource()
        task = asyncio.create_task(
            pull_block_range(
                source,
                tmp_path,
                plan=_plan(100, 101),
                chunk_size=1,
                controller=AcquisitionPullController(
                    configured_batch_size=1,
                    min_batch_size=1,
                    concurrency_rungs=(1,),
                    configured_concurrency=1,
                ),
                chain_name="ethereum",
                expected_chain_id=1,
            )
        )
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await asyncio.wait_for(cancelled.wait(), timeout=1)

    asyncio.run(exercise())


def test_pull_controller_backs_off_and_recovers_concurrency() -> None:
    controller = AcquisitionPullController(
        configured_batch_size=8,
        min_batch_size=2,
        concurrency_rungs=(1, 2, 4),
        configured_concurrency=4,
    )

    assert controller.record_oversize_failure() == 4
    assert controller.current_batch_size == 4
    assert controller.record_oversize_failure() == 2
    assert controller.record_oversize_failure() is None

    assert controller.record_transient_failure() is None
    assert controller.record_transient_failure() == 2
    for _ in range(64):
        recovered = controller.record_success()
    assert recovered == 4
