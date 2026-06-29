"""Training and inference corpus preparation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ..config.models import (
    ArtifactVariant,
    ChainRuntimeSpec,
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
from ..corpus.metadata import CorpusManifest
from ..features import CompiledFeatureContract, compile_feature_contract
from ..prediction import CompiledPredictionContract, compile_prediction_contract
from ..temporal.contracts import CompiledProblemContract, compile_problem_contract
from .dataset_builders import (
    PreparedTrainingDataset,
    TrainingDatasetPreparationContext,
    TrainingDatasetPreparationFacts,
    prepare_training_dataset,
)
from .families.base import ModelConfig
from .families.registry import build_model
from .results import TrainingSourceProvenance
from .training_run import TrainingRunResult
from .training_runner import (
    TrainingFitSpec,
    run_training_fit,
)
from .training_runner_types import (
    CheckpointCallback,
    EarlyStopCallback,
    EpochEndCallback,
    TrainingCallbacks,
    TrainingCheckpoint,
)

if TYPE_CHECKING:
    from ..storage.workflow_roots import ArtifactRootHandle, CorpusRootHandle, StudyRootHandle


@dataclass(slots=True)
class TrainingSpec:
    chain: ChainSpec
    corpus_id: str
    corpus_name: str
    training_source: TrainingSourceProvenance
    training_cutoff_timestamp: int | None
    artifact_id: str
    problem: ProblemSpec
    feature_contract: CompiledFeatureContract
    problem_contract: CompiledProblemContract
    features: FeaturesConfig
    prediction: PredictionConfig
    prediction_contract: CompiledPredictionContract
    model: ModelConfig
    split: SplitConfig
    training: TrainingConfig
    variant: ArtifactVariant = ArtifactVariant.BASELINE
    study: StudyConfig | None = None
    study_id: str | None = None


@dataclass(frozen=True, slots=True)
class TrainingRunCallbacks:
    on_prepare_complete: Callable[[PreparedTrainingDataset], None] | None = None
    on_fit_start: Callable[[], None] | None = None
    on_epoch_end: EpochEndCallback | None = None
    on_early_stop: EarlyStopCallback | None = None
    on_checkpoint: CheckpointCallback | None = None


@dataclass(frozen=True, slots=True)
class CompiledTrainingContext:
    feature_contract: CompiledFeatureContract
    problem_contract: CompiledProblemContract
    prediction_contract: CompiledPredictionContract


def build_artifact_training_spec(
    config: TrainConfig,
    *,
    corpus: CorpusRootHandle,
    artifact: ArtifactRootHandle,
    corpus_manifest: CorpusManifest | None = None,
) -> TrainingSpec:
    return _build_training_spec(
        config,
        corpus=corpus,
        artifact_id=artifact.artifact_id,
        variant=artifact.variant,
        study=config.study if artifact.variant is ArtifactVariant.TUNED else None,
        study_id=artifact.study_id,
        corpus_manifest=corpus_manifest,
    )


def build_trial_training_spec(
    config: TuneConfig,
    *,
    corpus: CorpusRootHandle,
    study: StudyRootHandle,
    corpus_manifest: CorpusManifest | None = None,
) -> TrainingSpec:
    return _build_training_spec(
        config,
        corpus=corpus,
        artifact_id=study.study_id,
        variant=ArtifactVariant.TUNED,
        study=config.study,
        study_id=study.study_id,
        corpus_manifest=corpus_manifest,
    )


def _build_training_spec(
    config: TrainConfig | TuneConfig,
    *,
    corpus: CorpusRootHandle,
    artifact_id: str,
    variant: ArtifactVariant,
    study: StudyConfig | None,
    study_id: str | None,
    corpus_manifest: CorpusManifest | None,
) -> TrainingSpec:
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
        corpus_id=corpus.corpus_id,
        corpus_name=(
            corpus.corpus_name if corpus_manifest is None else corpus_manifest.corpus.name
        ),
        training_source=_training_source_from_corpus_manifest(
            corpus.corpus_id,
            training_cutoff_timestamp=config.training_cutoff_timestamp,
            corpus_manifest=corpus_manifest,
        ),
        training_cutoff_timestamp=config.training_cutoff_timestamp,
        artifact_id=artifact_id,
        problem=config.problem,
        feature_contract=context.feature_contract,
        problem_contract=context.problem_contract,
        features=config.features,
        prediction=config.prediction,
        prediction_contract=context.prediction_contract,
        model=config.model,
        variant=variant,
        study=study if variant is ArtifactVariant.TUNED else None,
        study_id=study_id if variant is ArtifactVariant.TUNED else None,
        split=config.split,
        training=config.training,
    )


def _training_source_from_corpus_manifest(
    corpus_id: str,
    *,
    training_cutoff_timestamp: int | None,
    corpus_manifest: CorpusManifest | None,
) -> TrainingSourceProvenance:
    if corpus_manifest is None:
        raise ValueError("training source provenance requires a corpus manifest")
    blocks = corpus_manifest.blocks
    coverage = blocks.coverage
    if (
        coverage.first_block is None
        or coverage.last_block is None
        or coverage.first_timestamp is None
        or coverage.last_timestamp is None
    ):
        raise ValueError("training corpus manifest is missing block coverage")
    return TrainingSourceProvenance(
        corpus_id=corpus_id,
        window_start_timestamp=blocks.request.start_timestamp,
        window_end_timestamp=blocks.request.end_timestamp,
        first_block=coverage.first_block,
        last_block=coverage.last_block,
        first_timestamp=coverage.first_timestamp,
        last_timestamp=coverage.last_timestamp,
        training_cutoff_timestamp=training_cutoff_timestamp,
        source_requirements_fingerprint=(
            corpus_manifest.source_requirements.fingerprint()
        ),
    )


def compile_training_context(
    config: TrainConfig | TuneConfig,
    *,
    chain_runtime: ChainRuntimeSpec | None = None,
) -> CompiledTrainingContext:
    feature_contract = compile_feature_contract(features=config.features)
    prediction_contract = compile_prediction_contract(
        prediction_id=config.prediction.id,
        family_id=config.prediction.family_id,
    )
    return CompiledTrainingContext(
        feature_contract=feature_contract,
        problem_contract=compile_problem_contract(
            problem=config.problem,
            feature_contract=feature_contract,
            chain_runtime=chain_runtime or config.chain.runtime,
        ),
        prediction_contract=prediction_contract,
    )


def run_training(
    history_block_path: Path,
    *,
    spec: TrainingSpec,
    callbacks: TrainingRunCallbacks | None = None,
    checkpoint: TrainingCheckpoint | None = None,
) -> TrainingRunResult:
    active_callbacks = callbacks or TrainingRunCallbacks()
    blocks = load_block_frame(history_block_path)
    prepared = prepare_training_dataset(
        blocks,
        facts=TrainingDatasetPreparationFacts(
            split=spec.split,
            training_cutoff_timestamp=spec.training_cutoff_timestamp,
        ),
        context=TrainingDatasetPreparationContext(
            feature_contract=spec.feature_contract,
            problem_contract=spec.problem_contract,
        ),
        sequence=spec.training.sequence,
    )
    if active_callbacks.on_prepare_complete is not None:
        active_callbacks.on_prepare_complete(prepared)
    model = build_model(
        prepared.n_features,
        spec.prediction_contract.build_output_spec(prepared.temporal_capability.action_width),
        spec.model,
    )
    if active_callbacks.on_fit_start is not None:
        active_callbacks.on_fit_start()
    training_result = run_training_fit(
        TrainingFitSpec(
            model=model,
            prediction_contract=spec.prediction_contract,
            prepared=prepared,
            training_config=spec.training,
            checkpoint=checkpoint,
        ),
        callbacks=TrainingCallbacks(
            on_epoch_end=active_callbacks.on_epoch_end,
            on_early_stop=active_callbacks.on_early_stop,
            on_checkpoint=active_callbacks.on_checkpoint,
        ),
    )
    return TrainingRunResult(
        model=model,
        prepared=prepared,
        training_result=training_result,
    )
