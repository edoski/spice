"""web3.py-backed helpers for direct block acquisition."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil
from pathlib import Path
from typing import Any, cast

import polars as pl
from web3 import Web3

from ..core.config import AcquisitionConfig, ChainConfig, ProviderConfig
from ..core.console import NullReporter, Reporter
from ..data.block_schema import canonicalize_block_frame
from ..data.io import write_block_file
from .provider import build_web3


@dataclass(frozen=True, slots=True)
class TimestampRange:
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("timestamp range end must be greater than start")


@dataclass(frozen=True, slots=True)
class BlockRange:
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError("block range end must be greater than or equal to start")

    @property
    def count(self) -> int:
        return self.end - self.start


@dataclass(frozen=True, slots=True)
class BlockPullPlan:
    window: TimestampRange
    block_range: BlockRange
    expected_rows: int
    expected_files: int


@dataclass(slots=True)
class Web3BlockClient:
    provider: ProviderConfig
    chain: ChainConfig
    _web3: Web3 = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._web3 = build_web3(self.provider, self.chain)

    def get_block(self, block_number: int) -> dict[str, Any]:
        return cast(dict[str, Any], dict(self._web3.eth.get_block(block_number, False)))

    def get_latest_block_number(self) -> int:
        return int(self._web3.eth.block_number)

    def find_first_block_at_or_after(self, timestamp: int) -> int:
        if timestamp < 0:
            raise ValueError("timestamp must be non-negative")

        latest_block_number = self.get_latest_block_number()
        latest_block = self.get_block(latest_block_number)
        latest_timestamp = self._as_int(latest_block["timestamp"])
        if timestamp > latest_timestamp:
            return latest_block_number + 1

        low = 0
        high = latest_block_number
        while low < high:
            middle = (low + high) // 2
            middle_timestamp = self._as_int(self.get_block(middle)["timestamp"])
            if middle_timestamp >= timestamp:
                high = middle
            else:
                low = middle + 1
        return low

    def resolve_block_range(self, window: TimestampRange) -> BlockRange:
        return BlockRange(
            start=self.find_first_block_at_or_after(window.start),
            end=self.find_first_block_at_or_after(window.end),
        )

    def plan_window(self, window: TimestampRange, *, chunk_size: int) -> BlockPullPlan:
        block_range = self.resolve_block_range(window)
        expected_rows = block_range.count
        expected_files = 0 if expected_rows == 0 else ceil(expected_rows / chunk_size)
        return BlockPullPlan(
            window=window,
            block_range=block_range,
            expected_rows=expected_rows,
            expected_files=expected_files,
        )

    def get_block_rows(self, block_numbers: list[int]) -> list[dict[str, int]]:
        if not block_numbers:
            return []

        with self._web3.batch_requests() as batch:
            for block_number in block_numbers:
                batch.add(self._web3.eth.get_block(block_number, False))
            blocks = cast(list[dict[str, Any]], batch.execute())

        if len(blocks) != len(block_numbers):
            raise RuntimeError(
                f"Expected {len(block_numbers)} block responses, got {len(blocks)}"
            )

        return [self._canonical_block_row(block) for block in blocks]

    def pull_timestamp_window(
        self,
        output_dir: Path,
        *,
        window: TimestampRange,
        chunk_size: int,
        rpc_batch_size: int,
        reporter: Reporter | None = None,
    ) -> BlockPullPlan:
        reporter = reporter or NullReporter()
        plan = self.plan_window(window, chunk_size=chunk_size)
        if plan.expected_rows == 0:
            raise ValueError(f"No blocks found inside requested timestamp window: {window}")

        task_id = reporter.start_task("pull blocks", total=plan.expected_rows, unit="blocks")
        pending_rows: list[dict[str, int]] = []
        completed = 0

        for batch_start in range(plan.block_range.start, plan.block_range.end, rpc_batch_size):
            batch_end = min(batch_start + rpc_batch_size, plan.block_range.end)
            pending_rows.extend(self.get_block_rows(list(range(batch_start, batch_end))))
            while len(pending_rows) >= chunk_size:
                self._write_chunk(output_dir, pending_rows[:chunk_size])
                pending_rows = pending_rows[chunk_size:]
            completed += batch_end - batch_start
            reporter.update_task(task_id, completed=completed)

        if pending_rows:
            self._write_chunk(output_dir, pending_rows)

        reporter.finish_task(task_id, message=str(output_dir))
        return plan

    def _canonical_block_row(self, block: dict[str, Any]) -> dict[str, int]:
        base_fee = block.get("baseFeePerGas")
        return {
            "block_number": self._as_int(block["number"]),
            "timestamp": self._as_int(block["timestamp"]),
            "base_fee_per_gas": 0 if base_fee is None else self._as_int(base_fee),
            "gas_used": self._as_int(block["gasUsed"]),
            "chain_id": self.chain.chain_id,
            "gas_limit": self._as_int(block["gasLimit"]),
        }

    @staticmethod
    def _as_int(value: object) -> int:
        return int(cast(Any, value))

    def _write_chunk(self, output_dir: Path, rows: list[dict[str, int]]) -> Path:
        frame = canonicalize_block_frame(pl.DataFrame(rows))
        start_block = int(frame["block_number"][0])
        end_block = int(frame["block_number"][-1])
        destination = (
            output_dir
            / f"{self.chain.name.value}__blocks__{start_block}_to_{end_block}.parquet"
        )
        write_block_file(destination, frame)
        return destination


def history_range_for_required_blocks(
    chain: ChainConfig,
    acquisition: AcquisitionConfig,
    *,
    required_history_blocks: int,
    window_start_timestamp: int,
) -> TimestampRange:
    if required_history_blocks <= 0:
        raise ValueError("required_history_blocks must be positive")

    block_count = required_history_blocks + acquisition.chunk_size
    span_seconds = ceil(block_count * chain.block_time_seconds)
    return TimestampRange(
        start=window_start_timestamp - span_seconds,
        end=window_start_timestamp,
    )


def evaluation_range(start_timestamp: int, end_timestamp: int) -> TimestampRange:
    return TimestampRange(start=start_timestamp, end=end_timestamp)
