"""Evaluation-private temporal replay result ABI."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ._temporal_replay_metric_catalog import (
    TEMPORAL_REPLAY_EVENT_MEAN_METRICS,
    TEMPORAL_REPLAY_METRIC_FIELD_BY_ID,
    TEMPORAL_REPLAY_METRICS,
)
from .contracts import EvaluationMetadataValue


@dataclass(frozen=True, slots=True)
class TemporalReplayMetrics:
    profit_over_baseline: float
    cost_over_optimum: float
    baseline_cost_over_optimum: float
    exact_optimum_hit_rate: float
    realized_fee_sum: float
    baseline_fee_sum: float
    optimum_fee_sum: float

    def values(self) -> dict[str, float]:
        return {
            metric.id: getattr(self, metric.field_name)
            for metric in TEMPORAL_REPLAY_METRICS
        }


@dataclass(frozen=True, slots=True)
class TemporalReplayEventMetricSums:
    profit_over_baseline: float
    cost_over_optimum: float
    baseline_cost_over_optimum: float
    exact_optimum_hit_rate: float

    @classmethod
    def from_values(cls, values: Mapping[str, float]) -> TemporalReplayEventMetricSums:
        return cls(
            **{
                metric.field_name: values[metric.field_name]
                for metric in TEMPORAL_REPLAY_EVENT_MEAN_METRICS
            }
        )

    def value(self, metric_id: str) -> float:
        try:
            field_name = TEMPORAL_REPLAY_METRIC_FIELD_BY_ID[metric_id]
        except KeyError as exc:
            raise KeyError(metric_id) from exc
        if not hasattr(self, field_name):
            raise KeyError(metric_id)
        return getattr(self, field_name)


@dataclass(frozen=True, slots=True)
class TemporalReplayRunResult:
    n_events: int
    metrics: TemporalReplayMetrics
    event_metric_sums: TemporalReplayEventMetricSums
    metadata: dict[str, EvaluationMetadataValue]


@dataclass(frozen=True, slots=True)
class TemporalReplayWindowMetric:
    mean: float
    std: float


@dataclass(frozen=True, slots=True)
class TemporalReplayResult:
    metrics: TemporalReplayMetrics
    window_metrics: dict[str, TemporalReplayWindowMetric]
    total_events: int
    runs: tuple[TemporalReplayRunResult, ...]
