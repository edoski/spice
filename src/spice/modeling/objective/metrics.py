"""Objective-aware metric derivation."""

from __future__ import annotations

import statistics
from dataclasses import dataclass

import torch

from .loss import compute_objective_loss
from .references import candidate_reference_tensors


@dataclass(frozen=True, slots=True)
class BatchMetrics:
    count: int
    objective_loss_sum: float
    exact_hit_count: int
    realized_fee_sum: float
    baseline_fee_sum: float
    optimal_fee_sum: float


@dataclass(frozen=True, slots=True)
class EpochMetrics:
    objective_loss: float
    exact_optimum_hit_rate: float
    cost_over_optimum: float
    profit_over_baseline: float


@dataclass(frozen=True, slots=True)
class SimulationPrimarySummary:
    profit_over_baseline: float
    cost_over_optimum: float
    baseline_cost_over_optimum: float
    realized_fee_sum: float
    baseline_fee_sum: float
    optimum_fee_sum: float


@dataclass(frozen=True, slots=True)
class WindowMetricSummary:
    mean: float
    std: float


def compute_temporal_batch_metrics(
    logits: torch.Tensor,
    candidate_log_fees: torch.Tensor,
    candidate_mask: torch.Tensor,
) -> tuple[torch.Tensor, BatchMetrics]:
    objective_loss = compute_objective_loss(
        logits,
        candidate_log_fees,
        candidate_mask,
    )
    references = candidate_reference_tensors(
        logits.detach(),
        candidate_log_fees.detach(),
        candidate_mask.detach(),
    )
    realized_fee = torch.exp(references.realized_log_fee)
    baseline_fee = torch.exp(references.baseline_log_fee)
    optimum_fee = torch.exp(references.optimal_log_fee)
    count = int(candidate_log_fees.shape[0])
    return objective_loss, BatchMetrics(
        count=count,
        objective_loss_sum=float(objective_loss.detach().item()) * count,
        exact_hit_count=int(
            (references.predicted_candidate_index == references.optimal_candidate_index)
            .sum()
            .item()
        ),
        realized_fee_sum=float(realized_fee.sum().item()),
        baseline_fee_sum=float(baseline_fee.sum().item()),
        optimal_fee_sum=float(optimum_fee.sum().item()),
    )


def summarize_epoch_metrics(batch_metrics: list[BatchMetrics]) -> EpochMetrics:
    if not batch_metrics:
        raise ValueError("Cannot summarize an empty batch metric collection")
    count = sum(item.count for item in batch_metrics)
    realized_fee_sum = sum(item.realized_fee_sum for item in batch_metrics)
    baseline_fee_sum = sum(item.baseline_fee_sum for item in batch_metrics)
    optimal_fee_sum = sum(item.optimal_fee_sum for item in batch_metrics)
    return EpochMetrics(
        objective_loss=sum(item.objective_loss_sum for item in batch_metrics) / count,
        exact_optimum_hit_rate=sum(item.exact_hit_count for item in batch_metrics) / count,
        cost_over_optimum=(realized_fee_sum - optimal_fee_sum) / optimal_fee_sum,
        profit_over_baseline=(baseline_fee_sum - realized_fee_sum) / baseline_fee_sum,
    )


def summarize_simulation_primary(
    *,
    realized_fee_sum: float,
    baseline_fee_sum: float,
    optimum_fee_sum: float,
) -> SimulationPrimarySummary:
    return SimulationPrimarySummary(
        profit_over_baseline=(baseline_fee_sum - realized_fee_sum) / baseline_fee_sum,
        cost_over_optimum=(realized_fee_sum - optimum_fee_sum) / optimum_fee_sum,
        baseline_cost_over_optimum=(baseline_fee_sum - optimum_fee_sum) / optimum_fee_sum,
        realized_fee_sum=realized_fee_sum,
        baseline_fee_sum=baseline_fee_sum,
        optimum_fee_sum=optimum_fee_sum,
    )


def summarize_window_metric(values: list[float]) -> WindowMetricSummary:
    return WindowMetricSummary(
        mean=statistics.fmean(values),
        std=statistics.pstdev(values),
    )
