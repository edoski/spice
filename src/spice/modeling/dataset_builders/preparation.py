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
class DatasetSplitIndices:
    train: IntVector
    validation: IntVector
    test: IntVector


@dataclass(frozen=True, slots=True)
class EvaluationCoverageWindow:
    first_timestamp: int
    last_timestamp: int

    def __post_init__(self) -> None:
        if self.last_timestamp < self.first_timestamp:
            raise ValueError("evaluation coverage last_timestamp must be >= first_timestamp")

    def to_sample_timestamp_window(self) -> SampleTimestampWindow:
        return SampleTimestampWindow(
            start_timestamp_inclusive=self.first_timestamp,
            end_timestamp_exclusive=self.last_timestamp + 1,
        )


@dataclass(frozen=True, slots=True)
class SampleTimestampWindow:
    start_timestamp_inclusive: int
    end_timestamp_exclusive: int

    def __post_init__(self) -> None:
        if self.end_timestamp_exclusive <= self.start_timestamp_inclusive:
            raise ValueError(
                "sample timestamp window end_timestamp_exclusive must be greater "
                "than start_timestamp_inclusive"
            )


@dataclass(slots=True)
class ArtifactInferenceDatasetPreparationFacts:
    delay_seconds: int
    evaluation_coverage: EvaluationCoverageWindow


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
    sample_timestamp_window: SampleTimestampWindow


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
