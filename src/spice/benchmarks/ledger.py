# pyright: strict

"""Benchmark result ledger projection."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

from ..core.errors import SpiceOperatorError
from ..modeling.results import LoadedEvaluationSummary, LoadedTrainingSummary
from .runs import BenchmarkSubmissionRecord, LoadedBenchmarkPlanEntry, format_datetime

BENCHMARK_LEDGER_PATH = Path("benchmarks") / "results.csv"

LEDGER_COLUMNS = (
    "recorded_at_utc",
    "git_commit",
    "execution_ref",
    "artifact_id",
    "evaluation_storage_id",
    "chain",
    "dataset",
    "surface",
    "features",
    "model",
    "problem",
    "prediction",
    "objective",
    "evaluation",
    "delay_seconds",
    "variant",
    "study",
    "sample_count",
    "total_events",
    "profit_over_baseline",
    "cost_over_optimum",
    "baseline_cost_over_optimum",
    "total_loss",
    "offset_accuracy",
    "macro_f1",
    "classification_loss",
    "regression_loss",
    "log_fee_mae",
    "log_fee_mse",
    "exact_optimum_hit_rate",
    "notes",
)


def benchmark_ledger_row(
    *,
    entry: LoadedBenchmarkPlanEntry,
    evaluation: LoadedEvaluationSummary,
    training: LoadedTrainingSummary | None,
    submission: BenchmarkSubmissionRecord,
    collector_time: datetime,
) -> dict[str, str]:
    summary = evaluation
    manifest = summary.manifest
    runtime = summary.runtime
    metrics: dict[str, float] = (
        {} if training is None else dict(training.runtime.test_metrics.values)
    )
    metrics.update(runtime.metrics.values)
    recorded_at = (
        format_datetime(datetime.fromtimestamp(summary.recorded_at, UTC))
        if summary.recorded_at > 0
        else format_datetime(collector_time)
    )
    row = {
        "recorded_at_utc": recorded_at,
        "git_commit": submission.git_commit,
        "execution_ref": submission.execution_ref,
        "artifact_id": manifest.artifact_id,
        "evaluation_storage_id": summary.evaluation_id,
        "chain": manifest.chain_name,
        "dataset": manifest.dataset_name,
        "surface": str(entry.selection.get("surface", "")),
        "features": manifest.features_id,
        "model": manifest.model.id,
        "problem": manifest.problem_id,
        "prediction": manifest.prediction_id,
        "objective": str(entry.selection.get("objective", manifest.objective.id)),
        "evaluation": runtime.evaluation_id,
        "delay_seconds": str(runtime.delay_seconds),
        "variant": manifest.variant.value,
        "study": "" if manifest.study is None else manifest.study.name,
        "sample_count": str(runtime.sample_count),
        "total_events": str(runtime.total_events),
        "notes": "",
    }
    for column in LEDGER_COLUMNS:
        if column in row:
            continue
        row[column] = _metric_cell(metrics.get(column))
    return {column: row[column] for column in LEDGER_COLUMNS}


def append_ledger_rows(ledger_path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    ensure_ledger_header(ledger_path)
    with ledger_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(LEDGER_COLUMNS), lineterminator="\n")
        for row in rows:
            writer.writerow({column: row[column] for column in LEDGER_COLUMNS})


def read_ledger_keys(ledger_path: Path) -> set[tuple[str, str]]:
    if not ledger_path.exists():
        return set()
    ensure_ledger_header(ledger_path)
    with ledger_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return {ledger_key(row) for row in reader}


def ensure_ledger_header(ledger_path: Path) -> None:
    if not ledger_path.exists():
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with ledger_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(LEDGER_COLUMNS)
        return
    with ledger_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
    if tuple(header or ()) != LEDGER_COLUMNS:
        raise SpiceOperatorError(f"Benchmark ledger header mismatch: {ledger_path}")


def ledger_key(row: dict[str, str]) -> tuple[str, str]:
    return row["artifact_id"], row["evaluation_storage_id"]


def _metric_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return repr(value)
    return str(value)
