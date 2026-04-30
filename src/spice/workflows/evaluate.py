"""Evaluation workflow."""

from __future__ import annotations

from ..config.models import EvaluateConfig
from ..core.reporting import Reporter
from ..modeling.artifact_inference import prepare_artifact_inference_context
from ..modeling.results import LoadedEvaluationSummary, build_evaluation_runtime_summary
from ..modeling.scoring import score_evaluation
from ..modeling.summary import evaluation_result_fields
from ..storage.artifact import upsert_evaluation_state
from ..storage.root_consumer_paths import resolve_evaluate_consumer_paths


def _workflow_facts(config: EvaluateConfig) -> list[tuple[str, str]]:
    facts = [
        ("dataset_id", config.dataset_id),
        ("artifact_id", config.artifact_id),
        ("delay", "artifact_max" if config.delay_seconds is None else f"{config.delay_seconds}s"),
        ("evaluation", config.evaluation.id),
        ("batch_size", str(config.batch_size)),
    ]
    return facts


def run(config: EvaluateConfig, *, reporter: Reporter | None = None) -> None:
    paths = resolve_evaluate_consumer_paths(config)
    active_reporter = reporter or Reporter()
    active_reporter.header("evaluate", _workflow_facts(config))
    inference_context = prepare_artifact_inference_context(
        config,
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
        delay_seconds=inference_context.delay_seconds,
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
