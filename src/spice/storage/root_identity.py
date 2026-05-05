"""Pure workflow root identity facts."""

from __future__ import annotations

from dataclasses import dataclass

from ..config.models import AcquireConfig, EvaluateConfig, TrainConfig, TuneConfig
from ..core.errors import ConfigResolutionError
from .identity import artifact_storage_identity_from_config, study_storage_identity_from_config
from .ids import artifact_storage_id, corpus_storage_id, study_storage_id


@dataclass(frozen=True, slots=True)
class ConsumedRootFacts:
    dataset_id: str | None = None
    study_id: str | None = None
    artifact_id: str | None = None


@dataclass(frozen=True, slots=True)
class ProducedRootFacts:
    corpus_id: str | None = None
    study_id: str | None = None
    artifact_id: str | None = None


def produced_corpus_id(config: AcquireConfig) -> str:
    return corpus_storage_id(
        chain_name=config.chain.name,
        dataset_name=config.dataset.name,
        evaluation_date=config.dataset.evaluation_date,
    )


def produced_study_id(config: TuneConfig) -> str:
    return study_storage_id(
        identity=study_storage_identity_from_config(config, corpus_id=config.dataset_id)
    )


def produced_artifact_id(config: TrainConfig, *, dataset_id: str) -> str:
    return artifact_storage_id(
        identity=artifact_storage_identity_from_config(
            config,
            corpus_id=dataset_id,
            study_id=config.study_id,
        )
    )


def consumed_root_facts(
    config: TrainConfig | TuneConfig | EvaluateConfig,
) -> ConsumedRootFacts:
    if isinstance(config, TuneConfig):
        return ConsumedRootFacts(dataset_id=config.dataset_id)
    if isinstance(config, TrainConfig):
        return ConsumedRootFacts(dataset_id=config.dataset_id, study_id=config.study_id)
    return ConsumedRootFacts(dataset_id=config.dataset_id, artifact_id=config.artifact_id)


def produced_root_facts(
    config: AcquireConfig | TrainConfig | TuneConfig | EvaluateConfig,
    *,
    dataset_id: str | None = None,
) -> ProducedRootFacts:
    if isinstance(config, AcquireConfig):
        return ProducedRootFacts(corpus_id=produced_corpus_id(config))
    if isinstance(config, TuneConfig):
        return ProducedRootFacts(study_id=produced_study_id(config))
    if isinstance(config, EvaluateConfig):
        return ProducedRootFacts()
    resolved_dataset_id = dataset_id or config.dataset_id
    if resolved_dataset_id is None:
        raise ConfigResolutionError("train produced artifact identity requires dataset_id")
    return ProducedRootFacts(
        artifact_id=produced_artifact_id(config, dataset_id=resolved_dataset_id)
    )
