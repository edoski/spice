"""Canonical provenance payload builders for storage and study validation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from pydantic import BaseModel

from ..config.models import (
    ArtifactVariant,
    EvaluateConfig,
    PredictionConfig,
    ProblemSpec,
    SplitConfig,
    StudyConfig,
    TrainConfig,
    TrainingConfig,
    TuneConfig,
    TuningConfig,
    TuningSpaceConfig,
)
from ..core.errors import ConfigResolutionError
from ..modeling.dataset_builders import DatasetBuilderConfig
from ..modeling.families.base import ModelConfig
from ..objectives import ObjectiveConfig

if TYPE_CHECKING:
    from ..config.models import ChainSpec, DatasetSpec, FeatureSetConfig
    from .study_models import StudyManifest


def _payload(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, Mapping):
        return {str(key): _payload(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_payload(child) for child in value]
    return value


def study_storage_identity_payload(
    *,
    chain: ChainSpec,
    dataset: DatasetSpec,
    corpus_id: str,
    dataset_builder: DatasetBuilderConfig,
    feature_set: FeatureSetConfig,
    model: ModelConfig,
    problem: ProblemSpec,
    prediction: PredictionConfig,
    objective: ObjectiveConfig,
    study: StudyConfig,
    split: SplitConfig,
    training: TrainingConfig,
    tuning: TuningConfig,
    tuning_space: TuningSpaceConfig,
) -> dict[str, object]:
    return {
        "chain": _payload(chain),
        "dataset": _payload(dataset),
        "corpus_id": corpus_id,
        "dataset_builder": _payload(dataset_builder),
        "feature_set": _payload(feature_set),
        "model": _payload(model),
        "problem": _payload(problem),
        "prediction": _payload(prediction),
        "objective": _payload(objective),
        "study": _payload(study),
        "split": _payload(split),
        "training": _payload(training),
        "tuning": _payload(tuning),
        "tuning_space": _payload(tuning_space),
    }


def study_storage_identity_payload_from_config(
    config: TuneConfig | TrainConfig | EvaluateConfig,
    *,
    corpus_id: str,
) -> dict[str, object]:
    tuning, tuning_space = _study_definition(config)
    return study_storage_identity_payload(
        chain=config.chain,
        dataset=config.dataset,
        corpus_id=corpus_id,
        dataset_builder=config.dataset_builder,
        feature_set=config.feature_set,
        model=config.model,
        problem=config.problem,
        prediction=config.prediction,
        objective=config.objective,
        study=config.study,
        split=config.split,
        training=config.training,
        tuning=tuning,
        tuning_space=tuning_space,
    )


def artifact_storage_identity_payload_from_config(
    config: TrainConfig | EvaluateConfig,
    *,
    corpus_id: str,
    study_id: str | None,
) -> dict[str, object]:
    payload = {
        "chain": _payload(config.chain),
        "dataset": _payload(config.dataset),
        "corpus_id": corpus_id,
        "dataset_builder": _payload(config.dataset_builder),
        "feature_set": _payload(config.feature_set),
        "model": _payload(config.model),
        "problem": _payload(config.problem),
        "prediction": _payload(config.prediction),
        "objective": _payload(config.objective),
        "split": _payload(config.split),
        "training": _payload(config.training),
        "variant": config.artifact.variant.value,
    }
    if config.artifact.variant is ArtifactVariant.TUNED:
        if study_id is None:
            raise ConfigResolutionError("study_id is required for tuned artifact identity")
        payload["study_id"] = study_id
        payload["study"] = _payload(config.study)
    return payload


def study_request_identity_payload(
    *,
    study_name: str,
    study_id: str | None,
    chain_name: str,
    dataset_id: str,
    dataset_name: str,
    dataset_builder: DatasetBuilderConfig,
    prediction: PredictionConfig,
    objective: ObjectiveConfig,
    problem: ProblemSpec,
    feature_set: FeatureSetConfig,
    model: ModelConfig,
    split: SplitConfig,
    training: TrainingConfig,
    tuning: TuningConfig,
    tuning_space: TuningSpaceConfig,
) -> dict[str, object]:
    return {
        "study_name": study_name,
        "study_id": study_id,
        "dataset_builder": _payload(dataset_builder),
        "prediction": _payload(prediction),
        "objective": _payload(objective),
        "chain_name": chain_name,
        "dataset_id": dataset_id,
        "dataset_name": dataset_name,
        "problem": _payload(problem),
        "feature_set": _payload(feature_set),
        "model": _payload(model),
        "split": _payload(split),
        "training": _payload(training),
        "tuning": _payload(tuning),
        "tuning_space": _payload(tuning_space),
    }


def study_request_identity_payload_from_manifest(manifest: StudyManifest) -> dict[str, object]:
    return study_request_identity_payload(
        study_name=manifest.study_name,
        study_id=manifest.study_id,
        chain_name=manifest.chain_name,
        dataset_id=manifest.dataset_id,
        dataset_name=manifest.dataset_name,
        dataset_builder=manifest.dataset_builder,
        prediction=manifest.prediction,
        objective=manifest.objective,
        problem=manifest.problem,
        feature_set=manifest.feature_set,
        model=manifest.model,
        split=manifest.split,
        training=manifest.training,
        tuning=manifest.tuning,
        tuning_space=manifest.tuning_space,
    )


def study_request_identity_payload_from_tuned_config(
    config: TrainConfig | EvaluateConfig,
    *,
    study_id: str,
    dataset_id: str,
) -> dict[str, object]:
    if config.tuning is None or config.tuning_space is None:
        raise ConfigResolutionError(
            "tuned artifact requests require tuning and tuning_space in the preset"
        )
    return study_request_identity_payload(
        study_name=config.study.name,
        study_id=study_id,
        chain_name=config.chain.name,
        dataset_id=dataset_id,
        dataset_name=config.dataset.name,
        dataset_builder=config.dataset_builder,
        prediction=config.prediction,
        objective=config.objective,
        problem=config.problem,
        feature_set=config.feature_set,
        model=config.model,
        split=config.split,
        training=config.training,
        tuning=config.tuning,
        tuning_space=config.tuning_space,
    )


def study_manifest_identity_payload(manifest: StudyManifest) -> dict[str, object]:
    return {
        **study_request_identity_payload_from_manifest(manifest),
        "sampler_name": manifest.sampler_name,
        "sampler_seed": manifest.sampler_seed,
        "pruner_name": manifest.pruner_name,
        "enable_pruning": manifest.enable_pruning,
    }


def _study_definition(
    config: TuneConfig | TrainConfig | EvaluateConfig,
) -> tuple[TuningConfig, TuningSpaceConfig]:
    if isinstance(config, TuneConfig):
        return config.tuning, config.tuning_space
    if config.tuning is None or config.tuning_space is None:
        raise ConfigResolutionError(
            "tuned artifact requests require tuning and tuning_space in the preset"
        )
    return config.tuning, config.tuning_space
