"""Corpus-root inspection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..corpus.metadata import (
    AcquireRunRecord,
    CorpusManifest,
    SplitCoverageMetadata,
    SplitRequestMetadata,
)
from .catalog.records import CatalogCorpusRecord
from .corpus import list_acquire_runs, load_corpus_manifest


@dataclass(frozen=True, slots=True)
class CorpusRootDescription:
    manifest: CorpusManifest
    runs: list[AcquireRunRecord] | None = None


def dataset_list_sections(
    records: list[CatalogCorpusRecord],
) -> list[tuple[str, list[tuple[str, str]]]]:
    return [
        (
            "corpora",
            [
                (
                    record.corpus_name,
                    f"chain={record.chain_name} id={record.corpus_id}",
                )
                for record in records
            ],
        )
    ]


def describe_dataset_root(
    root_db_path: Path, *, detail: str | None = None
) -> CorpusRootDescription:
    return CorpusRootDescription(
        manifest=load_corpus_manifest(root_db_path),
        runs=list_acquire_runs(root_db_path) if detail == "runs" else None,
    )


def dataset_sections(
    description: CorpusRootDescription,
) -> list[tuple[str, list[tuple[str, str]]]]:
    manifest = description.manifest
    blocks = manifest.blocks
    sections = [
        (
            "corpus",
            [
                ("name", manifest.corpus.name),
                ("storage id", manifest.corpus.id),
                ("chain", manifest.chain.name),
            ],
        ),
        (
            "request",
            [
                ("blocks", request_string(blocks.request)),
            ],
        ),
        (
            "coverage",
            [
                ("blocks", coverage_string(blocks.coverage)),
                ("rows", str(blocks.coverage.rows)),
                ("outcome", blocks.materialization.outcome),
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


def request_string(window: SplitRequestMetadata) -> str:
    return f"{window.start_timestamp} -> {window.end_timestamp}"


def coverage_string(window: SplitCoverageMetadata) -> str:
    return f"{window.first_timestamp} -> {window.last_timestamp}"


def acquire_run_string(run: AcquireRunRecord) -> str:
    return (
        f"provider={run.provider.name} "
        f"requested_window={run.facts.requested_window_seconds}s"
    )
