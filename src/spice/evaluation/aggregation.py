"""Replay cost aggregation specs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..core.specs import lookup_local_spec
from .config import EvaluationAggregationId

PROFIT_OVER_BASELINE = "profit_over_baseline"
COST_OVER_OPTIMUM = "cost_over_optimum"
BASELINE_COST_OVER_OPTIMUM = "baseline_cost_over_optimum"
REPLAY_RATIO_METRIC_IDS = (
    PROFIT_OVER_BASELINE,
    COST_OVER_OPTIMUM,
    BASELINE_COST_OVER_OPTIMUM,
)


@dataclass(frozen=True, slots=True)
class ReplayCostSummary:
    n_events: int
    realized_fee_sum: float
    baseline_fee_sum: float
    optimum_fee_sum: float
    event_metric_sums: dict[str, float]


@dataclass(frozen=True, slots=True)
class ReplayAggregationSpec:
    id: EvaluationAggregationId
    run_metrics: Callable[[ReplayCostSummary], dict[str, float]]
    summary_metrics: Callable[[ReplayCostSummary], dict[str, float]]


def _event_mean_metrics(costs: ReplayCostSummary) -> dict[str, float]:
    return {
        PROFIT_OVER_BASELINE: _event_metric_mean(
            costs.event_metric_sums,
            PROFIT_OVER_BASELINE,
            costs.n_events,
        ),
        COST_OVER_OPTIMUM: _event_metric_mean(
            costs.event_metric_sums,
            COST_OVER_OPTIMUM,
            costs.n_events,
        ),
        BASELINE_COST_OVER_OPTIMUM: _event_metric_mean(
            costs.event_metric_sums,
            BASELINE_COST_OVER_OPTIMUM,
            costs.n_events,
        ),
    }


def _total_ratio_metrics(costs: ReplayCostSummary) -> dict[str, float]:
    return {
        PROFIT_OVER_BASELINE: (
            (costs.baseline_fee_sum - costs.realized_fee_sum) / costs.baseline_fee_sum
        ),
        COST_OVER_OPTIMUM: (
            (costs.realized_fee_sum - costs.optimum_fee_sum) / costs.optimum_fee_sum
        ),
        BASELINE_COST_OVER_OPTIMUM: (
            (costs.baseline_fee_sum - costs.optimum_fee_sum) / costs.optimum_fee_sum
        ),
    }


_REPLAY_AGGREGATION_SPECS: dict[EvaluationAggregationId, ReplayAggregationSpec] = {
    EvaluationAggregationId.EVENT_MEAN: ReplayAggregationSpec(
        id=EvaluationAggregationId.EVENT_MEAN,
        run_metrics=_event_mean_metrics,
        summary_metrics=_event_mean_metrics,
    ),
    EvaluationAggregationId.TOTAL_RATIO: ReplayAggregationSpec(
        id=EvaluationAggregationId.TOTAL_RATIO,
        run_metrics=_total_ratio_metrics,
        summary_metrics=_total_ratio_metrics,
    ),
}


def replay_aggregation_spec(
    aggregation_id: EvaluationAggregationId,
) -> ReplayAggregationSpec:
    return lookup_local_spec(
        _REPLAY_AGGREGATION_SPECS,
        aggregation_id,
        "evaluation.aggregation.id",
    )


def _event_metric_mean(
    event_metric_sums: dict[str, float],
    metric_id: str,
    n_events: int,
) -> float:
    if n_events <= 0:
        raise ValueError("evaluation event count must be positive")
    return event_metric_sums[metric_id] / n_events
