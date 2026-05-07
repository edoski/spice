# pyright: strict

"""Benchmark Result Index rebuild, update, and read operations."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from ..core.files import remove_path
from .result_records import BenchmarkCollectionSnapshot
from .result_store import (
    BENCHMARK_RESULT_INDEX_PATH,
    BenchmarkResultIndexRow,
    ensure_result_index,
    index_counts,
    list_indexed_results,
    upsert_collection_snapshot,
)
from .runs import BENCHMARK_RUNS_ROOT, load_benchmark_collection_snapshots


def upsert_benchmark_collection_snapshot(
    snapshot: BenchmarkCollectionSnapshot,
    *,
    index_path: Path = BENCHMARK_RESULT_INDEX_PATH,
) -> None:
    upsert_collection_snapshot(index_path, snapshot)


def rebuild_benchmark_result_index(
    *,
    runs_root: Path = BENCHMARK_RUNS_ROOT,
    index_path: Path = BENCHMARK_RESULT_INDEX_PATH,
) -> dict[str, int]:
    temp_path = index_path.parent / f".{index_path.name}.rebuild.{uuid4().hex}.tmp"
    remove_path(temp_path)
    try:
        ensure_result_index(temp_path)
        for snapshot in load_benchmark_collection_snapshots(runs_root=runs_root):
            upsert_collection_snapshot(temp_path, snapshot)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(temp_path, index_path)
        return index_counts(index_path)
    except Exception:
        remove_path(temp_path)
        raise


def benchmark_result_index_counts(
    *,
    index_path: Path = BENCHMARK_RESULT_INDEX_PATH,
) -> dict[str, int]:
    return index_counts(index_path)


def list_benchmark_results(
    *,
    index_path: Path = BENCHMARK_RESULT_INDEX_PATH,
    benchmark: str | None = None,
    chain: str | None = None,
    model: str | None = None,
    evaluation: str | None = None,
    limit: int | None = None,
) -> list[BenchmarkResultIndexRow]:
    return list_indexed_results(
        index_path,
        benchmark=benchmark,
        chain=chain,
        model=model,
        evaluation=evaluation,
        limit=limit,
    )
