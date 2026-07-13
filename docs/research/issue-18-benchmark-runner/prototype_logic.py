"""PROTOTYPE ONLY: compare runner shapes against the approved finite thesis work.

Question: do the real matrices need a benchmark-owned batch language, or are
named lists of already-constructed WorkflowRequest values enough?

The IDs below are fixed fixture IDs. Production constructors must mint UUIDv4
once and persist the complete request before submission or work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Workflow = Literal["train", "tune", "evaluate"]
CHAINS = ("ethereum", "polygon", "avalanche")
HORIZONS = (2, 3, 4, 5, 10, 15, 30, 50, 100, 200)
CONTEXTS = (50, 100, 500, 1000)


@dataclass(frozen=True, slots=True)
class RequestPreview:
    """Fixture projection of an exact typed request, not another request schema."""

    label: str
    workflow: Workflow
    output_id: str
    artifact_id: str | None = None


@dataclass(frozen=True, slots=True)
class Stage:
    name: str
    requests: tuple[RequestPreview, ...]
    reused_artifact_count: int = 0
    owner_gate_after: str | None = None


@dataclass(frozen=True, slots=True)
class BatchEntry:
    """The smallest plausible extra batch language."""

    label: str
    request: RequestPreview
    after_labels: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Design:
    name: str
    production_files: int
    production_lines: int
    owned_types: int
    owned_interfaces: int
    persistent_shapes: int
    scheduling_concepts: int
    note: str


@dataclass(frozen=True, slots=True)
class EvidenceRow:
    label: str
    artifact_id: str
    evaluation_id: str
    record_path: str


def _fixture_uuid(number: int) -> str:
    return f"00000000-0000-4000-8000-{number:012x}"


def approved_stages() -> tuple[Stage, ...]:
    """Build the finite topology without running or persisting anything."""

    next_id = 1

    def request(label: str, workflow: Workflow, artifact_id: str | None = None) -> RequestPreview:
        nonlocal next_id
        value = RequestPreview(label, workflow, _fixture_uuid(next_id), artifact_id)
        next_id += 1
        return value

    capacity = tuple(
        request(f"selection/capacity/{chain}/{candidate}", "train")
        for chain in CHAINS
        for candidate in ("capacity", "activity")
    )
    utc = tuple(request(f"selection/utc_hour/{chain}/addition", "train") for chain in CHAINS)
    weighted = tuple(
        request(f"selection/ce_weighting/{chain}/corrected", "train") for chain in CHAINS
    )
    studies = tuple(request(f"hpo/{chain}/k5", "tune") for chain in CHAINS)
    context = tuple(
        request(f"context/{chain}/c{context}", "train") for chain in CHAINS for context in CONTEXTS
    )
    horizons = tuple(
        request(f"horizon/{chain}/k{horizon}", "train") for chain in CHAINS for horizon in HORIZONS
    )

    # Fixture assumption only: the corrected-weighting additions stand in for
    # the three selected C=200 artifacts. Real winners remain owner-gated.
    context_artifacts = (*weighted, *context)
    test_artifacts = (*context_artifacts, *horizons)
    evaluations = tuple(
        request(f"testing/{artifact.label}", "evaluate", artifact.output_id)
        for artifact in test_artifacts
    )
    return (
        Stage("capacity_activity", capacity),
        Stage("utc_hour", utc, reused_artifact_count=3, owner_gate_after="capacity_activity"),
        Stage("ce_weighting", weighted, reused_artifact_count=3, owner_gate_after="utc_hour"),
        Stage("representative_hpo", studies, owner_gate_after="ce_weighting"),
        Stage("context", context, reused_artifact_count=3, owner_gate_after="representative_hpo"),
        Stage("horizon", horizons, owner_gate_after="representative_hpo"),
        Stage("sealed_testing", evaluations, owner_gate_after="context+horizon+affordability"),
    )


def minimal_batch(stages: tuple[Stage, ...]) -> tuple[tuple[str, tuple[BatchEntry, ...]], ...]:
    """Wrap each already-independent stage in the proposed extra batch types."""

    return tuple(
        (stage.name, tuple(BatchEntry(item.label, item) for item in stage.requests))
        for stage in stages
    )


def evidence_rows(stages: tuple[Stage, ...]) -> tuple[EvidenceRow, ...]:
    testing = next(stage for stage in stages if stage.name == "sealed_testing")
    rows = [
        EvidenceRow(
            label=item.label,
            artifact_id=item.artifact_id or "",
            evaluation_id=item.output_id,
            record_path=f"evaluations/{item.output_id}.json",
        )
        for item in testing.requests
    ]
    rows.append(
        EvidenceRow(
            label="accelerator/same_weight_parity",
            artifact_id="",
            evaluation_id="",
            record_path="<issue-40-report>",
        )
    )
    return tuple(rows)


def designs() -> tuple[Design, ...]:
    return (
        Design(
            "explicit named request lists",
            production_files=0,
            production_lines=0,
            owned_types=0,
            owned_interfaces=2,
            persistent_shapes=0,
            scheduling_concepts=0,
            note=(
                "Construct exact requests by named stage; call execution; "
                "load exact evaluation IDs."
            ),
        ),
        Design(
            "minimal BatchPlan",
            production_files=1,
            production_lines=45,
            owned_types=2,
            owned_interfaces=3,
            persistent_shapes=0,
            scheduling_concepts=1,
            note=(
                "Adds BatchPlan/BatchEntry, but every surviving stage contains "
                "independent requests."
            ),
        ),
        Design(
            "current generic engine",
            production_files=18,
            production_lines=2891,
            owned_types=40,
            owned_interfaces=27,
            persistent_shapes=8,
            scheduling_concepts=6,
            note=(
                "Axes, grids, graph matching, ledgers, codecs, collection search, and SQLite index."
            ),
        ),
    )


def counts(stages: tuple[Stage, ...]) -> dict[str, int]:
    requests = [item for stage in stages for item in stage.requests]
    by_workflow = {
        workflow: sum(item.workflow == workflow for item in requests)
        for workflow in ("train", "tune", "evaluate")
    }
    return {
        **by_workflow,
        "durable_non_hpo_artifacts": by_workflow["train"],
        "hpo_studies": by_workflow["tune"],
        "sealed_test_cells": by_workflow["evaluate"],
        "evidence_rows": len(evidence_rows(stages)),
    }
