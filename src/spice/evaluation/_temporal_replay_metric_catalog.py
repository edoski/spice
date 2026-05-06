"""Evaluation-private Temporal Replay metric catalog."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..metrics import MetricDescriptor


@dataclass(frozen=True, slots=True)
class TemporalReplayMetricSpec:
    id: str
    label: str
    role: Literal["primary", "secondary", "diagnostic"]
    field_name: str
    aggregate: Literal["event_mean", "fee_sum"]
    direction: Literal["maximize", "minimize"] | None = None
    window_summary: bool = False

    def descriptor(self) -> MetricDescriptor:
        return MetricDescriptor(
            id=self.id,
            label=self.label,
            role=self.role,
            direction=self.direction,
        )


TEMPORAL_REPLAY_METRICS: tuple[TemporalReplayMetricSpec, ...] = (
    TemporalReplayMetricSpec(
        id="profit_over_baseline",
        label="profit over baseline",
        role="primary",
        direction="maximize",
        field_name="profit_over_baseline",
        aggregate="event_mean",
        window_summary=True,
    ),
    TemporalReplayMetricSpec(
        id="cost_over_optimum",
        label="cost over optimum",
        role="secondary",
        direction="minimize",
        field_name="cost_over_optimum",
        aggregate="event_mean",
        window_summary=True,
    ),
    TemporalReplayMetricSpec(
        id="baseline_cost_over_optimum",
        label="baseline cost over optimum",
        role="secondary",
        direction="minimize",
        field_name="baseline_cost_over_optimum",
        aggregate="event_mean",
        window_summary=True,
    ),
    TemporalReplayMetricSpec(
        id="exact_optimum_hit_rate",
        label="exact optimum hit rate",
        role="secondary",
        direction="maximize",
        field_name="exact_optimum_hit_rate",
        aggregate="event_mean",
        window_summary=True,
    ),
    TemporalReplayMetricSpec(
        id="realized_fee_sum",
        label="realized fee sum",
        role="diagnostic",
        field_name="realized_fee_sum",
        aggregate="fee_sum",
    ),
    TemporalReplayMetricSpec(
        id="baseline_fee_sum",
        label="baseline fee sum",
        role="diagnostic",
        field_name="baseline_fee_sum",
        aggregate="fee_sum",
    ),
    TemporalReplayMetricSpec(
        id="optimum_fee_sum",
        label="optimum fee sum",
        role="diagnostic",
        field_name="optimum_fee_sum",
        aggregate="fee_sum",
    ),
)

TEMPORAL_REPLAY_METRIC_DESCRIPTORS: tuple[MetricDescriptor, ...] = tuple(
    metric.descriptor() for metric in TEMPORAL_REPLAY_METRICS
)
TEMPORAL_REPLAY_EVENT_MEAN_METRICS: tuple[TemporalReplayMetricSpec, ...] = tuple(
    metric for metric in TEMPORAL_REPLAY_METRICS if metric.aggregate == "event_mean"
)
TEMPORAL_REPLAY_WINDOW_METRICS: tuple[TemporalReplayMetricSpec, ...] = tuple(
    metric for metric in TEMPORAL_REPLAY_METRICS if metric.window_summary
)
TEMPORAL_REPLAY_EVENT_MEAN_METRIC_IDS: tuple[str, ...] = tuple(
    metric.id for metric in TEMPORAL_REPLAY_EVENT_MEAN_METRICS
)
TEMPORAL_REPLAY_METRIC_FIELD_BY_ID: dict[str, str] = {
    metric.id: metric.field_name for metric in TEMPORAL_REPLAY_METRICS
}
