"""Shared objective-driven selection rules."""

from __future__ import annotations

from .metrics import EpochMetrics
from .spec import ObjectiveSpec, active_objective


def primary_metric_name(spec: ObjectiveSpec | None = None) -> str:
    resolved = active_objective() if spec is None else spec
    return resolved.primary_metric_id


def primary_validation_metric_name(spec: ObjectiveSpec | None = None) -> str:
    resolved = active_objective() if spec is None else spec
    return resolved.checkpoint_monitor


def primary_direction(spec: ObjectiveSpec | None = None) -> str:
    resolved = active_objective() if spec is None else spec
    return resolved.direction


def optuna_direction(spec: ObjectiveSpec | None = None) -> str:
    return primary_direction(spec)


def objective_value(metrics: EpochMetrics, spec: ObjectiveSpec | None = None) -> float:
    resolved = active_objective() if spec is None else spec
    return getattr(metrics, resolved.primary_metric_id)


def best_epoch(history: list[EpochMetrics], spec: ObjectiveSpec | None = None) -> int:
    if not history:
        return 1
    resolved = active_objective() if spec is None else spec
    if resolved.direction == "maximize":
        winner = max(
            range(len(history)),
            key=lambda index: (
                getattr(history[index], resolved.primary_metric_id),
                -history[index].cost_over_optimum,
                -history[index].objective_loss,
            ),
        )
    else:
        winner = min(
            range(len(history)),
            key=lambda index: (
                getattr(history[index], resolved.primary_metric_id),
                history[index].cost_over_optimum,
                history[index].objective_loss,
            ),
        )
    return winner + 1
