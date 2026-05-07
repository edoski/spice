# pyright: strict

"""Durable benchmark plan creation and remote submission."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..core.errors import SpiceOperatorError
from ..execution.session import ExecutionSession, open_execution_session
from .plan_materialization import BenchmarkPlanEntry, materialize_benchmark_plan
from .runs import (
    BenchmarkSubmissionRecord,
    create_benchmark_run,
    load_benchmark_run,
    record_benchmark_submission,
)


@dataclass(frozen=True, slots=True)
class PlannedBenchmarkRun:
    run_dir: Path
    entry_count: int


@dataclass(frozen=True, slots=True)
class SubmittedBenchmarkWorkflow:
    record: BenchmarkSubmissionRecord
    run_dir: Path


def materialize_benchmark_plan_run(
    name: str,
    *,
    target: str,
    runs_root: Path,
) -> PlannedBenchmarkRun:
    entries = materialize_benchmark_plan(name)
    run = create_benchmark_run(name, target=target, runs_root=runs_root, plan=entries)
    return PlannedBenchmarkRun(run_dir=run.run_dir, entry_count=len(run.plan))


def submit_benchmark_run(run_dir: Path) -> list[SubmittedBenchmarkWorkflow]:
    run = load_benchmark_run(run_dir)
    if run.submissions:
        raise SpiceOperatorError(f"Benchmark run already has submissions: {run_dir}")
    session = open_execution_session(run.metadata.target)
    git_commit = session.remote_git_commit()
    return _submit_benchmark_entries(
        list(run.plan),
        run_dir=run_dir,
        session=session,
        git_commit=git_commit,
    )


def _submit_benchmark_entries(
    entries: list[BenchmarkPlanEntry],
    *,
    run_dir: Path,
    session: ExecutionSession,
    git_commit: str,
) -> list[SubmittedBenchmarkWorkflow]:
    submitted: dict[str, str] = {}
    records: list[SubmittedBenchmarkWorkflow] = []
    for entry in entries:
        dependency = compose_dependency(
            local_job_ids=[submitted[run_id] for run_id in entry.dependencies.local_run_ids],
            external_dependencies=entry.dependencies.external_slurm_dependencies,
        )
        submission = session.submit_workflow(
            entry.workflow,
            config=entry.config,
            dependency=dependency,
        )
        provenance = submission.provenance
        submitted[entry.run_id] = provenance.job_id
        record = BenchmarkSubmissionRecord(
            run_id=entry.run_id,
            workflow=entry.workflow,
            job_id=provenance.job_id,
            execution_ref=provenance.execution_ref,
            git_commit=git_commit,
            dependency=dependency,
            log_path=str(provenance.log_path),
        )
        record_benchmark_submission(run_dir, record)
        records.append(SubmittedBenchmarkWorkflow(record=record, run_dir=run_dir))
    return records


def compose_dependency(
    *,
    local_job_ids: list[str],
    external_dependencies: tuple[str, ...],
) -> str | None:
    parts = list(external_dependencies)
    if local_job_ids:
        parts.append("afterok:" + ":".join(local_job_ids))
    if not parts:
        return None
    return ",".join(parts)
