"""Prediction-family registry and compiled contracts."""

from .base import (
    MetricDescriptor,
    MetricSet,
    PredictionFamilyConfig,
    PredictionHeadSpec,
    PredictionOutputSpec,
    WindowMetricSummary,
)
from .contracts import (
    ActionSpaceDecodeContext,
    CompiledPredictionContract,
    DecodedOffsets,
    EpochMetricAccumulator,
    ModelInputBatch,
    PredictionBatch,
    PredictionTargetBatch,
    StagedPreparedTargets,
    bind_prediction_representation,
    decode_context_from_batch,
)
from .registry import (
    PredictionFamilySpec,
    apply_tuned_prediction_family_parameters,
    coerce_prediction_family_config,
    compile_prediction_contract,
    prediction_family_spec,
)

__all__ = [
    "CompiledPredictionContract",
    "DecodedOffsets",
    "EpochMetricAccumulator",
    "ActionSpaceDecodeContext",
    "MetricDescriptor",
    "MetricSet",
    "ModelInputBatch",
    "PredictionBatch",
    "PredictionFamilyConfig",
    "PredictionFamilySpec",
    "PredictionHeadSpec",
    "PredictionOutputSpec",
    "PredictionTargetBatch",
    "StagedPreparedTargets",
    "WindowMetricSummary",
    "apply_tuned_prediction_family_parameters",
    "bind_prediction_representation",
    "coerce_prediction_family_config",
    "compile_prediction_contract",
    "decode_context_from_batch",
    "prediction_family_spec",
]
