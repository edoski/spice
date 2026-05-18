from __future__ import annotations

import asyncio
import math
from typing import cast

import polars as pl

from spice.acquisition import AcquisitionPullController, BlockPullPlan, BlockRange, TimestampRange
from spice.corpus.contract import CanonicalBlockRow, canonicalize_block_frame
from spice.corpus.io import load_block_frame, write_block_file
from spice.corpus.split_materialization import (
    CorpusSplitIntent,
    CorpusSplitKind,
    CorpusSplitMaterializationSession,
    CorpusSplitMaterializationSpec,
    CorpusSplitOutcome,
)
from tests.dataset_helpers import make_block_rows


def _plan(
    *,
    start_timestamp: int = 1_000,
    end_timestamp: int = 1_048,
    start_block: int = 100,
) -> BlockPullPlan:
    count = max(1, math.ceil((end_timestamp - start_timestamp) / 12))
    return BlockPullPlan(
        window=TimestampRange(start=start_timestamp, end=end_timestamp),
        block_range=BlockRange(start=start_block, end=start_block + count),
    )


def _write_blocks(output_dir, *, start_block: int, row_count: int, start_timestamp: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = canonicalize_block_frame(
        pl.DataFrame(
            make_block_rows(
                row_count,
                start_block=start_block,
                start_timestamp=start_timestamp,
                chain_id=1,
            )
        )
    )
    write_block_file(output_dir / "ethereum__blocks.parquet", frame)


class _RangeSource:
    def __init__(self) -> None:
        self.requests: list[tuple[int, int]] = []

    async def get_block_rows(self, start: int, end: int):
        self.requests.append((start, end))
        return cast(
            list[CanonicalBlockRow],
            make_block_rows(
                end - start,
                start_block=start,
                start_timestamp=1_000 + (start - 100) * 12,
                chain_id=1,
            ),
        )

    async def estimate_recent_block_interval(self, sample_size: int = 128) -> float:
        del sample_size
        return 12.0

    async def plan_window(self, window: TimestampRange) -> BlockPullPlan:
        return _plan(start_timestamp=window.start, end_timestamp=window.end)

    async def close(self) -> None:
        return None


def _session(source: _RangeSource) -> CorpusSplitMaterializationSession:
    return CorpusSplitMaterializationSession(
        materialization=CorpusSplitMaterializationSpec(
            chain_name="ethereum",
            expected_chain_id=1,
            chunk_size=2,
            required_columns=frozenset(
                {"block_number", "timestamp", "chain_id", "base_fee_per_gas"}
            ),
        ),
        block_source=source,
        controller=AcquisitionPullController(
            configured_batch_size=2,
            min_batch_size=1,
            concurrency_rungs=(1,),
            configured_concurrency=1,
        ),
    )


def _intent(tmp_path, plan: BlockPullPlan) -> CorpusSplitIntent:
    return CorpusSplitIntent(
        kind=CorpusSplitKind.BLOCKS,
        output_dir=tmp_path / "blocks",
        working_dir=tmp_path / "work",
        plan=plan,
    )


def test_blocks_materialization_creates_contiguous_dataset(tmp_path) -> None:
    source = _RangeSource()
    plan = _plan()

    result = asyncio.run(_session(source).fulfill(_intent(tmp_path, plan)))

    assert result.outcome is CorpusSplitOutcome.CREATED
    assert result.validation.row_count == plan.block_range.count
    assert source.requests == [(100, 102), (102, 104)]
    assert load_block_frame(result.promote_dir).height == 4


def test_blocks_materialization_reuses_exact_committed_dataset(tmp_path) -> None:
    _write_blocks(tmp_path / "blocks", start_block=100, row_count=4, start_timestamp=1_000)
    source = _RangeSource()

    result = asyncio.run(_session(source).fulfill(_intent(tmp_path, _plan())))

    assert result.outcome is CorpusSplitOutcome.REUSED
    assert source.requests == []
    assert result.path == tmp_path / "blocks"
    assert result.promote_dir is None


def test_blocks_materialization_extends_committed_overlap(tmp_path) -> None:
    _write_blocks(tmp_path / "blocks", start_block=100, row_count=2, start_timestamp=1_000)
    source = _RangeSource()

    result = asyncio.run(_session(source).fulfill(_intent(tmp_path, _plan())))

    assert result.outcome is CorpusSplitOutcome.EXTENDED
    assert source.requests == [(102, 104)]
    assert load_block_frame(result.promote_dir).height == 4


def test_blocks_materialization_extends_committed_middle_overlap(tmp_path) -> None:
    _write_blocks(tmp_path / "blocks", start_block=101, row_count=2, start_timestamp=1_012)
    source = _RangeSource()

    result = asyncio.run(_session(source).fulfill(_intent(tmp_path, _plan())))

    assert result.outcome is CorpusSplitOutcome.EXTENDED
    assert source.requests == [(100, 101), (103, 104)]
    frame = load_block_frame(result.promote_dir)
    assert frame["block_number"].to_list() == [100, 101, 102, 103]
