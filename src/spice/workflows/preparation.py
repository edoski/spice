"""Prepared workflow inputs and root resolution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from ..config.models import AcquireConfig, ArtifactVariant, EvaluateConfig, TrainConfig, TuneConfig
from ..corpus.coverage import training_coverage_requirement, validate_corpus_coverage
from ..corpus.metadata import DatasetManifest
from ..modeling.artifact_inference import (
    ArtifactInferenceContext,
    prepare_artifact_inference_context,
)
from ..modeling.pipeline import TrainingSpec, build_artifact_training_spec
from ..modeling.tuning import apply_study_best_params
from ..modeling.tuning_execution import build_tuning_coverage_spec
from ..storage.workflow_root_materialization import (
    materialize_acquire_roots,
    materialize_evaluate_roots,
    materialize_train_roots,
    materialize_tune_roots,
)
from ..storage.workflow_roots import (
    AcquireWorkflowRoots,
    EvaluateWorkflowRoots,
    TrainWorkflowRoots,
    TunedTrainWorkflowRoots,
    TuneWorkflowRoots,
)


@dataclass(frozen=True, slots=True)
class PreparedAcquireWorkflow:
    config: AcquireConfig
    roots: AcquireWorkflowRoots


@dataclass(frozen=True, slots=True)
class PreparedTrainWorkflow:
    requested_config: TrainConfig
    active_config: TrainConfig
    roots: TrainWorkflowRoots
    corpus_manifest: DatasetManifest
    spec: TrainingSpec


@dataclass(frozen=True, slots=True)
class PreparedTuneWorkflow:
    config: TuneConfig
    roots: TuneWorkflowRoots
    corpus_manifest: DatasetManifest
    coverage_spec: TrainingSpec


@dataclass(frozen=True, slots=True)
class PreparedEvaluateWorkflow:
    config: EvaluateConfig
    roots: EvaluateWorkflowRoots
    inference_context: ArtifactInferenceContext


def prepare_acquire(config: AcquireConfig) -> PreparedAcquireWorkflow:
    return PreparedAcquireWorkflow(
        config=config,
        roots=materialize_acquire_roots(config),
    )


def prepare_train(config: TrainConfig) -> PreparedTrainWorkflow:
    roots = materialize_train_roots(config)
    active_config = config
    if config.artifact.variant is ArtifactVariant.TUNED:
        assert isinstance(roots, TunedTrainWorkflowRoots)
        applied = apply_study_best_params(
            config,
            study=roots.study,
            corpus=roots.corpus,
        )
        active_config = cast(TrainConfig, applied.config)
    corpus_manifest = roots.corpus.load_manifest()
    spec = build_artifact_training_spec(
        active_config,
        corpus=roots.corpus,
        artifact=roots.artifact,
        corpus_manifest=corpus_manifest,
    )
    validate_corpus_coverage(
        corpus_manifest,
        contract=spec.problem_contract,
        feature_contract=spec.feature_contract,
        requirement=training_coverage_requirement(spec.problem_contract),
    )
    return PreparedTrainWorkflow(
        requested_config=config,
        active_config=active_config,
        roots=roots,
        corpus_manifest=corpus_manifest,
        spec=spec,
    )


def prepare_tune(config: TuneConfig) -> PreparedTuneWorkflow:
    roots = materialize_tune_roots(config)
    corpus_manifest = roots.corpus.load_manifest()
    coverage_spec = build_tuning_coverage_spec(
        config,
        roots=roots,
        corpus_manifest=corpus_manifest,
    )
    validate_corpus_coverage(
        corpus_manifest,
        contract=coverage_spec.problem_contract,
        feature_contract=coverage_spec.feature_contract,
        requirement=training_coverage_requirement(coverage_spec.problem_contract),
    )
    return PreparedTuneWorkflow(
        config=config,
        roots=roots,
        corpus_manifest=corpus_manifest,
        coverage_spec=coverage_spec,
    )


def prepare_evaluate(config: EvaluateConfig) -> PreparedEvaluateWorkflow:
    roots = materialize_evaluate_roots(config)
    return PreparedEvaluateWorkflow(
        config=config,
        roots=roots,
        inference_context=prepare_artifact_inference_context(
            config,
            corpus=roots.corpus,
            artifact=roots.artifact,
        ),
    )
