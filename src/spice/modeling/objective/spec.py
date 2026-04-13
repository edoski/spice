"""Canonical objective semantics for training, tuning, and reporting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class MetricDescriptor:
    id: str
    label: str
    role: Literal["primary", "secondary", "diagnostic"]


@dataclass(frozen=True, slots=True)
class ObjectiveSpec:
    objective_id: str
    primary_metric_id: str
    direction: Literal["maximize", "minimize"]
    metric_order: tuple[MetricDescriptor, ...]

    @property
    def checkpoint_monitor(self) -> str:
        return f"validation_{self.primary_metric_id}"

    @property
    def early_stopping_monitor(self) -> str:
        return self.checkpoint_monitor


_OBJECTIVES: dict[str, ObjectiveSpec] = {}
_DEFAULT_OBJECTIVE_ID = "profit_over_baseline"


def register_objective(spec: ObjectiveSpec) -> None:
    existing = _OBJECTIVES.get(spec.objective_id)
    if existing is not None:
        raise ValueError(f"Duplicate objective id: {spec.objective_id}")
    _OBJECTIVES[spec.objective_id] = spec


def objective_spec(objective_id: str) -> ObjectiveSpec:
    try:
        return _OBJECTIVES[objective_id]
    except KeyError as exc:
        known = ", ".join(sorted(_OBJECTIVES))
        raise ValueError(
            f"Unknown objective id: {objective_id}. Known objectives: {known}"
        ) from exc


def active_objective() -> ObjectiveSpec:
    return objective_spec(_DEFAULT_OBJECTIVE_ID)


def metric_ids_in_display_order(spec: ObjectiveSpec | None = None) -> tuple[str, ...]:
    resolved = active_objective() if spec is None else spec
    return tuple(metric.id for metric in resolved.metric_order)


register_objective(
    ObjectiveSpec(
        objective_id="profit_over_baseline",
        primary_metric_id="profit_over_baseline",
        direction="maximize",
        metric_order=(
            MetricDescriptor(
                id="profit_over_baseline",
                label="profit over baseline",
                role="primary",
            ),
            MetricDescriptor(
                id="cost_over_optimum",
                label="cost over optimum",
                role="secondary",
            ),
            MetricDescriptor(
                id="objective_loss",
                label="objective loss",
                role="diagnostic",
            ),
            MetricDescriptor(
                id="exact_optimum_hit_rate",
                label="exact optimum hit rate",
                role="diagnostic",
            ),
        ),
    )
)
