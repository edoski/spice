from __future__ import annotations

import math
from datetime import date
from pathlib import Path
from typing import cast

import polars as pl
import pytest

from spice.config import AcquireConfig, WorkflowTask

PRESET = "icdcs_2026"
TEST_EVALUATION_DATE = date(2025, 11, 9)


@pytest.fixture
def acquire_override():
    def _override(
        *,
        sample_count: int = 4,
        lookback_seconds: int = 24,
        max_delay_seconds: int = 12,
    ) -> dict[str, object]:
        return {
            "chain": "ethereum",
            "dataset": {
                "evaluation_date": TEST_EVALUATION_DATE.isoformat(),
            },
            "problem": {
                "id": "acquire_test_problem",
                "lookback_seconds": lookback_seconds,
                "sample_count": sample_count,
                "max_delay_seconds": max_delay_seconds,
                "compiler": {"id": "timestamp_native"},
            },
            "acquisition": {
                "chunk_size": 64,
                "rpc": {
                    "batch_size": 16,
                    "concurrency": 8,
                    "min_batch_size": 8,
                    "concurrency_rungs": [8],
                },
            },
        }

    return _override


@pytest.fixture
def load_test_acquire_config(tmp_path: Path, load_workflow_config):
    def _load(
        tmp_path_arg: Path | None = None,
        *,
        override: dict[str, object] | None = None,
        chain: str | None = None,
        provider: str | None = None,
    ) -> AcquireConfig:
        workspace = tmp_path if tmp_path_arg is None else tmp_path_arg
        return cast(
            AcquireConfig,
            load_workflow_config(
                WorkflowTask.ACQUIRE,
                workspace=workspace,
                preset=PRESET,
                override=override,
                chain=chain,
                provider=provider,
            ),
        )

    return _load


@pytest.fixture
def make_block_rows():
    def _make_block_rows(
        count: int,
        *,
        start_block: int,
        start_timestamp: int,
        chain_id: int = 1,
        block_interval_seconds: int = 12,
    ) -> list[dict[str, int]]:
        rows: list[dict[str, int]] = []
        for offset in range(count):
            block_number = start_block + offset
            timestamp = start_timestamp + offset * block_interval_seconds
            base_fee = int(
                1_000_000_000
                + 150_000_000 * math.sin(block_number / 2.0)
                + 150_000_000 * math.cos(block_number / 2.5)
                + 50_000_000 * math.sin(block_number / 7.0)
            )
            rows.append(
                {
                    "block_number": block_number,
                    "timestamp": timestamp,
                    "base_fee_per_gas": max(base_fee, 1),
                    "gas_used": int(18_000_000 + 2_000_000 * math.sin(block_number / 5.0)),
                    "gas_limit": 30_000_000,
                    "chain_id": chain_id,
                }
            )
        return rows

    return _make_block_rows


@pytest.fixture
def write_dataset_dir():
    def _write_dataset_dir(dataset_dir: Path, rows: list[dict[str, int]]) -> Path:
        dataset_dir.mkdir(parents=True, exist_ok=True)
        path = dataset_dir / "blocks.parquet"
        pl.DataFrame(rows).write_parquet(path)
        return path

    return _write_dataset_dir
