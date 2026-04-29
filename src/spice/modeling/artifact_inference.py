"""Artifact-to-inference preparation context."""

from __future__ import annotations

from dataclasses import dataclass

from ..config.models import EvaluateConfig
from ..core.errors import ConfigResolutionError
from ..corpus.coverage import evaluation_coverage_requirement, validate_corpus_coverage
from ..corpus.io import load_block_frame
from ..evaluation import CompiledEvaluatorContract, compile_evaluator_contract
from ..prediction import compile_prediction_contract
from ..storage.corpus import load_dataset_manifest
from ..storage.workflow_paths import WorkflowPaths
from ..temporal.contracts import compile_problem_contract
from .artifacts import LoadedTrainingArtifact, load_training_artifact, validate_artifact_semantics
from .dataset_builders import (
    coerce_builder_runtime_metadata,
    compiler_runtime_metadata_from_builder_payload,
)
from .pipeline import PreparedInferenceDataset, prepare_inference_dataset
from .scoring import EvaluationScoringContext


@dataclass(slots=True)
class ArtifactInferenceContext:
    loaded_artifact: LoadedTrainingArtifact
    prepared: PreparedInferenceDataset
    evaluator_contract: CompiledEvaluatorContract
    scoring_context: EvaluationScoringContext


def prepare_artifact_inference_context(
    config: EvaluateConfig,
    *,
    paths: WorkflowPaths,
) -> ArtifactInferenceContext:
    if paths.artifact_root is None:
        raise ConfigResolutionError("evaluation workflow requires artifact output paths")
    if config.evaluation is None:
        raise ConfigResolutionError("evaluation workflow requires evaluation")

    loaded_artifact = load_training_artifact(paths.artifact_root)
    validated = validate_artifact_semantics(
        loaded_artifact.manifest,
        problem=config.problem,
        dataset_builder=config.dataset_builder,
        features=config.features,
        prediction=config.prediction,
        objective=config.objective,
        model=config.model,
        split=config.split,
        training=config.training,
    )
    feature_contract = validated.feature_contract
    problem_contract = compile_problem_contract(
        problem=config.problem,
        feature_contract=feature_contract,
        chain_runtime=config.chain.runtime,
    )
    prediction_contract = compile_prediction_contract(
        prediction_id=config.prediction.id,
        family_id=config.prediction.family_id,
    )
    evaluator_contract = compile_evaluator_contract(config.evaluation)
    if config.delay_seconds > loaded_artifact.manifest.max_delay_seconds:
        raise ConfigResolutionError(
            "delay_seconds exceeds artifact capability: "
            f"{config.delay_seconds} > {loaded_artifact.manifest.max_delay_seconds}"
        )

    validate_corpus_coverage(
        load_dataset_manifest(paths.corpus_state_db),
        contract=problem_contract,
        feature_contract=feature_contract,
        requirement=evaluation_coverage_requirement(
            problem_contract,
            delay_seconds=config.delay_seconds,
        ),
    )
    builder_runtime_metadata = coerce_builder_runtime_metadata(
        loaded_artifact.manifest.dataset_builder.id,
        loaded_artifact.manifest.builder_runtime_metadata,
    )
    compiler_runtime_metadata = compiler_runtime_metadata_from_builder_payload(
        builder_runtime_metadata,
        compiler_id=problem_contract.compiler_id,
    )
    prepared = prepare_inference_dataset(
        load_block_frame(paths.history_dir),
        load_block_frame(paths.evaluation_dir),
        dataset_builder_contract=validated.dataset_builder_contract,
        feature_contract=feature_contract,
        problem_contract=problem_contract,
        delay_seconds=config.delay_seconds,
        builder_runtime_metadata=builder_runtime_metadata,
        compiler_runtime_metadata=compiler_runtime_metadata,
        scaler=loaded_artifact.manifest.scaler,
        max_candidate_slots=loaded_artifact.manifest.max_candidate_slots,
        window_start_timestamp=config.evaluation_window_start_timestamp,
        window_end_timestamp=config.evaluation_window_end_timestamp,
    )
    scoring_context = EvaluationScoringContext(
        model=loaded_artifact.model,
        model_config=loaded_artifact.manifest.model,
        prediction_contract=prediction_contract,
        representation_contract=loaded_artifact.representation_contract,
        evaluator_contract=evaluator_contract,
        execution_policy=prepared.execution_policy,
        store=prepared.store,
        sample_indices=prepared.sample_indices,
        batch_size=config.training.batch_size,
    )
    return ArtifactInferenceContext(
        loaded_artifact=loaded_artifact,
        prepared=prepared,
        evaluator_contract=evaluator_contract,
        scoring_context=scoring_context,
    )
