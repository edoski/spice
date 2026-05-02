"""Tuning workflow."""

from __future__ import annotations

from ..config.models import TuneConfig
from ..core.rendering import metric_string
from ..core.reporting import Reporter
from ..corpus.coverage import training_coverage_requirement, validate_corpus_coverage
from ..modeling.tuning_execution import (
    TuningBestProgress,
    TuningExecutionCallbacks,
    TuningTrialProgress,
    build_tuning_coverage_spec,
    open_tuning_execution,
    run_tuning_execution,
)
from ..storage.study_render import study_result_fields
from ..storage.workflow_roots import TuneWorkflowRoots, resolve_tune_roots


def _workflow_facts(config: TuneConfig, roots: TuneWorkflowRoots) -> list[tuple[str, str]]:
    return [
        ("dataset", roots.corpus.dataset_name),
        ("dataset_id", roots.corpus.dataset_id),
        ("chain", roots.corpus.chain_name),
        ("problem", config.problem.id),
        ("features", config.features.id),
        ("prediction", config.prediction.id),
        ("model", config.model.id),
        ("study", roots.study.study_name),
        ("study_id", roots.study.study_id),
        ("trials", str(config.tuning.trial_count)),
    ]


def _trial_message(progress: TuningTrialProgress) -> str:
    parts = [f"trial {progress.number + 1}/{progress.total_trials}"]
    if progress.state == "COMPLETE":
        parts.append("complete")
        if progress.value is not None:
            parts.append(f"value={metric_string(progress.value)}")
        if progress.best_epoch is not None:
            parts.append(f"best_epoch={progress.best_epoch}")
        return " ".join(parts)
    if progress.state == "PRUNED":
        parts.append("pruned")
        return " ".join(parts)
    parts.append("failed")
    return " ".join(parts)


def _best_message(progress: TuningBestProgress) -> str:
    return (
        "best improved "
        f"trial={progress.trial_number + 1} "
        f"value={metric_string(progress.value)}"
    )


def run(config: TuneConfig, *, reporter: Reporter | None = None) -> None:
    active_reporter = reporter or Reporter()
    roots = resolve_tune_roots(config)
    corpus_manifest = roots.corpus.load_manifest()
    active_reporter.header("tune", _workflow_facts(config, roots))
    spec = build_tuning_coverage_spec(
        config,
        roots=roots,
        corpus_manifest=corpus_manifest,
    )
    validate_corpus_coverage(
        corpus_manifest,
        contract=spec.problem_contract,
        feature_contract=spec.feature_contract,
        requirement=training_coverage_requirement(spec.problem_contract),
    )

    opened = open_tuning_execution(
        config,
        roots=roots,
        corpus_manifest=corpus_manifest,
    )
    roots.study.reindex()
    summary = run_tuning_execution(
        opened,
        config=config,
        roots=roots,
        corpus_manifest=corpus_manifest,
        callbacks=TuningExecutionCallbacks(
            on_resume=lambda existing, target: active_reporter.milestone(
                f"resume trials={existing}/{target}"
            ),
            on_study_start=lambda remaining: active_reporter.milestone(
                f"study started trials={remaining}"
            ),
            on_trial_complete=lambda progress: active_reporter.milestone(
                _trial_message(progress)
            ),
            on_best_improved=lambda progress: active_reporter.milestone(
                _best_message(progress)
            ),
        ),
    )
    roots.study.reindex()
    active_reporter.result("tune", study_result_fields(summary))
