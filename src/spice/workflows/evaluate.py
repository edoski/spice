"""Evaluation workflow."""

from __future__ import annotations

from typing import cast

from ..config.models import EvaluateConfig
from ..core.errors import ConfigResolutionError
from ..core.reporting import Reporter
from ..modeling.artifact_inference import prepare_artifact_inference_context
from ..modeling.results import LoadedEvaluationSummary, build_evaluation_runtime_summary
from ..modeling.scoring import score_evaluation
from ..modeling.summary import evaluation_result_fields
from ..modeling.tuning import apply_study_best_params
from ..storage.artifact import upsert_evaluation_state
from ..storage.workflow_paths import resolve_workflow_paths


def _workflow_facts(config: EvaluateConfig) -> list[tuple[str, str]]:
    if config.evaluation is None:
        raise ConfigResolutionError("evaluation workflow requires evaluation")
    facts = [
        ("dataset", config.dataset.name),
        ("chain", config.chain.name),
        ("problem", config.problem.id),
        ("prediction", config.prediction.id),
        ("delay", f"{config.delay_seconds}s"),
        ("model", config.model.id),
        ("variant", config.artifact.variant.value),
        ("evaluation", config.evaluation.id),
    ]
    if config.artifact.variant.value == "tuned":
        facts.append(("study", config.study.name))
    return facts


def run(config: EvaluateConfig, *, reporter: Reporter | None = None) -> None:
    active_config: EvaluateConfig = config
    study_id: str | None = None
    if config.artifact.variant.value == "tuned":
        applied = apply_study_best_params(config)
        active_config = cast(EvaluateConfig, applied.config)
        study_id = applied.study_id
    paths = resolve_workflow_paths(active_config, study_id=study_id)
    active_reporter = reporter or Reporter()
    active_reporter.header("evaluate", _workflow_facts(active_config))
    inference_context = prepare_artifact_inference_context(
        active_config,
        paths=paths,
    )
    prepared = inference_context.prepared
    active_reporter.milestone(
        "prepare "
        f"history_rows={prepared.n_history_rows} "
        f"evaluation_rows={prepared.n_evaluation_rows} "
        f"samples={prepared.sample_count}"
    )
    evaluation = score_evaluation(inference_context.scoring_context)
    runtime_summary = build_evaluation_runtime_summary(
        prepared=prepared,
        evaluation=evaluation,
        delay_seconds=active_config.delay_seconds,
        evaluation_id=inference_context.evaluator_contract.evaluation_id,
        evaluation_config=inference_context.evaluator_contract.config_payload,
        metric_descriptors=inference_context.evaluator_contract.metric_descriptors,
    )
    artifact_dir = paths.artifact_root
    assert artifact_dir is not None
    evaluation_id, recorded_at = upsert_evaluation_state(
        artifact_dir / ".spice" / "state.sqlite",
        summary=runtime_summary,
    )
    summary = LoadedEvaluationSummary(
        evaluation_id=evaluation_id,
        recorded_at=recorded_at,
        manifest=inference_context.loaded_artifact.manifest,
        runtime=runtime_summary,
    )
    active_reporter.result("evaluate", evaluation_result_fields(summary))
