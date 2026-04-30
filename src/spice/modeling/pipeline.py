"""Training and inference dataset preparation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from ..config.models import (
    ArtifactVariant,
    ChainSpec,
    FeaturesConfig,
    PredictionConfig,
    ProblemSpec,
    SplitConfig,
    StudyConfig,
    TrainConfig,
    TrainingConfig,
    TuneConfig,
)
from ..corpus.io import load_block_frame
from ..corpus.metadata import DatasetManifest
from ..features import CompiledFeatureContract
from ..objectives import CompiledObjectiveContract, ObjectiveConfig
from ..prediction import CompiledPredictionContract
from ..semantics import FeatureSemantics
from ..storage.workflow_paths import WorkflowPaths
from ..temporal.contracts import CompiledProblemContract
from ..temporal.execution_policy import CompiledExecutionPolicyContract
from ..temporal.input_normalization import CompiledInputNormalizationContract
from ..temporal.problem_store import (
    CompiledProblemStore,
    DatasetSplitIndices,
    IntVector,
)
from ..temporal.scaling import ScalerStats
from ._training_context import compile_training_context
from .dataset_builders import (
    BuilderRuntimeMetadata,
    CompiledDatasetBuilderContract,
    DatasetBuilderConfig,
)
from .families.base import ModelConfig
from .families.registry import build_model
from .models import TemporalModel
from .objective_metrics import CompiledObjectiveMetricSource
from .representations import CompiledRepresentationContract
from .training_runner import (
    EarlyStopCallback,
    EpochEndCallback,
    TrainingCallbacks,
    TrainingFitSpec,
    TrainingResult,
    run_training_fit,
)


@dataclass(slots=True)
class TrainingSpec:
    chain: ChainSpec
    dataset_id: str
    dataset_name: str
    artifact_id: str
    problem: ProblemSpec
    dataset_builder: DatasetBuilderConfig
    dataset_builder_contract: CompiledDatasetBuilderContract
    feature_contract: CompiledFeatureContract
    problem_contract: CompiledProblemContract
    features: FeaturesConfig
    prediction: PredictionConfig
    objective: ObjectiveConfig
    prediction_contract: CompiledPredictionContract
    objective_contract: CompiledObjectiveContract
    objective_metric_source: CompiledObjectiveMetricSource
    input_normalization_contract: CompiledInputNormalizationContract
    representation_contract: CompiledRepresentationContract
    model: ModelConfig
    split: SplitConfig
    training: TrainingConfig
    variant: ArtifactVariant = ArtifactVariant.BASELINE
    study: StudyConfig | None = None
    study_id: str | None = None


@dataclass(slots=True)
class InferencePreparationSpec:
    feature_contract: CompiledFeatureContract
    problem_contract: CompiledProblemContract
    delay_seconds: int
    builder_runtime_metadata: BuilderRuntimeMetadata
    compiler_runtime_metadata: object
    scaler: ScalerStats
    max_candidate_slots: int
    window_start_timestamp: int
    window_end_timestamp: int


def build_training_spec(
    config: TrainConfig | TuneConfig,
    *,
    paths: WorkflowPaths,
    corpus_manifest: DatasetManifest | None = None,
) -> TrainingSpec:
    variant = ArtifactVariant.TUNED if isinstance(config, TuneConfig) else config.artifact.variant
    chain = (
        ChainSpec(name=corpus_manifest.chain.name, runtime=corpus_manifest.chain.runtime)
        if corpus_manifest is not None
        else config.chain
    )
    context = compile_training_context(
        config,
        chain_runtime=None if corpus_manifest is None else corpus_manifest.chain.runtime,
    )
    return TrainingSpec(
        chain=chain,
        dataset_id=paths.corpus_id,
        dataset_name=(
            config.dataset.name if corpus_manifest is None else corpus_manifest.dataset.name
        ),
        artifact_id=(
            paths.artifact_id
            if paths.artifact_id is not None
            else paths.study_id or "trial"
        ),
        problem=config.problem,
        dataset_builder=config.dataset_builder,
        dataset_builder_contract=context.dataset_builder_contract,
        feature_contract=context.feature_contract,
        problem_contract=context.problem_contract,
        features=config.features,
        prediction=config.prediction,
        objective=config.objective,
        prediction_contract=context.prediction_contract,
        objective_contract=context.objective_contract,
        objective_metric_source=context.objective_metric_source,
        input_normalization_contract=context.input_normalization_contract,
        representation_contract=context.representation_contract,
        model=config.model,
        variant=variant,
        study=config.study if variant is ArtifactVariant.TUNED else None,
        study_id=paths.study_id if variant is ArtifactVariant.TUNED else None,
        split=config.split,
        training=config.training,
    )


@dataclass(slots=True)
class PreparedTrainingDataset:
    n_rows_available: int
    n_rows_used: int
    sample_count: int
    feature: FeatureSemantics
    execution_policy: CompiledExecutionPolicyContract
    store: CompiledProblemStore
    split_indices: DatasetSplitIndices
    scaler: ScalerStats
    builder_runtime_metadata: BuilderRuntimeMetadata

    @property
    def n_features(self) -> int:
        return self.store.n_features

    @property
    def max_candidate_slots(self) -> int:
        return self.store.max_candidate_slots


@dataclass(slots=True)
class PreparedInferenceDataset:
    n_history_rows: int
    n_evaluation_rows: int
    sample_count: int
    feature: FeatureSemantics
    execution_policy: CompiledExecutionPolicyContract
    store: CompiledProblemStore
    sample_indices: IntVector

    @property
    def n_features(self) -> int:
        return self.store.n_features


@dataclass(slots=True)
class TrainingRunResult:
    model: TemporalModel
    prepared: PreparedTrainingDataset
    training_result: TrainingResult
    prediction_training_state: object | None


def prepare_training_dataset(
    blocks: pl.DataFrame,
    *,
    spec: TrainingSpec,
) -> PreparedTrainingDataset:
    return spec.dataset_builder_contract.prepare_training_dataset(blocks, spec=spec)


def prepare_inference_dataset(
    history_blocks: pl.DataFrame,
    evaluation_blocks: pl.DataFrame,
    *,
    dataset_builder_contract: CompiledDatasetBuilderContract,
    feature_contract: CompiledFeatureContract,
    problem_contract: CompiledProblemContract,
    delay_seconds: int,
    builder_runtime_metadata: BuilderRuntimeMetadata,
    compiler_runtime_metadata: object,
    scaler: ScalerStats,
    max_candidate_slots: int,
    window_start_timestamp: int,
    window_end_timestamp: int,
) -> PreparedInferenceDataset:
    return dataset_builder_contract.prepare_inference_dataset(
        history_blocks,
        evaluation_blocks,
        spec=InferencePreparationSpec(
            feature_contract=feature_contract,
            problem_contract=problem_contract,
            delay_seconds=delay_seconds,
            builder_runtime_metadata=builder_runtime_metadata,
            compiler_runtime_metadata=compiler_runtime_metadata,
            scaler=scaler,
            max_candidate_slots=max_candidate_slots,
            window_start_timestamp=window_start_timestamp,
            window_end_timestamp=window_end_timestamp,
        ),
    )


def run_training(
    history_block_path: Path,
    *,
    spec: TrainingSpec,
    on_prepare_complete: Callable[[PreparedTrainingDataset], None] | None = None,
    on_fit_start: Callable[[], None] | None = None,
    on_epoch_end: EpochEndCallback | None = None,
    on_early_stop: EarlyStopCallback | None = None,
) -> TrainingRunResult:
    blocks = load_block_frame(history_block_path)
    prepared = prepare_training_dataset(blocks, spec=spec)
    if on_prepare_complete is not None:
        on_prepare_complete(prepared)
    model = build_model(
        prepared.n_features,
        spec.prediction_contract.build_output_spec(prepared.max_candidate_slots),
        spec.model,
    )
    if on_fit_start is not None:
        on_fit_start()
    training_result = run_training_fit(
        TrainingFitSpec(
            model=model,
            model_config=spec.model,
            prediction_contract=spec.prediction_contract,
            objective_contract=spec.objective_contract,
            objective_metric_source=spec.objective_metric_source,
            execution_policy=prepared.execution_policy,
            representation_contract=spec.representation_contract,
            store=prepared.store,
            train_sample_indices=prepared.split_indices.train,
            validation_sample_indices=prepared.split_indices.validation,
            training_config=spec.training,
        ),
        callbacks=TrainingCallbacks(
            on_epoch_end=on_epoch_end,
            on_early_stop=on_early_stop,
        ),
    )
    return TrainingRunResult(
        model=model,
        prepared=prepared,
        training_result=training_result,
        prediction_training_state=training_result.prediction_training_state,
    )
