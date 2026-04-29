"""Resolve benchmark evaluate results from remote storage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from ..config.models import EvaluateConfig
from ..core.errors import ConfigResolutionError, SpiceOperatorError
from ..execution.session import ExecutionSession
from ..execution.transfer import pull_artifact_from_cluster, pull_study_from_cluster
from ..modeling.results import LoadedEvaluationSummary, LoadedTrainingSummary
from ..modeling.tuning import apply_study_best_params
from ..storage.artifact import list_evaluation_summaries, load_training_summary
from ..storage.selectors import ArtifactSelector, StudySelector
from ..storage.workflow_paths import resolve_workflow_paths


@dataclass(frozen=True, slots=True)
class ResolvedBenchmarkEvaluation:
    evaluation: LoadedEvaluationSummary
    training: LoadedTrainingSummary | None


def resolve_benchmark_evaluation(
    config: EvaluateConfig,
    *,
    session: ExecutionSession,
) -> ResolvedBenchmarkEvaluation | None:
    active_config = config
    study_id: str | None = None
    if config.artifact.variant.value == "tuned":
        study_paths = resolve_workflow_paths(config)
        if study_paths.study_id is None:
            raise ConfigResolutionError("tuned evaluation has no study identity")
        _pull_study_once(
            config,
            session=session,
            study_id=study_paths.study_id,
        )
        applied = apply_study_best_params(config)
        active_config = cast(EvaluateConfig, applied.config)
        study_id = applied.study_id
    paths = resolve_workflow_paths(active_config, study_id=study_id)
    if paths.artifact_id is None or paths.artifact_state_db is None:
        raise ConfigResolutionError("evaluation has no artifact identity")
    if active_config.evaluation is None:
        raise ConfigResolutionError("evaluation workflow requires evaluation")
    _pull_artifact_once(
        active_config,
        session=session,
        artifact_id=paths.artifact_id,
    )
    training_summary = load_training_summary(paths.artifact_state_db)
    summaries = [
        summary
        for summary in list_evaluation_summaries(paths.artifact_state_db)
        if summary.runtime.delay_seconds == active_config.delay_seconds
        and summary.runtime.evaluation_id == active_config.evaluation.id
    ]
    if not summaries:
        return None
    if len(summaries) > 1:
        raise SpiceOperatorError(
            f"Multiple evaluation summaries match artifact {paths.artifact_id}"
        )
    return ResolvedBenchmarkEvaluation(evaluation=summaries[0], training=training_summary)


def _pull_study_once(
    config: EvaluateConfig,
    *,
    session: ExecutionSession,
    study_id: str,
) -> None:
    pull_study_from_cluster(
        storage_root=config.storage.root,
        session=session,
        selector=StudySelector(
            study_id=study_id,
            chain_name=config.chain.name,
            dataset_name=config.dataset.name,
        ),
        replace=True,
    )


def _pull_artifact_once(
    config: EvaluateConfig,
    *,
    session: ExecutionSession,
    artifact_id: str,
) -> None:
    pull_artifact_from_cluster(
        storage_root=config.storage.root,
        session=session,
        selector=ArtifactSelector(
            artifact_id=artifact_id,
            chain_name=config.chain.name,
            dataset_name=config.dataset.name,
        ),
        replace=True,
    )
