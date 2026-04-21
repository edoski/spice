"""Dataset-root inspection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..corpus.metadata import AcquireRunRecord, DatasetManifest, DatasetWindowMetadata
from .catalog import CatalogDatasetRecord
from .corpus import list_acquire_runs, load_dataset_manifest


@dataclass(frozen=True, slots=True)
class DatasetRootDescription:
    manifest: DatasetManifest
    runs: list[AcquireRunRecord] | None = None


def dataset_list_sections(
    records: list[CatalogDatasetRecord],
) -> list[tuple[str, list[tuple[str, str]]]]:
    return [
        (
            "datasets",
            [
                (
                    record.dataset_name,
                    f"chain={record.chain_name} id={record.dataset_id}",
                )
                for record in records
            ],
        )
    ]


def describe_dataset_root(
    root_db_path: Path, *, detail: str | None = None
) -> DatasetRootDescription:
    return DatasetRootDescription(
        manifest=load_dataset_manifest(root_db_path),
        runs=list_acquire_runs(root_db_path) if detail == "runs" else None,
    )


def dataset_sections(
    description: DatasetRootDescription,
) -> list[tuple[str, list[tuple[str, str]]]]:
    manifest = description.manifest
    sections = [
        (
            "dataset",
            [
                ("name", manifest.dataset.name),
                ("storage id", manifest.dataset.id),
                ("chain", manifest.chain.name),
            ],
        ),
        (
            "request",
            [
                ("history", window_string(manifest.request.history)),
                ("evaluation", window_string(manifest.request.evaluation)),
            ],
        ),
        (
            "coverage",
            [
                ("history", window_string(manifest.coverage.history)),
                ("evaluation", window_string(manifest.coverage.evaluation)),
                ("history rows", str(manifest.validation.history.rows)),
                ("evaluation rows", str(manifest.validation.evaluation.rows)),
            ],
        ),
        (
            "provenance",
            [
                ("problem", manifest.semantics.problem.problem_id),
                ("compiler", manifest.semantics.problem.compiler_id),
                ("feature set", manifest.semantics.feature.feature_set_id),
                ("feature family", manifest.semantics.feature.feature_family_id),
                ("lookback", f"{manifest.semantics.problem.lookback_seconds}s"),
                ("capability", f"{manifest.semantics.problem.max_delay_seconds}s"),
            ],
        ),
    ]
    if description.runs:
        sections.append(
            (
                "runs",
                [
                    (f"run {index}", acquire_run_string(run))
                    for index, run in enumerate(description.runs, start=1)
                ],
            )
        )
    return sections


def window_string(window: DatasetWindowMetadata) -> str:
    return f"{window.start_timestamp} -> {window.end_timestamp}"


def acquire_run_string(run: AcquireRunRecord) -> str:
    return (
        f"provider={run.provider.name} "
        f"requested_history={run.facts.requested_history_window_seconds}s "
        f"samples={run.facts.resolved_capability_samples}"
    )
