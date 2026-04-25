"""Generic evaluator summary helpers."""

from __future__ import annotations

from ..prediction.base import MetricSet
from .contracts import EvaluationMetadataValue, EvaluationRun, EvaluationSummary


def single_run_summary(
    *,
    metric_values: dict[str, float],
    n_events: int,
    metadata: dict[str, EvaluationMetadataValue],
) -> EvaluationSummary:
    run = EvaluationRun(
        n_events=n_events,
        metrics=metric_values,
        metadata=metadata,
    )
    return EvaluationSummary(
        metrics=MetricSet(values=dict(metric_values)),
        window_metrics={},
        total_events=n_events,
        runs=[run],
    )
