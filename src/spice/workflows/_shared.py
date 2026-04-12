"""Shared workflow helpers."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from ..core.config import ArtifactVariant, ExperimentConfig, WorkflowTask
from ..core.console import ConsoleRuntime, Reporter, create_console_runtime
from ..modeling.evaluation import EpochMetrics
from ..modeling.pipeline import TrainingSpec
from ._tuning import apply_tuned_parameters, load_tuning_best_params_report


def build_training_spec(config: ExperimentConfig) -> TrainingSpec:
    variant = selected_artifact_variant(config)
    return TrainingSpec(
        chain=config.chain,
        dataset_id=config.dataset.id,
        feature_set=config.feature_set,
        model=config.model,
        variant=variant,
        study=config.study if variant is ArtifactVariant.TUNED else None,
        max_delay_seconds=config.dataset.temporal.max_delay_seconds,
        lookback_seconds=config.dataset.temporal.lookback_seconds,
        sample_count=config.dataset.sampling.sample_count,
        split=config.split,
        training=config.training,
    )


def epoch_metrics_to_dict(metrics: EpochMetrics) -> dict[str, float]:
    return {
        "loss": metrics.total_loss,
        "accuracy": metrics.accuracy,
        "cost_over_optimum": metrics.mean_cost_over_optimum,
        "profit_over_baseline": metrics.mean_profit_over_baseline,
    }


@dataclass(slots=True)
class WorkflowSession:
    runtime: ConsoleRuntime
    reporter: Reporter


def selected_artifact_variant(config: ExperimentConfig) -> ArtifactVariant:
    if config.task is WorkflowTask.TUNE:
        return ArtifactVariant.TUNED
    return config.artifact.variant


@contextmanager
def abort_cleanup(
    reporter: Reporter,
    *,
    label: str,
    cleanup: Callable[[], None],
) -> Iterator[None]:
    try:
        yield
    except KeyboardInterrupt:
        cleanup()
        reporter.log(f"{label} interrupted; partial outputs removed", level="warning")
        raise


@contextmanager
def managed_workflow(
    config: ExperimentConfig,
    *,
    run_name: str,
    runtime: ConsoleRuntime | None = None,
    reporter: Reporter | None = None,
    default_runtime_factory: Callable[..., ConsoleRuntime] = create_console_runtime,
    nested: bool = False,
) -> Iterator[WorkflowSession]:
    del config, run_name, nested
    active_runtime = runtime or default_runtime_factory(reporter=reporter)
    owns_runtime = runtime is None
    try:
        with active_runtime.activate():
            yield WorkflowSession(
                runtime=active_runtime,
                reporter=active_runtime.reporter,
            )
    finally:
        if owns_runtime:
            active_runtime.close()


def trial_artifact_dir(config: ExperimentConfig, trial_number: int) -> Path:
    return config.paths.tuning_root / "trials" / f"trial-{trial_number:03d}"


def apply_study_best_params(config: ExperimentConfig) -> ExperimentConfig:
    path = config.paths.tuning_best_params_path
    try:
        report = load_tuning_best_params_report(path)
    except OSError as exc:
        raise FileNotFoundError(
            f"Best tuning params are required but missing: {path}"
        ) from exc
    return apply_tuned_parameters(config, report.params)
