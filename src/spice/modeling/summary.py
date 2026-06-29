# pyright: strict

"""Compact workflow result field builders."""

from __future__ import annotations

from pathlib import Path

from ..core.rendering import metric_string
from .results import LoadedTrainingSummary


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
            "best.validation.total_loss",
            metric_string(runtime.best_validation_total_loss),
        ),
    ]
    if primary_metric_id == "total_loss":
        fields.append(("test.total_loss", metric_string(runtime.test_total_loss)))
    return fields
