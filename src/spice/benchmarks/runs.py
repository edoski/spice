# pyright: strict

"""Benchmark run-state files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict

from ..config.hydration import hydrate_resolved_workflow_config
from ..config.models import WorkflowTask
from ..config.resolution import WorkflowConfig
from ..core.errors import SpiceOperatorError
from ..core.validation import validate_path_segment
from .compilation import BenchmarkPlanEntry

BENCHMARK_RUNS_ROOT = Path("outputs") / "benchmarks" / "runs"
PLAN_FILENAME = "plan.jsonl"
SUBMISSION_FILENAME = "submission.jsonl"
METADATA_FILENAME = "metadata.json"


class BenchmarkRunMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    benchmark: str
    created_at_utc: str
    target: str
    git_commit: str


class BenchmarkSubmissionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    workflow: WorkflowTask
    job_id: str
    execution_ref: str
    git_commit: str
    dependency: str | None
    log_path: str


class BenchmarkCollectionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    workflow: WorkflowTask
    status: Literal["ready", "skipped", "missing"]
    row: dict[str, str] | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class LoadedBenchmarkPlanEntry:
    run_id: str
    case_id: str
    step_id: str
    workflow: WorkflowTask
    depends_on: tuple[str, ...]
    external_dependencies: tuple[str, ...]
    selection: dict[str, object]
    config: WorkflowConfig


def create_benchmark_run_dir(
    name: str,
    *,
    target: str,
    git_commit: str,
    runs_root: Path = BENCHMARK_RUNS_ROOT,
) -> Path:
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
        git_commit=git_commit,
    )
    write_json(run_dir / METADATA_FILENAME, metadata.model_dump(mode="json"))
    (run_dir / "collections").mkdir()
    return run_dir


def latest_benchmark_run_dir(
    name: str,
    *,
    runs_root: Path = BENCHMARK_RUNS_ROOT,
) -> Path:
    safe_name = validate_path_segment(name, label="benchmark name")
    root = runs_root / safe_name
    if not root.is_dir():
        raise SpiceOperatorError(f"No benchmark run directory found for {safe_name}")
    candidates = sorted(path for path in root.iterdir() if path.is_dir())
    if not candidates:
        raise SpiceOperatorError(f"No benchmark run directory found for {safe_name}")
    return candidates[-1]


def write_plan_jsonl(run_dir: Path, entries: list[BenchmarkPlanEntry]) -> None:
    write_jsonl(run_dir / PLAN_FILENAME, [entry.to_json_dict() for entry in entries])


def append_submission_jsonl(run_dir: Path, record: BenchmarkSubmissionRecord) -> None:
    append_jsonl(run_dir / SUBMISSION_FILENAME, record.model_dump(mode="json"))


def load_plan_jsonl(run_dir: Path) -> list[LoadedBenchmarkPlanEntry]:
    entries: list[LoadedBenchmarkPlanEntry] = []
    for payload in read_jsonl(run_dir / PLAN_FILENAME):
        workflow = WorkflowTask(str(payload["workflow"]))
        config_payload = mapping_payload(payload["config"], label="config")
        entries.append(
            LoadedBenchmarkPlanEntry(
                run_id=str(payload["run_id"]),
                case_id=str(payload["case_id"]),
                step_id=str(payload["step_id"]),
                workflow=workflow,
                depends_on=tuple(
                    str(value) for value in sequence_payload(payload.get("depends_on", []))
                ),
                external_dependencies=tuple(
                    str(value)
                    for value in sequence_payload(payload.get("external_dependencies", []))
                ),
                selection=dict(mapping_payload(payload.get("selection", {}), label="selection")),
                config=hydrate_resolved_workflow_config(workflow, config_payload),
            )
        )
    return entries


def load_submission_jsonl(run_dir: Path) -> dict[str, BenchmarkSubmissionRecord]:
    records: dict[str, BenchmarkSubmissionRecord] = {}
    for payload in read_jsonl(run_dir / SUBMISSION_FILENAME):
        record = BenchmarkSubmissionRecord.model_validate(payload)
        records[record.run_id] = record
    return records


def write_collection_jsonl(
    run_dir: Path,
    records: list[BenchmarkCollectionRecord],
) -> None:
    collection_dir = run_dir / "collections"
    collection_dir.mkdir(exist_ok=True)
    path = collection_dir / f"{timestamp_for_path(utc_now())}.jsonl"
    write_jsonl(path, [record.model_dump(mode="json") for record in records])


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def append_jsonl(path: Path, row: dict[str, object]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        raise SpiceOperatorError(f"Missing benchmark run file: {path}")
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise SpiceOperatorError(f"Invalid JSONL object in {path}")
        rows.append(cast(dict[str, object], payload))
    return rows


def mapping_payload(value: object, *, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise SpiceOperatorError(f"benchmark {label} must be an object")
    return cast(dict[str, object], value)


def sequence_payload(value: object) -> list[object]:
    if not isinstance(value, list):
        raise SpiceOperatorError("benchmark JSONL field must be a list")
    return cast(list[object], value)


def utc_now() -> datetime:
    return datetime.now(UTC)


def timestamp_for_path(value: datetime) -> str:
    return value.strftime("%Y%m%dT%H%M%SZ")


def format_datetime(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
