"""Workflow runner reporting composition."""

from __future__ import annotations

from ..config.models import TuneConfig
from ..core.rendering import metric_string
from ..core.reporting import Reporter
from ..modeling.tuning_execution import (
    TuningBestProgress,
    TuningExecutionCallbacks,
    TuningTrialProgress,
)
from ..storage.study_models import StudySummary
from ..storage.study_render import study_result_fields
from ..storage.workflow_roots import TuneWorkflowRoots


def tune_workflow_facts(config: TuneConfig, roots: TuneWorkflowRoots) -> list[tuple[str, str]]:
    return [
        ("corpus", roots.corpus.corpus_name),
        ("corpus_id", roots.corpus.corpus_id),
        ("chain", roots.corpus.chain_name),
        ("problem", config.problem.id),
        ("features", config.features.id),
        ("prediction", config.prediction.id),
        ("model", config.model.id),
        ("study", roots.study.study_name),
        ("study_id", roots.study.study_id),
        ("trials", str(config.tuning.trial_count)),
    ]


def report_tune_resume(reporter: Reporter, *, existing: int, target: int) -> None:
    reporter.milestone(f"resume trials={existing}/{target}")


def report_tune_study_start(reporter: Reporter, *, remaining: int) -> None:
    reporter.milestone(f"study started trials={remaining}")


def report_tune_trial(reporter: Reporter, progress: TuningTrialProgress) -> None:
    reporter.milestone(_trial_message(progress))


def report_tune_best(reporter: Reporter, progress: TuningBestProgress) -> None:
    reporter.milestone(
        "best improved "
        f"trial={progress.trial_number + 1} "
        f"value={metric_string(progress.value)}"
    )


def report_tune_result(reporter: Reporter, *, summary: StudySummary) -> None:
    reporter.result("tune", study_result_fields(summary))


def tune_reporting_callbacks(reporter: Reporter) -> TuningExecutionCallbacks:
    return TuningExecutionCallbacks(
        on_resume=lambda existing, target: report_tune_resume(
            reporter,
            existing=existing,
            target=target,
        ),
        on_study_start=lambda remaining: report_tune_study_start(
            reporter,
            remaining=remaining,
        ),
        on_trial_complete=lambda progress: report_tune_trial(
            reporter,
            progress,
        ),
        on_best_improved=lambda progress: report_tune_best(
            reporter,
            progress,
        ),
    )


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
