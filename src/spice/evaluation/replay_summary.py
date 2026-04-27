"""Replay-specific cost aggregation helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..prediction import DecodedOffsets
from ..prediction.base import MetricSet, WindowMetricSummary
from ..temporal.execution_policy import CompiledExecutionPolicyContract
from ..temporal.problem_store import CompiledProblemStore
from .aggregation import (
    BASELINE_COST_OVER_OPTIMUM,
    COST_OVER_OPTIMUM,
    PROFIT_OVER_BASELINE,
    REPLAY_RATIO_METRIC_IDS,
    ReplayAggregationSpec,
    ReplayCostSummary,
)
from .contracts import EvaluationRun, EvaluationSummary, IntVector


@dataclass(frozen=True, slots=True)
class ReplayRun:
    run: EvaluationRun
    event_metric_sums: dict[str, float]


def summarize_selected_costs(
    store: CompiledProblemStore,
    execution_policy: CompiledExecutionPolicyContract,
    decoded_offsets: DecodedOffsets,
    sample_indices: IntVector,
    selected_positions: IntVector,
    *,
    aggregation: ReplayAggregationSpec,
    metadata: dict[str, str | int | float],
) -> ReplayRun:
    if len(decoded_offsets) != int(sample_indices.shape[0]):
        raise ValueError("decoded_offsets must align with sample_indices")
    if selected_positions.size == 0:
        raise ValueError("selected_positions must be non-empty")

    realized = execution_policy.realize_selections(
        store,
        decoded_offsets,
        sample_indices,
        selected_positions,
    )
    realized_logs = store.log_base_fees[realized.realized_rows]
    realized_fees = np.exp(realized_logs.astype(np.float64, copy=False))
    baseline_fees = np.exp(
        store.log_base_fees[realized.baseline_rows].astype(np.float64, copy=False)
    )
    realized_total = float(realized_fees.sum())
    baseline_total = float(baseline_fees.sum())
    optimum_logs = store.log_base_fees[realized.optimum_rows].astype(np.float64, copy=False)
    optimum_fees = np.exp(optimum_logs)
    optimum_total = float(optimum_fees.sum())
    if baseline_total <= 0.0:
        raise ValueError("baseline fee total must be positive")
    if optimum_total <= 0.0:
        raise ValueError("optimum fee total must be positive")
    if np.any(baseline_fees <= 0.0):
        raise ValueError("baseline fees must be positive")
    if np.any(optimum_fees <= 0.0):
        raise ValueError("optimum fees must be positive")

    profit_values = (baseline_fees - realized_fees) / baseline_fees
    cost_values = (realized_fees - optimum_fees) / optimum_fees
    baseline_cost_values = (baseline_fees - optimum_fees) / optimum_fees
    costs = ReplayCostSummary(
        n_events=int(selected_positions.shape[0]),
        realized_fee_sum=realized_total,
        baseline_fee_sum=baseline_total,
        optimum_fee_sum=optimum_total,
        event_metric_sums={
            PROFIT_OVER_BASELINE: float(profit_values.sum()),
            COST_OVER_OPTIMUM: float(cost_values.sum()),
            BASELINE_COST_OVER_OPTIMUM: float(baseline_cost_values.sum()),
        },
    )
    aggregated_metrics = aggregation.run_metrics(costs)
    run = EvaluationRun(
        n_events=costs.n_events,
        metrics={
            **aggregated_metrics,
            "realized_fee_sum": costs.realized_fee_sum,
            "baseline_fee_sum": costs.baseline_fee_sum,
            "optimum_fee_sum": costs.optimum_fee_sum,
        },
        metadata={
            **dict(metadata),
            "overflow_count": int(realized.overflow_mask.sum()),
        },
    )
    return ReplayRun(run=run, event_metric_sums=costs.event_metric_sums)


def summarize_runs(
    runs: list[ReplayRun],
    *,
    aggregation: ReplayAggregationSpec,
) -> EvaluationSummary:
    if not runs:
        raise ValueError("evaluation produced no runs")

    public_runs = [run.run for run in runs]
    realized_fee_sum = sum(run.metrics["realized_fee_sum"] for run in public_runs)
    baseline_fee_sum = sum(run.metrics["baseline_fee_sum"] for run in public_runs)
    optimum_fee_sum = sum(run.metrics["optimum_fee_sum"] for run in public_runs)
    if baseline_fee_sum <= 0.0:
        raise ValueError("baseline fee sum must be positive")
    if optimum_fee_sum <= 0.0:
        raise ValueError("optimum fee sum must be positive")
    total_events = sum(run.n_events for run in public_runs)
    costs = ReplayCostSummary(
        n_events=total_events,
        realized_fee_sum=realized_fee_sum,
        baseline_fee_sum=baseline_fee_sum,
        optimum_fee_sum=optimum_fee_sum,
        event_metric_sums={
            metric_id: sum(run.event_metric_sums[metric_id] for run in runs)
            for metric_id in REPLAY_RATIO_METRIC_IDS
        },
    )
    aggregated_metrics = aggregation.summary_metrics(costs)
    return EvaluationSummary(
        metrics=MetricSet(
            values={
                **aggregated_metrics,
                "realized_fee_sum": realized_fee_sum,
                "baseline_fee_sum": baseline_fee_sum,
                "optimum_fee_sum": optimum_fee_sum,
            }
        ),
        window_metrics={
            "profit_over_baseline": _summarize_window_metric(
                [run.metrics["profit_over_baseline"] for run in public_runs]
            ),
            "cost_over_optimum": _summarize_window_metric(
                [run.metrics["cost_over_optimum"] for run in public_runs]
            ),
            "baseline_cost_over_optimum": _summarize_window_metric(
                [run.metrics["baseline_cost_over_optimum"] for run in public_runs]
            ),
        }
        if len(public_runs) > 1
        else {},
        total_events=total_events,
        runs=public_runs,
    )


def _summarize_window_metric(values: list[float]) -> WindowMetricSummary:
    return WindowMetricSummary(
        mean=float(np.mean(values)),
        std=float(np.std(values)),
    )
