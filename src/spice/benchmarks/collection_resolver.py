"""Resolve benchmark evaluate results from remote storage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config.models import EvaluateConfig, WorkflowTask
from ..core.errors import SpiceOperatorError
from ..modeling.results import LoadedEvaluationSummary, LoadedTrainingSummary
from ..storage.artifact import (
    list_evaluation_summaries,
    load_artifact_manifest,
    load_training_summary,
)
from ..storage.catalog.materialization import materialize_catalog_root
from ..storage.catalog.records import CatalogArtifactRecord
from .plan_materialization import BenchmarkPlanEntry
from .runs import BenchmarkSubmissionRecord


@dataclass(frozen=True, slots=True)
class BenchmarkCollectionSelection:
    run_id: str
    storage_root: Path
    artifact_id: str
    artifact_corpus_id: str
    evaluation_corpus_id: str
    evaluator_id: str
    configured_delay_seconds: int | None
    execution_ref: str
    job_id: str
    log_path: str
    workflow_task: str
    target: str


@dataclass(frozen=True, slots=True)
class BenchmarkCollectionMatchFacts:
    artifact_id: str
    artifact_corpus_id: str
    evaluation_corpus_id: str
    evaluation_storage_id: str
    evaluator_id: str
    delay_seconds: int
    evaluation_execution_ref: str
    evaluation_job_id: str | None
    evaluation_log_path: str | None
    evaluation_workflow_task: str | None
    evaluation_target: str | None


@dataclass(frozen=True, slots=True)
class ResolvedBenchmarkEvaluation:
    selection: BenchmarkCollectionSelection
    evaluation: LoadedEvaluationSummary
    training: LoadedTrainingSummary | None
    match_facts: BenchmarkCollectionMatchFacts


def benchmark_collection_selection(
    entry: BenchmarkPlanEntry,
    submission: BenchmarkSubmissionRecord,
    *,
    target: str,
) -> BenchmarkCollectionSelection:
    if entry.run_id != submission.run_id:
        raise SpiceOperatorError(
            f"Submission run id does not match benchmark plan entry: "
            f"{submission.run_id} != {entry.run_id}"
        )
    if entry.workflow is not WorkflowTask.EVALUATE:
        raise SpiceOperatorError(f"benchmark run {entry.run_id} is not an evaluate entry")
    if submission.workflow is not WorkflowTask.EVALUATE:
        raise SpiceOperatorError(f"benchmark submission {entry.run_id} is not evaluate")
    if not isinstance(entry.config, EvaluateConfig):
        raise SpiceOperatorError(f"benchmark run {entry.run_id} is not an evaluate config")
    facts = entry.root_facts
    if facts.consumed_artifact_id is None:
        raise SpiceOperatorError(
            f"benchmark run {entry.run_id} root facts are missing consumed artifact"
        )
    if facts.consumed_artifact_id != entry.config.artifact_id:
        raise SpiceOperatorError(
            f"benchmark run {entry.run_id} root facts artifact mismatch: "
            f"{facts.consumed_artifact_id} != {entry.config.artifact_id}"
        )
    if facts.consumed_corpus_id is None:
        raise SpiceOperatorError(
            f"benchmark run {entry.run_id} root facts are missing consumed dataset"
        )
    if facts.consumed_corpus_id != entry.config.corpus_id:
        raise SpiceOperatorError(
            f"benchmark run {entry.run_id} root facts corpus mismatch: "
            f"{facts.consumed_corpus_id} != {entry.config.corpus_id}"
        )
    if facts.consumed_artifact_corpus_id is None:
        raise SpiceOperatorError(
            f"benchmark run {entry.run_id} root facts are missing consumed artifact dataset"
        )
    return BenchmarkCollectionSelection(
        run_id=entry.run_id,
        storage_root=entry.config.storage.root,
        artifact_id=facts.consumed_artifact_id,
        artifact_corpus_id=facts.consumed_artifact_corpus_id,
        evaluation_corpus_id=facts.consumed_corpus_id,
        evaluator_id=entry.config.evaluator.id,
        configured_delay_seconds=entry.config.delay_seconds,
        execution_ref=submission.execution_ref,
        job_id=submission.job_id,
        log_path=submission.log_path,
        workflow_task=submission.workflow.value,
        target=target,
    )


def resolve_benchmark_evaluation(
    selection: BenchmarkCollectionSelection,
    *,
    artifact_record: CatalogArtifactRecord,
) -> ResolvedBenchmarkEvaluation | None:
    if artifact_record.artifact_id != selection.artifact_id:
        raise SpiceOperatorError(
            "Artifact record does not match benchmark collection selection for "
            f"{selection.run_id}: {artifact_record.artifact_id} != {selection.artifact_id}"
        )
    artifact_location = materialize_catalog_root(selection.storage_root, artifact_record)
    training_summary = load_training_summary(artifact_location.state_db_path)
    manifest = load_artifact_manifest(artifact_location.state_db_path)
    if manifest.artifact_id != selection.artifact_id:
        raise SpiceOperatorError(
            "Artifact manifest does not match benchmark collection selection for "
            f"{selection.run_id}: {manifest.artifact_id} != {selection.artifact_id}"
        )
    if manifest.corpus_id != selection.artifact_corpus_id:
        raise SpiceOperatorError(
            "Artifact manifest corpus does not match benchmark collection "
            f"selection for {selection.run_id}: {manifest.corpus_id} != "
            f"{selection.artifact_corpus_id}"
        )
    expected_delay = (
        selection.configured_delay_seconds
        or manifest.temporal_capability.max_delay_seconds
    )
    summaries = _matching_evaluation_summaries(
        selection,
        summaries=tuple(list_evaluation_summaries(artifact_location.state_db_path)),
        expected_delay=expected_delay,
    )
    if not summaries:
        return None
    evaluation = summaries[0]
    _validate_matching_provenance(selection, evaluation)
    provenance = evaluation.runtime.execution_provenance
    if provenance is None:
        raise AssertionError("validated evaluation provenance cannot be None")
    return ResolvedBenchmarkEvaluation(
        selection=selection,
        evaluation=evaluation,
        training=training_summary,
        match_facts=BenchmarkCollectionMatchFacts(
            artifact_id=selection.artifact_id,
            artifact_corpus_id=selection.artifact_corpus_id,
            evaluation_corpus_id=selection.evaluation_corpus_id,
            evaluation_storage_id=evaluation.evaluation_storage_id,
            evaluator_id=selection.evaluator_id,
            delay_seconds=expected_delay,
            evaluation_execution_ref=selection.execution_ref,
            evaluation_job_id=getattr(provenance, "job_id", None),
            evaluation_log_path=getattr(provenance, "log_path", None),
            evaluation_workflow_task=getattr(provenance, "workflow_task", None),
            evaluation_target=getattr(provenance, "target", None),
        ),
    )


def _matching_evaluation_summaries(
    selection: BenchmarkCollectionSelection,
    *,
    summaries: tuple[LoadedEvaluationSummary, ...],
    expected_delay: int,
) -> list[LoadedEvaluationSummary]:
    candidates = [
        summary
        for summary in summaries
        if summary.runtime.delay_seconds == expected_delay
        and summary.runtime.evaluator_id == selection.evaluator_id
    ]
    if not candidates:
        return []
    provenance_matches = [
        summary
        for summary in candidates
        if _provenance_matches(selection, summary)
    ]
    if not provenance_matches:
        execution_ref_matches = [
            summary
            for summary in candidates
            if summary.runtime.execution_provenance is not None
            and summary.runtime.execution_provenance.execution_ref == selection.execution_ref
        ]
        if execution_ref_matches:
            _validate_matching_provenance(selection, execution_ref_matches[0])
        raise SpiceOperatorError(
            "No evaluation summary matches submitted execution provenance for "
            f"benchmark run {selection.run_id}: expected {selection.execution_ref}"
        )
    if len(provenance_matches) > 1:
        raise SpiceOperatorError(
            "Multiple evaluation summaries match submitted execution provenance for "
            f"benchmark run {selection.run_id}"
        )
    return provenance_matches


def _provenance_matches(
    selection: BenchmarkCollectionSelection,
    summary: LoadedEvaluationSummary,
) -> bool:
    provenance = summary.runtime.execution_provenance
    if provenance is None:
        return False
    return (
        provenance.execution_ref == selection.execution_ref
        and getattr(provenance, "job_id", None) == selection.job_id
        and getattr(provenance, "log_path", None) == selection.log_path
        and getattr(provenance, "workflow_task", None) == selection.workflow_task
        and getattr(provenance, "target", None) == selection.target
    )


def _validate_matching_provenance(
    selection: BenchmarkCollectionSelection,
    summary: LoadedEvaluationSummary,
) -> None:
    provenance = summary.runtime.execution_provenance
    if provenance is None:
        raise SpiceOperatorError(
            "No evaluation summary matches submitted execution provenance for "
            f"benchmark run {selection.run_id}: expected {selection.execution_ref}"
        )
    expected = {
        "job_id": selection.job_id,
        "log_path": selection.log_path,
        "workflow_task": selection.workflow_task,
        "target": selection.target,
    }
    actual = {
        "job_id": getattr(provenance, "job_id", None),
        "log_path": getattr(provenance, "log_path", None),
        "workflow_task": getattr(provenance, "workflow_task", None),
        "target": getattr(provenance, "target", None),
    }
    mismatches = [
        f"{field}={actual[field]} expected {expected[field]}"
        for field in expected
        if actual[field] != expected[field]
    ]
    if mismatches:
        raise SpiceOperatorError(
            "Evaluation summary provenance does not match benchmark submission for "
            f"{selection.run_id}: "
            + ", ".join(mismatches)
        )
