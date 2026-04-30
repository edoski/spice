"""Resolve benchmark evaluate results from remote storage."""

from __future__ import annotations

from dataclasses import dataclass

from ..config.models import EvaluateConfig
from ..core.errors import SpiceOperatorError
from ..execution.session import ExecutionSession
from ..execution.transfer import pull_artifact_from_cluster
from ..modeling.results import LoadedEvaluationSummary, LoadedTrainingSummary
from ..storage.artifact import (
    list_evaluation_summaries,
    load_artifact_manifest,
    load_training_summary,
)
from ..storage.catalog.index import resolve_artifact_record
from ..storage.selectors import ArtifactSelector


@dataclass(frozen=True, slots=True)
class ResolvedBenchmarkEvaluation:
    evaluation: LoadedEvaluationSummary
    training: LoadedTrainingSummary | None


def resolve_benchmark_evaluation(
    config: EvaluateConfig,
    *,
    session: ExecutionSession,
) -> ResolvedBenchmarkEvaluation | None:
    _pull_artifact_once(
        config,
        session=session,
        artifact_id=config.artifact_id,
    )
    record = resolve_artifact_record(
        config.storage.root,
        selector=ArtifactSelector(artifact_id=config.artifact_id),
    )
    training_summary = load_training_summary(record.state_db_path)
    manifest = load_artifact_manifest(record.state_db_path)
    expected_delay = config.delay_seconds or manifest.max_delay_seconds
    summaries = [
        summary
        for summary in list_evaluation_summaries(record.state_db_path)
        if summary.runtime.delay_seconds == expected_delay
        and summary.runtime.evaluation_id == config.evaluation.id
    ]
    if not summaries:
        return None
    if len(summaries) > 1:
        raise SpiceOperatorError(
            f"Multiple evaluation summaries match artifact {config.artifact_id}"
        )
    return ResolvedBenchmarkEvaluation(evaluation=summaries[0], training=training_summary)


def _pull_artifact_once(
    config: EvaluateConfig,
    *,
    session: ExecutionSession,
    artifact_id: str,
) -> None:
    pull_artifact_from_cluster(
        storage_root=config.storage.root,
        session=session,
        artifact_id=artifact_id,
        replace=True,
    )
