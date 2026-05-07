"""Storage-owned workflow root materialization."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..config.models import AcquireConfig, ArtifactVariant, EvaluateConfig, TrainConfig, TuneConfig
from ..core.errors import ConfigResolutionError, SelectorResolutionError
from .catalog.index import (
    resolve_artifact_record,
    resolve_dataset_record,
    resolve_study_record,
)
from .identity import artifact_storage_identity_from_config, study_storage_identity_from_config
from .ids import artifact_storage_id, corpus_storage_id, study_storage_id
from .selectors import ArtifactSelector, DatasetSelector, StudySelector
from .workflow_roots import (
    AcquireWorkflowRoots,
    ArtifactRootHandle,
    BaselineTrainWorkflowRoots,
    CorpusRootHandle,
    EvaluateWorkflowRoots,
    StudyRootHandle,
    TrainWorkflowRoots,
    TunedTrainWorkflowRoots,
    TuneWorkflowRoots,
    artifact_root_handle_from_record,
    corpus_root_handle_from_record,
    produced_artifact_root_handle,
    produced_corpus_root_handle,
    produced_study_root_handle,
    study_root_handle_from_record,
)


@dataclass(frozen=True, slots=True)
class ConsumedRootFacts:
    dataset_id: str | None = None
    study_id: str | None = None
    artifact_id: str | None = None


@dataclass(frozen=True, slots=True)
class ProducedRootFacts:
    dataset_id: str | None = None
    study_id: str | None = None
    artifact_id: str | None = None


@dataclass(frozen=True, slots=True)
class SourceRootFacts:
    artifact_dataset_id: str | None = None


@dataclass(frozen=True, slots=True)
class MaterializedWorkflowRootFacts:
    consumed: ConsumedRootFacts
    produced: ProducedRootFacts
    source: SourceRootFacts = SourceRootFacts()
    consumed_study_dataset_id: str | None = None
    consumed_artifact_dataset_id: str | None = None
    produced_study_dataset_id: str | None = None
    produced_artifact_dataset_id: str | None = None


@dataclass(frozen=True, slots=True)
class _WorkflowRootMaterialization:
    facts: MaterializedWorkflowRootFacts
    corpus: CorpusRootHandle | None = None
    study: StudyRootHandle | None = None
    artifact: ArtifactRootHandle | None = None


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


def materialize_workflow_root_facts(
    config: AcquireConfig | TrainConfig | TuneConfig | EvaluateConfig,
    *,
    known_study_dataset_ids: Mapping[str, str] | None = None,
    known_artifact_dataset_ids: Mapping[str, str] | None = None,
    artifact_source_dataset_id: str | None = None,
) -> MaterializedWorkflowRootFacts:
    return _materialize_workflow_roots(
        config,
        include_handles=False,
        known_study_dataset_ids=known_study_dataset_ids,
        known_artifact_dataset_ids=known_artifact_dataset_ids,
        artifact_source_dataset_id=artifact_source_dataset_id,
    ).facts


def _materialize_workflow_roots(
    config: AcquireConfig | TrainConfig | TuneConfig | EvaluateConfig,
    *,
    include_handles: bool,
    known_study_dataset_ids: Mapping[str, str] | None = None,
    known_artifact_dataset_ids: Mapping[str, str] | None = None,
    artifact_source_dataset_id: str | None = None,
) -> _WorkflowRootMaterialization:
    if isinstance(config, AcquireConfig):
        produced = ProducedRootFacts(dataset_id=produced_corpus_id(config))
        corpus = (
            produced_corpus_root_handle(
                config.storage.root,
                chain_name=config.chain.name,
                dataset_id=_required(
                    produced.dataset_id,
                    "acquire root identity did not produce dataset_id",
                ),
                dataset_name=config.dataset.name,
            )
            if include_handles
            else None
        )
        return _WorkflowRootMaterialization(
            facts=MaterializedWorkflowRootFacts(
                consumed=ConsumedRootFacts(),
                produced=produced,
            ),
            corpus=corpus,
        )

    if isinstance(config, TuneConfig):
        produced = ProducedRootFacts(study_id=produced_study_id(config))
        corpus = None
        study = None
        if include_handles:
            dataset = resolve_dataset_record(
                config.storage.root,
                selector=DatasetSelector(dataset_id=config.dataset_id),
            )
            corpus = corpus_root_handle_from_record(config.storage.root, dataset)
            study = produced_study_root_handle(
                config.storage.root,
                corpus=corpus,
                study_id=_required(
                    produced.study_id,
                    "tune root identity did not produce study_id",
                ),
                study_name=config.study.name,
            )
        return _WorkflowRootMaterialization(
            facts=MaterializedWorkflowRootFacts(
                consumed=ConsumedRootFacts(dataset_id=config.dataset_id),
                produced=produced,
                produced_study_dataset_id=config.dataset_id,
            ),
            corpus=corpus,
            study=study,
        )

    if isinstance(config, TrainConfig):
        if config.artifact.variant is ArtifactVariant.TUNED:
            return _materialize_tuned_train_roots(
                config,
                include_handles=include_handles,
                known_study_dataset_ids=known_study_dataset_ids,
            )
        return _materialize_baseline_train_roots(config, include_handles=include_handles)

    return _materialize_evaluate_roots(
        config,
        include_handles=include_handles,
        known_artifact_dataset_ids=known_artifact_dataset_ids,
        artifact_source_dataset_id=artifact_source_dataset_id,
    )


def _materialize_baseline_train_roots(
    config: TrainConfig,
    *,
    include_handles: bool,
) -> _WorkflowRootMaterialization:
    if config.dataset_id is None:
        raise ValueError("baseline training requires dataset_id")
    produced = ProducedRootFacts(
        artifact_id=produced_artifact_id(config, dataset_id=config.dataset_id)
    )
    corpus = None
    artifact = None
    if include_handles:
        dataset = resolve_dataset_record(
            config.storage.root,
            selector=DatasetSelector(dataset_id=config.dataset_id),
        )
        corpus = corpus_root_handle_from_record(config.storage.root, dataset)
        artifact = produced_artifact_root_handle(
            config.storage.root,
            corpus=corpus,
            artifact_id=_required(
                produced.artifact_id,
                "train root identity did not produce artifact_id",
            ),
            variant=config.artifact.variant,
        )
    return _WorkflowRootMaterialization(
        facts=MaterializedWorkflowRootFacts(
            consumed=ConsumedRootFacts(dataset_id=config.dataset_id),
            produced=produced,
            produced_artifact_dataset_id=config.dataset_id,
        ),
        corpus=corpus,
        artifact=artifact,
    )


def _materialize_tuned_train_roots(
    config: TrainConfig,
    *,
    include_handles: bool,
    known_study_dataset_ids: Mapping[str, str] | None,
) -> _WorkflowRootMaterialization:
    if config.study_id is None:
        raise ValueError("tuned training requires study_id")
    study_record = (
        resolve_study_record(
            config.storage.root,
            selector=StudySelector(study_id=config.study_id),
        )
        if include_handles
        else None
    )
    study_dataset_id = (
        study_record.dataset_id
        if study_record is not None
        else _known_or_catalog_study_dataset_id(
            config,
            config.study_id,
            known_study_dataset_ids=known_study_dataset_ids,
        )
    )
    produced = ProducedRootFacts(
        artifact_id=produced_artifact_id(config, dataset_id=study_dataset_id)
    )
    corpus = None
    study = None
    artifact = None
    if include_handles:
        if study_record is None:
            raise ValueError("tuned train study record was not resolved")
        dataset = resolve_dataset_record(
            config.storage.root,
            selector=DatasetSelector(dataset_id=study_dataset_id),
        )
        corpus = corpus_root_handle_from_record(config.storage.root, dataset)
        study = study_root_handle_from_record(config.storage.root, study_record)
        artifact = produced_artifact_root_handle(
            config.storage.root,
            corpus=corpus,
            artifact_id=_required(
                produced.artifact_id,
                "train root identity did not produce artifact_id",
            ),
            variant=config.artifact.variant,
            study=study,
        )
    return _WorkflowRootMaterialization(
        facts=MaterializedWorkflowRootFacts(
            consumed=ConsumedRootFacts(study_id=config.study_id),
            produced=produced,
            consumed_study_dataset_id=study_dataset_id,
            produced_artifact_dataset_id=study_dataset_id,
        ),
        corpus=corpus,
        study=study,
        artifact=artifact,
    )


def _materialize_evaluate_roots(
    config: EvaluateConfig,
    *,
    include_handles: bool,
    known_artifact_dataset_ids: Mapping[str, str] | None,
    artifact_source_dataset_id: str | None,
) -> _WorkflowRootMaterialization:
    artifact_record = (
        resolve_artifact_record(
            config.storage.root,
            selector=ArtifactSelector(artifact_id=config.artifact_id),
        )
        if include_handles
        else None
    )
    artifact_dataset_id = (
        artifact_record.dataset_id
        if artifact_record is not None
        else _known_or_catalog_artifact_dataset_id(
            config,
            config.artifact_id,
            known_artifact_dataset_ids=known_artifact_dataset_ids,
            artifact_source_dataset_id=artifact_source_dataset_id,
        )
    )
    corpus = None
    artifact = None
    if include_handles:
        dataset = resolve_dataset_record(
            config.storage.root,
            selector=DatasetSelector(dataset_id=config.dataset_id),
        )
        if artifact_record is None:
            raise ValueError("evaluate artifact record was not resolved")
        corpus = corpus_root_handle_from_record(config.storage.root, dataset)
        artifact = artifact_root_handle_from_record(config.storage.root, artifact_record)
    return _WorkflowRootMaterialization(
        facts=MaterializedWorkflowRootFacts(
            consumed=ConsumedRootFacts(
                dataset_id=config.dataset_id,
                artifact_id=config.artifact_id,
            ),
            produced=ProducedRootFacts(),
            source=SourceRootFacts(artifact_dataset_id=artifact_source_dataset_id),
            consumed_artifact_dataset_id=artifact_dataset_id,
        ),
        corpus=corpus,
        artifact=artifact,
    )


def _known_or_catalog_study_dataset_id(
    config: TrainConfig,
    study_id: str,
    *,
    known_study_dataset_ids: Mapping[str, str] | None,
) -> str:
    if known_study_dataset_ids is not None and study_id in known_study_dataset_ids:
        return known_study_dataset_ids[study_id]
    try:
        study = resolve_study_record(
            config.storage.root,
            selector=StudySelector(study_id=study_id),
        )
    except SelectorResolutionError as exc:
        raise ConfigResolutionError(str(exc)) from exc
    return study.dataset_id


def _known_or_catalog_artifact_dataset_id(
    config: EvaluateConfig,
    artifact_id: str,
    *,
    known_artifact_dataset_ids: Mapping[str, str] | None,
    artifact_source_dataset_id: str | None,
) -> str:
    if artifact_source_dataset_id is not None:
        return artifact_source_dataset_id
    if known_artifact_dataset_ids is not None and artifact_id in known_artifact_dataset_ids:
        return known_artifact_dataset_ids[artifact_id]
    try:
        artifact = resolve_artifact_record(
            config.storage.root,
            selector=ArtifactSelector(artifact_id=artifact_id),
        )
    except SelectorResolutionError as exc:
        raise ConfigResolutionError(str(exc)) from exc
    return artifact.dataset_id


def _required(value: str | None, message: str) -> str:
    if value is None:
        raise ValueError(message)
    return value


def materialize_acquire_roots(config: AcquireConfig) -> AcquireWorkflowRoots:
    materialized = _materialize_workflow_roots(config, include_handles=True)
    corpus = materialized.corpus
    if corpus is None:
        raise ValueError("acquire root identity did not produce corpus root")
    return AcquireWorkflowRoots(
        corpus=corpus,
    )


def materialize_tune_roots(config: TuneConfig) -> TuneWorkflowRoots:
    materialized = _materialize_workflow_roots(config, include_handles=True)
    corpus = materialized.corpus
    study = materialized.study
    if corpus is None or study is None:
        raise ValueError("tune root identity did not produce workflow roots")
    return TuneWorkflowRoots(
        corpus=corpus,
        study=study,
    )


def materialize_train_roots(config: TrainConfig) -> TrainWorkflowRoots:
    materialized = _materialize_workflow_roots(config, include_handles=True)
    corpus = materialized.corpus
    artifact = materialized.artifact
    if corpus is None or artifact is None:
        raise ValueError("train root identity did not produce workflow roots")
    if config.artifact.variant is ArtifactVariant.TUNED:
        study = materialized.study
        if study is None:
            raise ValueError("tuned train root identity did not produce study root")
        return TunedTrainWorkflowRoots(
            corpus=corpus,
            study=study,
            artifact=artifact,
        )
    return BaselineTrainWorkflowRoots(
        corpus=corpus,
        artifact=artifact,
    )


def materialize_evaluate_roots(config: EvaluateConfig) -> EvaluateWorkflowRoots:
    materialized = _materialize_workflow_roots(config, include_handles=True)
    corpus = materialized.corpus
    artifact = materialized.artifact
    if corpus is None or artifact is None:
        raise ValueError("evaluate root identity did not produce workflow roots")
    return EvaluateWorkflowRoots(
        corpus=corpus,
        artifact=artifact,
    )
