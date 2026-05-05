"""Shared metric result ABI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .core.validation import validate_path_segment


@dataclass(frozen=True, slots=True)
class MetricDescriptor:
    id: str
    label: str
    role: Literal["primary", "secondary", "diagnostic"]
    direction: Literal["maximize", "minimize"] | None = None

    def __post_init__(self) -> None:
        validate_path_segment(self.id, label="metric.id")
        if not self.label:
            raise ValueError("metric.label must be non-empty")
        if self.role not in {"primary", "secondary", "diagnostic"}:
            raise ValueError("metric.role must be one of: primary, secondary, diagnostic")
        if self.direction is not None and self.direction not in {"maximize", "minimize"}:
            raise ValueError("metric.direction must be one of: maximize, minimize")


@dataclass(frozen=True, slots=True)
class MetricSet:
    values: dict[str, float]

    def require(self, metric_id: str) -> float:
        try:
            return self.values[metric_id]
        except KeyError as exc:
            known = ", ".join(sorted(self.values))
            raise ValueError(f"Unknown metric id: {metric_id}. Known metrics: {known}") from exc


@dataclass(frozen=True, slots=True)
class WindowMetricSummary:
    mean: float
    std: float
