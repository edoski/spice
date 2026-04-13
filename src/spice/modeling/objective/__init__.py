"""Objective-centric training semantics."""

from .loss import compute_objective_loss
from .metrics import (
    BatchMetrics,
    EpochMetrics,
    SimulationPrimarySummary,
    WindowMetricSummary,
    compute_temporal_batch_metrics,
    summarize_epoch_metrics,
    summarize_simulation_primary,
    summarize_window_metric,
)
from .references import (
    CandidateReferenceArrays,
    CandidateReferenceTensors,
    candidate_reference_arrays,
    candidate_reference_tensors,
    masked_candidate_logits,
)
from .selection import (
    best_epoch,
    objective_value,
    optuna_direction,
    primary_direction,
    primary_validation_metric_name,
)
from .spec import (
    MetricDescriptor,
    ObjectiveSpec,
    active_objective,
    metric_ids_in_display_order,
    objective_spec,
)

__all__ = [
    "BatchMetrics",
    "CandidateReferenceArrays",
    "CandidateReferenceTensors",
    "EpochMetrics",
    "MetricDescriptor",
    "ObjectiveSpec",
    "SimulationPrimarySummary",
    "WindowMetricSummary",
    "active_objective",
    "best_epoch",
    "candidate_reference_arrays",
    "candidate_reference_tensors",
    "compute_objective_loss",
    "compute_temporal_batch_metrics",
    "masked_candidate_logits",
    "metric_ids_in_display_order",
    "objective_value",
    "objective_spec",
    "optuna_direction",
    "primary_direction",
    "primary_validation_metric_name",
    "summarize_epoch_metrics",
    "summarize_simulation_primary",
    "summarize_window_metric",
]
