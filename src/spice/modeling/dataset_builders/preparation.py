"""Dataset-builder preparation Interface types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...config.models import SplitConfig
    from ...features import CompiledFeatureContract
    from ...temporal.capability import TemporalCapability
    from ...temporal.contracts import CompiledProblemContract
    from ...temporal.execution_policy import CompiledExecutionPolicyContract
    from ...temporal.input_normalization import CompiledInputNormalizationContract
    from ...temporal.problem_store import (
        CompiledProblemStore,
        DatasetSplitIndices,
        IntVector,
    )
    from ...temporal.scaling import ScalerStats
    from .base import BuilderRuntimeMetadata


@dataclass(slots=True)
class TrainingDatasetPreparationContext:
    feature_contract: CompiledFeatureContract
    problem_contract: CompiledProblemContract
    input_normalization_contract: CompiledInputNormalizationContract


@dataclass(slots=True)
class TrainingDatasetPreparationFacts:
    split: SplitConfig


@dataclass(slots=True)
class InclusiveEvaluationWindow:
    start_timestamp: int
    end_timestamp: int

    @property
    def exclusive_end_timestamp(self) -> int:
        return self.end_timestamp + 1


@dataclass(slots=True)
class ArtifactInferenceDatasetPreparationFacts:
    delay_seconds: int
    evaluation_window: InclusiveEvaluationWindow


@dataclass(slots=True)
class ArtifactInferenceDatasetPreparationContext:
    feature_contract: CompiledFeatureContract
    problem_contract: CompiledProblemContract
    builder_runtime_metadata: BuilderRuntimeMetadata
    scaler: ScalerStats
    temporal_capability: TemporalCapability


@dataclass(slots=True)
class CompiledInferenceDatasetPreparationRequest:
    feature_contract: CompiledFeatureContract
    problem_contract: CompiledProblemContract
    delay_seconds: int
    builder_runtime_metadata: BuilderRuntimeMetadata
    scaler: ScalerStats
    temporal_capability: TemporalCapability
    window_start_timestamp: int
    window_end_timestamp: int


@dataclass(slots=True)
class PreparedTrainingDataset:
    n_rows_available: int
    n_rows_used: int
    sample_count: int
    execution_policy: CompiledExecutionPolicyContract
    store: CompiledProblemStore
    split_indices: DatasetSplitIndices
    scaler: ScalerStats
    builder_runtime_metadata: BuilderRuntimeMetadata
    temporal_capability: TemporalCapability

    @property
    def n_features(self) -> int:
        return self.store.n_features

@dataclass(slots=True)
class PreparedInferenceDataset:
    n_history_rows: int
    n_evaluation_rows: int
    sample_count: int
    execution_policy: CompiledExecutionPolicyContract
    store: CompiledProblemStore
    sample_indices: IntVector

    @property
    def n_features(self) -> int:
        return self.store.n_features
