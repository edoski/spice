"""Catalog-record path resolution for workflows that consume existing roots."""

from __future__ import annotations

from pathlib import Path

from ..config.models import ArtifactVariant, EvaluateConfig, TrainConfig, TuneConfig
from .catalog.index import resolve_artifact_record, resolve_dataset_record, resolve_study_record
from .catalog.records import CatalogArtifactRecord, CatalogDatasetRecord, CatalogStudyRecord
from .engine import state_db_path
from .identity import artifact_storage_identity_from_config, study_storage_identity_from_config
from .ids import artifact_storage_id, study_storage_id
from .layout import artifact_root_path, catalog_db_path, study_root_path
from .selectors import ArtifactSelector, DatasetSelector, StudySelector
from .workflow_paths import WorkflowPaths


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


def resolve_tune_consumer_paths(config: TuneConfig) -> WorkflowPaths:
    dataset = resolve_dataset_record(
        config.storage.root,
        selector=DatasetSelector(dataset_id=config.dataset_id),
    )
    study_id = produced_study_id(config)
    return _paths_from_records(
        storage_root=config.storage.root,
        dataset=dataset,
        study_id=study_id,
    )


def resolve_train_consumer_paths(config: TrainConfig) -> WorkflowPaths:
    if config.artifact.variant is ArtifactVariant.TUNED:
        if config.study_id is None:
            raise ValueError("tuned training requires study_id")
        study = resolve_study_record(
            config.storage.root,
            selector=StudySelector(study_id=config.study_id),
        )
        dataset = resolve_dataset_record(
            config.storage.root,
            selector=DatasetSelector(dataset_id=study.dataset_id),
        )
        artifact_id = produced_artifact_id(config, dataset_id=study.dataset_id)
        return _paths_from_records(
            storage_root=config.storage.root,
            dataset=dataset,
            study=study,
            artifact_id=artifact_id,
        )

    if config.dataset_id is None:
        raise ValueError("baseline training requires dataset_id")
    dataset = resolve_dataset_record(
        config.storage.root,
        selector=DatasetSelector(dataset_id=config.dataset_id),
    )
    artifact_id = produced_artifact_id(config, dataset_id=dataset.dataset_id)
    return _paths_from_records(
        storage_root=config.storage.root,
        dataset=dataset,
        artifact_id=artifact_id,
    )


def resolve_evaluate_consumer_paths(config: EvaluateConfig) -> WorkflowPaths:
    dataset = resolve_dataset_record(
        config.storage.root,
        selector=DatasetSelector(dataset_id=config.dataset_id),
    )
    artifact = resolve_artifact_record(
        config.storage.root,
        selector=ArtifactSelector(artifact_id=config.artifact_id),
    )
    return _paths_from_records(
        storage_root=config.storage.root,
        dataset=dataset,
        artifact=artifact,
    )


def _paths_from_records(
    *,
    storage_root: Path,
    dataset: CatalogDatasetRecord,
    study: CatalogStudyRecord | None = None,
    artifact: CatalogArtifactRecord | None = None,
    study_id: str | None = None,
    artifact_id: str | None = None,
) -> WorkflowPaths:
    resolved_study_id = study.study_id if study is not None else study_id
    resolved_artifact_id = artifact.artifact_id if artifact is not None else artifact_id
    study_root = (
        study.root_path
        if study is not None
        else None
        if resolved_study_id is None
        else study_root_path(
            storage_root,
            chain_name=dataset.chain_name,
            study_id=resolved_study_id,
        )
    )
    artifact_root = (
        artifact.root_path
        if artifact is not None
        else None
        if resolved_artifact_id is None
        else artifact_root_path(
            storage_root,
            chain_name=dataset.chain_name,
            artifact_id=resolved_artifact_id,
        )
    )
    return WorkflowPaths(
        output_root=storage_root,
        catalog_db=catalog_db_path(storage_root),
        corpus_id=dataset.dataset_id,
        corpus_root=dataset.root_path,
        history_dir=dataset.root_path / "history",
        evaluation_dir=dataset.root_path / "evaluation",
        corpus_state_db=dataset.state_db_path,
        artifact_id=resolved_artifact_id,
        artifact_root=artifact_root,
        artifact_state_db=None if artifact_root is None else state_db_path(artifact_root),
        study_id=resolved_study_id,
        study_root=study_root,
        study_state_db=None if study_root is None else state_db_path(study_root),
    )
