# pyright: strict

"""Modeling-owned workflow summary builders."""

from __future__ import annotations

from ..core.rendering import metric_fields, window_metric_fields
from .results import LoadedEvaluationSummary, LoadedTrainingSummary


def training_summary_sections(
    summary: LoadedTrainingSummary,
) -> list[tuple[str, list[tuple[str, str]]]]:
    manifest = summary.manifest
    runtime = summary.runtime
    return [
        (
            "dataset",
            [
                ("name", manifest.dataset_name),
                ("storage id", manifest.dataset_id),
                ("chain", manifest.chain_name),
                ("model", manifest.model.id),
                ("problem", manifest.problem_id),
                ("prediction", manifest.prediction_id),
            ],
        ),
        (
            "provenance",
            [
                ("artifact id", manifest.artifact_id),
                ("variant", manifest.variant.value),
                *([] if manifest.study is None else [("study", manifest.study.name)]),
                ("capability", f"{manifest.max_delay_seconds}s"),
                ("realization", manifest.semantics.realization_policy.realization_policy_id),
            ],
        ),
        (
            "training",
            [
                ("lookback", f"{manifest.lookback_seconds}s"),
                (
                    "rows",
                    f"used={runtime.n_rows_used:,} available={runtime.n_rows_available:,}",
                ),
                (
                    "split sizes",
                    (
                        f"train={runtime.split_sizes.train_samples:,} "
                        f"validation={runtime.split_sizes.validation_samples:,} "
                        f"test={runtime.split_sizes.test_samples:,}"
                    ),
                ),
                ("best epoch", str(runtime.best_epoch)),
                (
                    "objective",
                    (
                        f"{manifest.semantics.objective.objective_id}:"
                        f"{runtime.best_objective_metric_id}"
                    ),
                ),
                ("objective direction", manifest.semantics.objective.direction),
                ("best objective", f"{runtime.best_objective_value:.4f}"),
            ],
        ),
        (
            "metrics",
            [
                *[
                    (f"validation {label}", value)
                    for label, value in metric_fields(
                        manifest.training_metric_descriptors,
                        runtime.best_validation_metrics.values,
                    )
                ],
                *[
                    (f"test {label}", value)
                    for label, value in metric_fields(
                        manifest.training_metric_descriptors,
                        runtime.test_metrics.values,
                    )
                ],
            ],
        ),
    ]


def evaluation_summary_sections(
    summary: LoadedEvaluationSummary,
) -> list[tuple[str, list[tuple[str, str]]]]:
    manifest = summary.manifest
    runtime = summary.runtime
    return [
        (
            "dataset",
            [
                ("name", manifest.dataset_name),
                ("storage id", manifest.dataset_id),
                ("chain", manifest.chain_name),
                ("model", manifest.model.id),
                ("problem", manifest.problem_id),
                ("prediction", manifest.prediction_id),
            ],
        ),
        (
            "provenance",
            [
                ("artifact id", manifest.artifact_id),
                ("evaluation id", summary.evaluation_id),
                ("variant", manifest.variant.value),
                *([] if manifest.study is None else [("study", manifest.study.name)]),
                ("capability", f"{manifest.max_delay_seconds}s"),
                ("requested", f"{runtime.delay_seconds}s"),
                ("realization", manifest.semantics.realization_policy.realization_policy_id),
            ],
        ),
        (
            "evaluation",
            [
                ("evaluator", runtime.evaluator_id),
                ("events", f"{runtime.total_events:,}"),
            ],
        ),
        (
            "results",
            metric_fields(runtime.metric_descriptors, runtime.metrics.values),
        ),
        *(
            []
            if not runtime.window_metrics
            else [
                (
                    "window metrics",
                    window_metric_fields(
                        runtime.metric_descriptors,
                        runtime.window_metrics,
                    ),
                )
            ]
        ),
    ]
