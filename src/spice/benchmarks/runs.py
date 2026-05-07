# pyright: strict

"""Benchmark run-state files."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from ..core.validation import validate_path_segment
from ._run_state_codec import (
    BenchmarkRunMetadata,
    BenchmarkSubmissionRecord,
    collection_snapshot_path,
    load_collection_snapshot,
    load_plan_jsonl,
    load_run_metadata,
    load_submission_jsonl,
    write_collection_snapshot,
    write_plan_jsonl,
    write_run_metadata,
)
from .plan_materialization import BenchmarkPlanEntry

if TYPE_CHECKING:
    from .result_records import BenchmarkCollectionSnapshot

BENCHMARK_RUNS_ROOT = Path("outputs") / "benchmarks" / "runs"

__all__ = [
    "BENCHMARK_RUNS_ROOT",
    "BenchmarkRun",
    "BenchmarkRunMetadata",
    "BenchmarkSubmissionRecord",
    "create_benchmark_run",
    "format_datetime",
    "has_benchmark_collection_snapshot",
    "load_benchmark_collection_snapshot",
    "load_benchmark_collection_snapshots",
    "load_benchmark_run",
    "record_benchmark_submission",
    "timestamp_for_path",
    "utc_now",
    "write_benchmark_collection_snapshot",
]


class BenchmarkRun(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    run_dir: Path
    metadata: BenchmarkRunMetadata
    plan: tuple[BenchmarkPlanEntry, ...]
    submissions: dict[str, BenchmarkSubmissionRecord]
    has_collection: bool


def create_benchmark_run(
    name: str,
    *,
    target: str,
    runs_root: Path = BENCHMARK_RUNS_ROOT,
    plan: Sequence[BenchmarkPlanEntry],
) -> BenchmarkRun:
    safe_name = validate_path_segment(name, label="benchmark name")
    created_at = utc_now()
    base_dir = runs_root / safe_name / timestamp_for_path(created_at)
    run_dir = base_dir
    suffix = 1
    while run_dir.exists():
        suffix += 1
        run_dir = base_dir.with_name(f"{base_dir.name}-{suffix}")
    run_dir.mkdir(parents=True)
    metadata = BenchmarkRunMetadata(
        benchmark=safe_name,
        created_at_utc=format_datetime(created_at),
        target=target,
    )
    write_run_metadata(run_dir, metadata)
    write_plan_jsonl(run_dir, list(plan))
    return load_benchmark_run(run_dir)


def load_benchmark_run(run_dir: Path) -> BenchmarkRun:
    return BenchmarkRun(
        run_dir=run_dir,
        metadata=load_run_metadata(run_dir),
        plan=tuple(load_plan_jsonl(run_dir)),
        submissions=load_submission_jsonl(run_dir),
        has_collection=collection_snapshot_path(run_dir).is_file(),
    )


def record_benchmark_submission(
    run_dir: Path,
    record: BenchmarkSubmissionRecord,
) -> BenchmarkRun:
    from ._run_state_codec import append_submission_jsonl

    append_submission_jsonl(run_dir, record)
    return load_benchmark_run(run_dir)


def write_benchmark_collection_snapshot(
    run_dir: Path,
    snapshot: BenchmarkCollectionSnapshot,
) -> BenchmarkRun:
    write_collection_snapshot(run_dir, snapshot)
    return load_benchmark_run(run_dir)


def load_benchmark_collection_snapshot(run_dir: Path) -> BenchmarkCollectionSnapshot:
    return load_collection_snapshot(run_dir)


def has_benchmark_collection_snapshot(run_dir: Path) -> bool:
    return collection_snapshot_path(run_dir).is_file()


def load_benchmark_collection_snapshots(
    *,
    runs_root: Path = BENCHMARK_RUNS_ROOT,
) -> list[BenchmarkCollectionSnapshot]:
    return [
        load_benchmark_collection_snapshot(run_dir)
        for run_dir in _benchmark_run_dirs(runs_root)
        if has_benchmark_collection_snapshot(run_dir)
    ]


def _benchmark_run_dirs(runs_root: Path) -> list[Path]:
    if not runs_root.exists():
        return []
    return sorted(
        candidate
        for benchmark_dir in runs_root.iterdir()
        if benchmark_dir.is_dir()
        for candidate in benchmark_dir.iterdir()
        if candidate.is_dir()
    )


def utc_now() -> datetime:
    return datetime.now(UTC)


def timestamp_for_path(value: datetime) -> str:
    return value.strftime("%Y%m%dT%H%M%SZ")


def format_datetime(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
