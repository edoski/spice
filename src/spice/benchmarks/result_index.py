# pyright: strict

"""Benchmark Result Index rebuild, update, query, and export operations."""

from __future__ import annotations

import csv
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from sqlalchemy import ColumnElement, and_, delete, func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from ..core.errors import SpiceOperatorError
from ..core.files import remove_path
from ..storage.engine import create_sqlite_engine, ensure_table_shapes
from ._result_schema import (
    benchmark_runs,
    metadata,
    metric_values,
    result_observations,
)
from .result_records import BenchmarkCollectionSnapshot, BenchmarkResultRecord
from .runs import BENCHMARK_RUNS_ROOT, load_benchmark_collection_snapshots

BENCHMARK_RESULT_INDEX_PATH = Path("benchmarks") / "results.sqlite"
BENCHMARK_RESULT_EXPORT_COLUMNS = (
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

__all__ = [
    "BENCHMARK_RESULT_EXPORT_COLUMNS",
    "BENCHMARK_RESULT_INDEX_PATH",
    "BenchmarkResultIndexRow",
    "benchmark_result_index_counts",
    "export_benchmark_results_csv",
    "list_benchmark_results",
    "rebuild_benchmark_result_index",
    "upsert_benchmark_collection_snapshot",
]


def _empty_metrics() -> dict[str, float]:
    return {}


@dataclass(frozen=True, slots=True)
class BenchmarkResultIndexRow:
    run_id: str
    artifact_id: str
    evaluation_storage_id: str
    git_commit: str
    execution_ref: str
    chain_name: str
    artifact_dataset_id: str
    evaluation_dataset_id: str
    artifact_dataset_name: str
    surface: str
    features_id: str
    model_id: str
    problem_id: str
    prediction_id: str
    objective_id: str
    evaluator_id: str
    delay_seconds: int
    variant: str
    study_name: str | None
    sample_count: int
    total_events: int
    recorded_at_utc: str
    metrics: dict[str, float] = field(default_factory=_empty_metrics)


def upsert_benchmark_collection_snapshot(
    snapshot: BenchmarkCollectionSnapshot,
    *,
    index_path: Path = BENCHMARK_RESULT_INDEX_PATH,
) -> None:
    _upsert_collection_snapshot(index_path, snapshot)


def rebuild_benchmark_result_index(
    *,
    runs_root: Path = BENCHMARK_RUNS_ROOT,
    index_path: Path = BENCHMARK_RESULT_INDEX_PATH,
) -> dict[str, int]:
    temp_path = index_path.parent / f".{index_path.name}.rebuild.{uuid4().hex}.tmp"
    remove_path(temp_path)
    try:
        _ensure_result_index(temp_path)
        for snapshot in load_benchmark_collection_snapshots(runs_root=runs_root):
            _upsert_collection_snapshot(temp_path, snapshot)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(temp_path, index_path)
        return _index_counts(index_path)
    except Exception:
        remove_path(temp_path)
        raise


def benchmark_result_index_counts(
    *,
    index_path: Path = BENCHMARK_RESULT_INDEX_PATH,
) -> dict[str, int]:
    return _index_counts(index_path)


def list_benchmark_results(
    *,
    index_path: Path = BENCHMARK_RESULT_INDEX_PATH,
    benchmark: str | None = None,
    chain: str | None = None,
    model: str | None = None,
    evaluation: str | None = None,
    limit: int | None = None,
) -> list[BenchmarkResultIndexRow]:
    return _list_indexed_results(
        index_path,
        benchmark=benchmark,
        chain=chain,
        model=model,
        evaluation=evaluation,
        limit=limit,
    )


def export_benchmark_results_csv(
    *,
    output_path: Path,
    index_path: Path = BENCHMARK_RESULT_INDEX_PATH,
    benchmark: str | None = None,
    chain: str | None = None,
    model: str | None = None,
    evaluation: str | None = None,
) -> list[dict[str, str]]:
    rows = [
        _result_record_csv_row(row)
        for row in list_benchmark_results(
            index_path=index_path,
            benchmark=benchmark,
            chain=chain,
            model=model,
            evaluation=evaluation,
        )
    ]
    _write_results_csv(output_path, rows)
    return rows


def _ensure_result_index(path: Path) -> None:
    engine = create_sqlite_engine(path, create_dirs=True)
    try:
        metadata.create_all(engine)
        with engine.begin() as conn:
            ensure_table_shapes(
                conn,
                tables=(
                    benchmark_runs,
                    result_observations,
                    metric_values,
                ),
            )
    finally:
        engine.dispose()


def _upsert_collection_snapshot(path: Path, snapshot: BenchmarkCollectionSnapshot) -> None:
    _ensure_result_index(path)
    now = int(time.time())
    engine = create_sqlite_engine(path)
    try:
        with engine.begin() as conn:
            conn.execute(
                sqlite_insert(benchmark_runs)
                .values(
                    run_dir=snapshot.run_dir,
                    benchmark=snapshot.benchmark,
                    target=snapshot.target,
                    created_at_utc=snapshot.run_created_at_utc,
                    updated_at=now,
                )
                .on_conflict_do_update(
                    index_elements=[benchmark_runs.c.run_dir],
                    set_={
                        "benchmark": snapshot.benchmark,
                        "target": snapshot.target,
                        "created_at_utc": snapshot.run_created_at_utc,
                        "updated_at": now,
                    },
                )
            )
            stale_observation_ids = [
                str(row["observation_id"])
                for row in conn.execute(
                    select(result_observations.c.observation_id).where(
                        result_observations.c.run_dir == snapshot.run_dir
                    )
                ).mappings()
            ]
            if stale_observation_ids:
                conn.execute(
                    delete(metric_values).where(
                        metric_values.c.observation_id.in_(stale_observation_ids)
                    )
                )
            conn.execute(
                delete(result_observations).where(
                    result_observations.c.run_dir == snapshot.run_dir
                )
            )
            for record in snapshot.records:
                observation_id = _observation_key(snapshot.run_dir, record)
                conn.execute(
                    sqlite_insert(result_observations).values(
                        observation_id=observation_id,
                        run_dir=snapshot.run_dir,
                        benchmark=snapshot.benchmark,
                        run_id=record.run_id,
                        case_id=record.case_id,
                        step_id=record.step_id,
                        git_commit=record.git_commit,
                        execution_ref=record.execution_ref,
                        artifact_id=record.artifact_id,
                        evaluation_storage_id=record.evaluation_storage_id,
                        artifact_dataset_id=record.artifact_dataset_id,
                        evaluation_dataset_id=record.evaluation_dataset_id,
                        chain_name=record.chain_name,
                        artifact_dataset_name=record.artifact_dataset_name,
                        surface=record.selection.surface or "",
                        features_id=record.features_id,
                        model_id=record.model_id,
                        problem_id=record.problem_id,
                        prediction_id=record.prediction_id,
                        objective_id=record.objective_id,
                        evaluator_id=record.evaluator_id,
                        delay_seconds=record.delay_seconds,
                        variant=record.variant,
                        study_name=record.study_name,
                        sample_count=record.sample_count,
                        total_events=record.total_events,
                        recorded_at_utc=record.recorded_at_utc,
                        updated_at=now,
                    )
                )
                conn.execute(
                    delete(metric_values).where(metric_values.c.observation_id == observation_id)
                )
                if record.metrics:
                    conn.execute(
                        metric_values.insert(),
                        [
                            {
                                "observation_id": observation_id,
                                "source": metric.source,
                                "metric_id": metric.metric_id,
                                "value": metric.value,
                            }
                            for metric in record.metrics
                        ],
                    )
    finally:
        engine.dispose()


def _observation_key(run_dir: str, record: BenchmarkResultRecord) -> str:
    return f"{run_dir}\0{record.run_id}\0{record.evaluation_storage_id}"


def _index_counts(path: Path) -> dict[str, int]:
    _ensure_result_index(path)
    engine = create_sqlite_engine(path)
    try:
        with engine.connect() as conn:
            run_count = conn.execute(select(func.count()).select_from(benchmark_runs)).scalar_one()
            observation_count = conn.execute(
                select(func.count()).select_from(result_observations)
            ).scalar_one()
            metric_count = conn.execute(
                select(func.count()).select_from(metric_values)
            ).scalar_one()
        return {
            "runs": int(run_count),
            "observations": int(observation_count),
            "metrics": int(metric_count),
        }
    finally:
        engine.dispose()


def _list_indexed_results(
    path: Path,
    *,
    benchmark: str | None = None,
    chain: str | None = None,
    model: str | None = None,
    evaluation: str | None = None,
    limit: int | None = None,
) -> list[BenchmarkResultIndexRow]:
    _ensure_result_index(path)
    filters: list[ColumnElement[bool]] = []
    if benchmark is not None:
        filters.append(result_observations.c.benchmark == benchmark)
    if chain is not None:
        filters.append(result_observations.c.chain_name == chain)
    if model is not None:
        filters.append(result_observations.c.model_id == model)
    if evaluation is not None:
        filters.append(result_observations.c.evaluator_id == evaluation)
    statement = select(
        result_observations.c.observation_id,
        result_observations.c.run_id,
        result_observations.c.artifact_id,
        result_observations.c.evaluation_storage_id,
        result_observations.c.git_commit,
        result_observations.c.execution_ref,
        result_observations.c.chain_name,
        result_observations.c.artifact_dataset_id,
        result_observations.c.evaluation_dataset_id,
        result_observations.c.artifact_dataset_name,
        result_observations.c.surface,
        result_observations.c.features_id,
        result_observations.c.model_id,
        result_observations.c.problem_id,
        result_observations.c.prediction_id,
        result_observations.c.objective_id,
        result_observations.c.evaluator_id,
        result_observations.c.delay_seconds,
        result_observations.c.variant,
        result_observations.c.study_name,
        result_observations.c.sample_count,
        result_observations.c.total_events,
        result_observations.c.recorded_at_utc,
    ).order_by(
        result_observations.c.recorded_at_utc.desc(),
        result_observations.c.observation_id,
    )
    if filters:
        statement = statement.where(and_(*filters))
    if limit is not None:
        statement = statement.limit(limit)
    engine = create_sqlite_engine(path)
    try:
        with engine.connect() as conn:
            rows = [dict(row) for row in conn.execute(statement).mappings()]
            observation_ids = [str(row["observation_id"]) for row in rows]
            metrics_by_observation: dict[str, dict[str, float]] = {
                observation_id: {} for observation_id in observation_ids
            }
            if observation_ids:
                metric_statement = select(
                    metric_values.c.observation_id,
                    metric_values.c.source,
                    metric_values.c.metric_id,
                    metric_values.c.value,
                ).where(metric_values.c.observation_id.in_(observation_ids))
                for metric in conn.execute(metric_statement).mappings():
                    if metric["source"] not in {"training_test", "evaluation"}:
                        continue
                    observation_id = str(metric["observation_id"])
                    metric_id = str(metric["metric_id"])
                    if metric_id in metrics_by_observation[observation_id]:
                        raise SpiceOperatorError(
                            "Benchmark result metric id collision across sources: "
                            f"{metric_id}"
                        )
                    metrics_by_observation[observation_id][metric_id] = float(
                        metric["value"]
                    )
            return [
                BenchmarkResultIndexRow(
                    run_id=str(row["run_id"]),
                    artifact_id=str(row["artifact_id"]),
                    evaluation_storage_id=str(row["evaluation_storage_id"]),
                    git_commit=str(row["git_commit"]),
                    execution_ref=str(row["execution_ref"]),
                    chain_name=str(row["chain_name"]),
                    artifact_dataset_id=str(row["artifact_dataset_id"]),
                    evaluation_dataset_id=str(row["evaluation_dataset_id"]),
                    artifact_dataset_name=str(row["artifact_dataset_name"]),
                    surface=str(row["surface"]),
                    features_id=str(row["features_id"]),
                    model_id=str(row["model_id"]),
                    problem_id=str(row["problem_id"]),
                    prediction_id=str(row["prediction_id"]),
                    objective_id=str(row["objective_id"]),
                    evaluator_id=str(row["evaluator_id"]),
                    delay_seconds=int(row["delay_seconds"]),
                    variant=str(row["variant"]),
                    study_name=None if row["study_name"] is None else str(row["study_name"]),
                    sample_count=int(row["sample_count"]),
                    total_events=int(row["total_events"]),
                    recorded_at_utc=str(row["recorded_at_utc"]),
                    metrics=metrics_by_observation[str(row["observation_id"])],
                )
                for row in rows
            ]
    finally:
        engine.dispose()


def _write_results_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(BENCHMARK_RESULT_EXPORT_COLUMNS),
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in BENCHMARK_RESULT_EXPORT_COLUMNS})


def _result_record_csv_row(record: BenchmarkResultIndexRow) -> dict[str, str]:
    row = {
        "recorded_at_utc": record.recorded_at_utc,
        "git_commit": record.git_commit,
        "execution_ref": record.execution_ref,
        "artifact_id": record.artifact_id,
        "evaluation_storage_id": record.evaluation_storage_id,
        "chain": record.chain_name,
        "dataset": record.artifact_dataset_name,
        "surface": record.surface,
        "features": record.features_id,
        "model": record.model_id,
        "problem": record.problem_id,
        "prediction": record.prediction_id,
        "objective": record.objective_id,
        "evaluation": record.evaluator_id,
        "delay_seconds": str(record.delay_seconds),
        "variant": record.variant,
        "study": record.study_name or "",
        "sample_count": str(record.sample_count),
        "total_events": str(record.total_events),
        "notes": "",
    }
    for column in BENCHMARK_RESULT_EXPORT_COLUMNS:
        if column in row:
            continue
        row[column] = _metric_cell(record.metrics.get(column))
    return {column: row[column] for column in BENCHMARK_RESULT_EXPORT_COLUMNS}


def _metric_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return repr(value)
    return str(value)
