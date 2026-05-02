"""Modeling-domain helpers for tuned parameter application."""

from __future__ import annotations

from dataclasses import dataclass
from typing import overload

from ..config.models import (
    ProblemSpec,
    StudyConfig,
    TrainConfig,
    TrainingConfig,
    TuneConfig,
    TunedParameterSet,
    TunedProblemParams,
    TunedTrainingParams,
)
from ..core.errors import ConfigResolutionError, MissingStateError
from ..storage.study_manifest import load_study_manifest, validate_tuned_artifact_definition
from ..storage.study_optuna import load_best_params
from ..storage.workflow_roots import CorpusRootHandle, StudyRootHandle
from .families.registry import (
    apply_model_tuned_parameters,
)


@dataclass(frozen=True, slots=True)
class AppliedStudyBestParams:
    config: TrainConfig
    study_id: str


@overload
def apply_tuned_parameters(
    config: TrainConfig,
    params: TunedParameterSet,
) -> TrainConfig: ...


@overload
def apply_tuned_parameters(
    config: TuneConfig,
    params: TunedParameterSet,
) -> TuneConfig: ...


def apply_tuned_parameters(
    config: TrainConfig | TuneConfig,
    params: TunedParameterSet,
) -> TrainConfig | TuneConfig:
    training = _apply_training_params(config.training, params.training)
    problem = _apply_problem_params(config.problem, params.problem)
    model = config.model
    if params.model is not None:
        model = apply_model_tuned_parameters(model, params.model)
    if isinstance(config, TuneConfig):
        return TuneConfig(
            chain=config.chain,
            dataset=config.dataset,
            storage=config.storage,
            dataset_id=config.dataset_id,
            problem=problem,
            model=model,
            dataset_builder=config.dataset_builder,
            features=config.features,
            prediction=config.prediction,
            objective=config.objective,
            evaluation=config.evaluation,
            study=config.study,
            artifact=config.artifact,
            training=training,
            split=config.split,
            tuning=config.tuning,
            tuning_space=config.tuning_space,
        )
    return TrainConfig(
        chain=config.chain,
        dataset=config.dataset,
        storage=config.storage,
        dataset_id=config.dataset_id,
        study_id=config.study_id,
        problem=problem,
        model=model,
        dataset_builder=config.dataset_builder,
        features=config.features,
        prediction=config.prediction,
        objective=config.objective,
        evaluation=config.evaluation,
        study=config.study,
        artifact=config.artifact,
        training=training,
        split=config.split,
        tuning=config.tuning,
        tuning_space=config.tuning_space,
    )


def apply_study_best_params(
    config: TrainConfig,
    *,
    study: StudyRootHandle,
    corpus: CorpusRootHandle,
) -> AppliedStudyBestParams:
    try:
        manifest = load_study_manifest(study.state_db_path)
    except MissingStateError as exc:
        raise ConfigResolutionError(
            "Configured tuned study does not match the current problem, features, "
            "model, or study selection"
        ) from exc
    study_config = _with_manifest_study_name(config, study_name=manifest.study_name)
    validate_tuned_artifact_definition(
        study_config,
        manifest=manifest,
        study_id=study.study_id,
        dataset_id=corpus.dataset_id,
    )
    params = load_best_params(study.state_db_path, study_name=manifest.study_name)
    tuned_config = apply_tuned_parameters(study_config, params)
    return AppliedStudyBestParams(config=tuned_config, study_id=study.study_id)


def _with_manifest_study_name(config: TrainConfig, *, study_name: str) -> TrainConfig:
    return TrainConfig(
        chain=config.chain,
        dataset=config.dataset,
        storage=config.storage,
        dataset_id=config.dataset_id,
        study_id=config.study_id,
        problem=config.problem,
        model=config.model,
        dataset_builder=config.dataset_builder,
        features=config.features,
        prediction=config.prediction,
        objective=config.objective,
        evaluation=config.evaluation,
        study=StudyConfig(name=study_name),
        artifact=config.artifact,
        training=config.training,
        split=config.split,
        tuning=config.tuning,
        tuning_space=config.tuning_space,
    )


def _apply_training_params(
    training: TrainingConfig,
    params: TunedTrainingParams | None,
) -> TrainingConfig:
    if params is None:
        return training
    return TrainingConfig(
        learning_rate=(
            training.learning_rate
            if params.learning_rate is None
            else params.learning_rate
        ),
        weight_decay=(
            training.weight_decay
            if params.weight_decay is None
            else params.weight_decay
        ),
        batch_size=training.batch_size if params.batch_size is None else params.batch_size,
        max_epochs=training.max_epochs,
        early_stopping=training.early_stopping,
        gradient_clip_norm=training.gradient_clip_norm,
        seed=training.seed,
        deterministic=training.deterministic,
        log_every_n_steps=training.log_every_n_steps,
        input_normalization=training.input_normalization,
    )


def _apply_problem_params(
    problem: ProblemSpec,
    params: TunedProblemParams | None,
) -> ProblemSpec:
    if params is None or params.lookback_seconds is None:
        return problem
    return ProblemSpec(
        id=problem.id,
        lookback_seconds=params.lookback_seconds,
        sample_count=problem.sample_count,
        max_delay_seconds=problem.max_delay_seconds,
        compiler=problem.compiler,
        execution_policy=problem.execution_policy,
    )
