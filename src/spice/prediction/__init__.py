"""Prediction-family registry and compiled contracts."""

from .base import (
    MetricDescriptor,
    MetricSet,
    PredictionHeadSpec,
    PredictionOutputSpec,
    WindowMetricSummary,
)
from .contracts import (
    CompiledPredictionContract,
    EpochMetricAccumulator,
    ModelInputBatch,
    PredictionBatch,
    PredictionTargetBatch,
)
from .registry import (
    compile_prediction_contract,
    validate_prediction_family_id,
)

__all__ = [
    "CompiledPredictionContract",
    "EpochMetricAccumulator",
    "MetricDescriptor",
    "MetricSet",
    "ModelInputBatch",
    "PredictionBatch",
    "PredictionHeadSpec",
    "PredictionOutputSpec",
    "PredictionTargetBatch",
    "WindowMetricSummary",
    "compile_prediction_contract",
    "validate_prediction_family_id",
]
