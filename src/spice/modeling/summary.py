"""Modeling-owned workflow summary builders."""

from __future__ import annotations

from .results import SimulationSummaryRecord, TrainingSummary


def training_summary_sections(
    summary: TrainingSummary,
) -> list[tuple[str, list[tuple[str, str]]]]:
    return [
        (
            "dataset",
            [
                ("name", summary.dataset_name),
                ("storage id", summary.dataset_id),
                ("chain", summary.chain),
                ("model", summary.model_id),
                ("task", summary.task_id),
            ],
        ),
        (
            "provenance",
            [
                ("artifact id", summary.artifact_id),
                ("variant", summary.variant.value),
                *([] if summary.study is None else [("study", summary.study.name)]),
                ("capability", f"{summary.max_supported_delay_seconds}s"),
            ],
        ),
        (
            "runtime",
            [
                ("lookback", f"{summary.lookback_seconds}s"),
                ("best epoch", str(summary.best_epoch)),
                ("device", summary.resolved_device),
                ("precision", summary.resolved_precision),
                ("compile", "on" if summary.compiled else "off"),
                ("representation", summary.representation_id),
                ("storage mode", summary.storage_mode_id),
                ("batch planner", summary.batch_planner_id),
                ("family execution", summary.family_execution_id),
            ],
        ),
        (
            "metrics",
            [
                (
                    "split sizes",
                    (
                        f"train={summary.split_sizes.train_samples:,} "
                        f"validation={summary.split_sizes.validation_samples:,} "
                        f"test={summary.split_sizes.test_samples:,}"
                    ),
                ),
                (
                    "validation profit",
                    f"{summary.best_validation_metrics.profit_over_baseline:.4f}",
                ),
                (
                    "validation cost",
                    f"{summary.best_validation_metrics.cost_over_optimum:.4f}",
                ),
                (
                    "test profit over baseline",
                    f"{summary.test_metrics.profit_over_baseline:.4f}",
                ),
            ],
        ),
    ]


def simulation_summary_sections(
    summary: SimulationSummaryRecord,
) -> list[tuple[str, list[tuple[str, str]]]]:
    return [
        (
            "dataset",
            [
                ("name", summary.dataset_name),
                ("storage id", summary.dataset_id),
                ("chain", summary.chain),
                ("model", summary.model_id),
                ("task", summary.task_id),
            ],
        ),
        (
            "provenance",
            [
                ("artifact id", summary.artifact_id),
                ("variant", summary.variant.value),
                *([] if summary.study is None else [("study", summary.study.name)]),
                ("capability", f"{summary.max_supported_delay_seconds}s"),
                ("requested", f"{summary.requested_delay_seconds}s"),
            ],
        ),
        (
            "simulation",
            [
                ("window", f"{summary.simulation_window_seconds}s"),
                ("repetitions", str(summary.repetitions)),
                ("events", f"{summary.total_events:,}"),
            ],
        ),
        (
            "results",
            [
                ("profit over baseline", f"{summary.profit_over_baseline:.4f}"),
                ("cost over optimum", f"{summary.cost_over_optimum:.4f}"),
            ],
        ),
    ]
