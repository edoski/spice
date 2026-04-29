# pyright: strict

"""Benchmark collection from remote completed workflows."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ..config.models import EvaluateConfig, WorkflowTask
from ..core.errors import ConfigResolutionError, SelectorResolutionError, SpiceOperatorError
from ..execution.session import open_execution_session
from .collection_resolver import resolve_benchmark_evaluation
from .ledger import (
    BENCHMARK_LEDGER_PATH,
    append_ledger_rows,
    benchmark_ledger_row,
    ledger_key,
    read_ledger_keys,
)
from .runs import (
    BenchmarkCollectionRecord,
    load_plan_jsonl,
    load_submission_jsonl,
    utc_now,
    write_collection_jsonl,
)


def collect_benchmark_run(
    *,
    run_dir: Path,
    target_name: str,
    ledger_path: Path = BENCHMARK_LEDGER_PATH,
    write: bool = False,
) -> list[BenchmarkCollectionRecord]:
    plan = load_plan_jsonl(run_dir)
    submissions = load_submission_jsonl(run_dir)
    existing_keys = read_ledger_keys(ledger_path)
    records: list[BenchmarkCollectionRecord] = []
    collector_time = utc_now()
    session = open_execution_session(target_name)
    for entry in plan:
        if entry.workflow is not WorkflowTask.EVALUATE:
            continue
        if not isinstance(entry.config, EvaluateConfig):
            raise ConfigResolutionError(f"benchmark run {entry.run_id} is not an evaluate config")
        submission = submissions.get(entry.run_id)
        if submission is None:
            records.append(
                BenchmarkCollectionRecord(
                    run_id=entry.run_id,
                    workflow=entry.workflow,
                    status="missing",
                    reason="missing submission record",
                )
            )
            continue
        try:
            state = resolve_benchmark_evaluation(
                entry.config,
                session=session,
            )
        except SelectorResolutionError as exc:
            records.append(
                BenchmarkCollectionRecord(
                    run_id=entry.run_id,
                    workflow=entry.workflow,
                    status="missing",
                    reason=str(exc),
                )
            )
            continue
        if state is None:
            records.append(
                BenchmarkCollectionRecord(
                    run_id=entry.run_id,
                    workflow=entry.workflow,
                    status="missing",
                    reason="evaluation summary not found",
                )
            )
            continue
        row = benchmark_ledger_row(
            entry=entry,
            evaluation=state.evaluation,
            training=state.training,
            submission=submission,
            collector_time=collector_time,
        )
        key = ledger_key(row)
        if key in existing_keys:
            records.append(
                BenchmarkCollectionRecord(
                    run_id=entry.run_id,
                    workflow=entry.workflow,
                    status="skipped",
                    reason="ledger row already exists",
                    row=row,
                )
            )
            continue
        existing_keys.add(key)
        records.append(
            BenchmarkCollectionRecord(
                run_id=entry.run_id,
                workflow=entry.workflow,
                status="ready",
                row=row,
            )
        )
    write_collection_jsonl(run_dir, records)
    if write:
        missing = [record for record in records if record.status == "missing"]
        if missing:
            raise SpiceOperatorError(
                f"Refusing partial benchmark ledger write: {len(missing)} evaluation rows missing"
            )
        append_ledger_rows(
            ledger_path,
            [cast(dict[str, str], record.row) for record in records if record.status == "ready"],
        )
    return records
