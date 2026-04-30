"""Typed canonical provenance identities for storage and study validation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, SerializeAsAny

from ..config.models import (
    ArtifactVariant,
    FeaturesConfig,
    PredictionConfig,
    ProblemSpec,
    SplitConfig,
    StudyConfig,
    TrainConfig,
    TrainingConfig,
    TuneConfig,
    TuningConfig,
    TuningSearchConfig,
    TuningSpaceConfig,
)
from ..core.errors import ConfigResolutionError
from ..modeling.dataset_builders import DatasetBuilderConfig
from ..modeling.families.base import ModelConfig
from ..objectives import ObjectiveConfig
from .study_models import StudyManifest


class IdentityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class StudyStorageIdentity(IdentityModel):
    corpus_id: str
    dataset_builder: SerializeAsAny[DatasetBuilderConfig]
    features: FeaturesConfig
    model: SerializeAsAny[ModelConfig]
    problem: ProblemSpec
    prediction: PredictionConfig
    objective: ObjectiveConfig
    study: StudyConfig
    split: SplitConfig
    training: TrainingConfig
    tuning: TuningSearchConfig
    tuning_space: TuningSpaceConfig


class ArtifactStorageIdentity(IdentityModel):
    corpus_id: str
    dataset_builder: SerializeAsAny[DatasetBuilderConfig]
    features: FeaturesConfig
    model: SerializeAsAny[ModelConfig]
    problem: ProblemSpec
    prediction: PredictionConfig
    objective: ObjectiveConfig
    split: SplitConfig
    training: TrainingConfig
    variant: ArtifactVariant
    study_id: str | None = None
    study: StudyConfig | None = None


class StudyDefinitionIdentity(IdentityModel):
    study_name: str
    study_id: str | None
    chain_name: str
    dataset_id: str
    dataset_name: str
    dataset_builder: SerializeAsAny[DatasetBuilderConfig]
    prediction: PredictionConfig
    objective: ObjectiveConfig
    problem: ProblemSpec
    features: FeaturesConfig
    model: SerializeAsAny[ModelConfig]
    split: SplitConfig
    training: TrainingConfig
    tuning: TuningSearchConfig
    tuning_space: TuningSpaceConfig


class StudyManifestIdentity(IdentityModel):
    definition: StudyDefinitionIdentity
    sampler_name: str
    sampler_seed: int
    pruner_name: str
    enable_pruning: bool


def identity_payload(identity: IdentityModel) -> dict[str, object]:
    payload = identity.model_dump(mode="json", exclude_none=True)
    if not isinstance(payload, dict):
        raise TypeError("identity must serialize to a mapping payload")
    return payload


def study_storage_identity(
    *,
    corpus_id: str,
    dataset_builder: DatasetBuilderConfig,
    features: FeaturesConfig,
    model: ModelConfig,
    problem: ProblemSpec,
    prediction: PredictionConfig,
    objective: ObjectiveConfig,
    study: StudyConfig,
    split: SplitConfig,
    training: TrainingConfig,
    tuning: TuningSearchConfig,
    tuning_space: TuningSpaceConfig,
) -> StudyStorageIdentity:
    return StudyStorageIdentity(
        corpus_id=corpus_id,
        dataset_builder=dataset_builder,
        features=features,
        model=model,
        problem=problem,
        prediction=prediction,
        objective=objective,
        study=study,
        split=split,
        training=training,
        tuning=tuning,
        tuning_space=tuning_space,
    )


def study_storage_identity_from_config(
    config: TuneConfig | TrainConfig,
    *,
    corpus_id: str,
) -> StudyStorageIdentity:
    tuning, tuning_space = _study_definition(config)
    return study_storage_identity(
        corpus_id=corpus_id,
        dataset_builder=config.dataset_builder,
        features=config.features,
        model=config.model,
        problem=config.problem,
        prediction=config.prediction,
        objective=config.objective,
        study=config.study,
        split=config.split,
        training=config.training,
        tuning=tuning.search,
        tuning_space=tuning_space,
    )


def artifact_storage_identity_from_config(
    config: TrainConfig,
    *,
    corpus_id: str,
    study_id: str | None,
) -> ArtifactStorageIdentity:
    if config.artifact.variant is ArtifactVariant.TUNED and study_id is None:
        raise ConfigResolutionError("study_id is required for tuned artifact identity")
    return ArtifactStorageIdentity(
        corpus_id=corpus_id,
        dataset_builder=config.dataset_builder,
        features=config.features,
        model=config.model,
        problem=config.problem,
        prediction=config.prediction,
        objective=config.objective,
        split=config.split,
        training=config.training,
        variant=config.artifact.variant,
        study_id=study_id,
        study=config.study if config.artifact.variant is ArtifactVariant.TUNED else None,
    )


def study_definition_identity(
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
    features: FeaturesConfig,
    model: ModelConfig,
    split: SplitConfig,
    training: TrainingConfig,
    tuning: TuningSearchConfig,
    tuning_space: TuningSpaceConfig,
) -> StudyDefinitionIdentity:
    return StudyDefinitionIdentity(
        study_name=study_name,
        study_id=study_id,
        chain_name=chain_name,
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        dataset_builder=dataset_builder,
        prediction=prediction,
        objective=objective,
        problem=problem,
        features=features,
        model=model,
        split=split,
        training=training,
        tuning=tuning,
        tuning_space=tuning_space,
    )


def study_definition_identity_from_manifest(manifest: StudyManifest) -> StudyDefinitionIdentity:
    return study_definition_identity(
        study_name=manifest.study_name,
        study_id=manifest.study_id,
        chain_name=manifest.chain_name,
        dataset_id=manifest.dataset_id,
        dataset_name=manifest.dataset_name,
        dataset_builder=manifest.dataset_builder,
        prediction=manifest.prediction,
        objective=manifest.objective,
        problem=manifest.problem,
        features=manifest.features,
        model=manifest.model,
        split=manifest.split,
        training=manifest.training,
        tuning=manifest.tuning,
        tuning_space=manifest.tuning_space,
    )


def study_definition_identity_from_tuned_config(
    config: TrainConfig,
    *,
    study_id: str,
    chain_name: str,
    dataset_id: str,
    dataset_name: str,
) -> StudyDefinitionIdentity:
    if config.tuning is None or config.tuning_space is None:
        raise ConfigResolutionError(
            "tuned artifact definitions require tuning and tuning_space in the surface"
        )
    return study_definition_identity(
        study_name=config.study.name,
        study_id=study_id,
        chain_name=chain_name,
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        dataset_builder=config.dataset_builder,
        prediction=config.prediction,
        objective=config.objective,
        problem=config.problem,
        features=config.features,
        model=config.model,
        split=config.split,
        training=config.training,
        tuning=config.tuning.search,
        tuning_space=config.tuning_space,
    )


def study_manifest_identity(manifest: StudyManifest) -> StudyManifestIdentity:
    return StudyManifestIdentity(
        definition=study_definition_identity_from_manifest(manifest),
        sampler_name=manifest.sampler_name,
        sampler_seed=manifest.sampler_seed,
        pruner_name=manifest.pruner_name,
        enable_pruning=manifest.enable_pruning,
    )


def _study_definition(
    config: TuneConfig | TrainConfig,
) -> tuple[TuningConfig, TuningSpaceConfig]:
    if isinstance(config, TuneConfig):
        return config.tuning, config.tuning_space
    if config.tuning is None or config.tuning_space is None:
        raise ConfigResolutionError(
            "tuned artifact definitions require tuning and tuning_space in the surface"
        )
    return config.tuning, config.tuning_space
