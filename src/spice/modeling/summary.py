# pyright: strict

"""Compact workflow result field builders."""

from __future__ import annotations

from pathlib import Path

from ..core.rendering import metric_string
from .results import LoadedEvaluationSummary, LoadedTrainingSummary


def training_result_fields(
    summary: LoadedTrainingSummary,
    *,
    artifact_dir: Path,
) -> list[tuple[str, str]]:
    manifest = summary.manifest
    runtime = summary.runtime
    primary_metric_id = manifest.prediction_id
    if manifest.training_metric_descriptors:
        primary_metric_id = next(
            (
                descriptor.id
                for descriptor in manifest.training_metric_descriptors
                if descriptor.role == "primary"
            ),
            manifest.training_metric_descriptors[0].id,
        )
    fields = [
        ("artifact", str(artifact_dir)),
        ("best_epoch", str(runtime.best_epoch)),
        (
            f"objective.{runtime.best_objective_metric_id}",
            metric_string(runtime.best_objective_value),
        ),
    ]
    if primary_metric_id in runtime.best_validation_metrics.values:
        fields.append(
            (
                f"validation.{primary_metric_id}",
                metric_string(runtime.best_validation_metrics.values[primary_metric_id]),
            )
        )
    if primary_metric_id in runtime.test_metrics.values:
        fields.append(
            (
                f"test.{primary_metric_id}",
                metric_string(runtime.test_metrics.values[primary_metric_id]),
            )
        )
    return fields


def evaluation_result_fields(summary: LoadedEvaluationSummary) -> list[tuple[str, str]]:
    runtime = summary.runtime
    fields = [
        ("evaluation_storage_id", summary.evaluation_storage_id),
        ("events", str(runtime.total_events)),
    ]
    primary_descriptor = next(
        (descriptor for descriptor in runtime.metric_descriptors if descriptor.role == "primary"),
        None,
    )
    if primary_descriptor is not None and primary_descriptor.id in runtime.metrics.values:
        fields.append(
            (
                primary_descriptor.id,
                metric_string(runtime.metrics.values[primary_descriptor.id]),
            )
        )
    return fields
