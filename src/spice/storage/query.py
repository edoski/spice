"""Typed catalog selectors and storage-level resolve/delete helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from ..core.errors import DeleteBlockedError, SelectorResolutionError
from ..core.files import prune_empty_directories, remove_path
from .catalog import (
    CatalogArtifactRecord,
    CatalogDatasetRecord,
    CatalogStudyRecord,
)
from .catalog import (
    delete_artifact_record as _delete_artifact_catalog_record,
)
from .catalog import (
    delete_dataset_record as _delete_dataset_catalog_record,
)
from .catalog import (
    delete_study_record as _delete_study_catalog_record,
)
from .catalog import (
    list_artifact_records as _list_artifact_catalog_records,
)
from .catalog import (
    list_artifacts_for_dataset as _list_artifacts_for_dataset_catalog_records,
)
from .catalog import (
    list_artifacts_for_study as _list_artifacts_for_study_catalog_records,
)
from .catalog import (
    list_dataset_records as _list_dataset_catalog_records,
)
from .catalog import (
    list_studies_for_dataset as _list_studies_for_dataset_catalog_records,
)
from .catalog import (
    list_study_records as _list_study_catalog_records,
)
from .layout import catalog_db_path

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class DatasetSelector:
    chain_name: str | None = None
    dataset_name: str | None = None


@dataclass(frozen=True, slots=True)
class StudySelector:
    chain_name: str | None = None
    dataset_name: str | None = None
    feature_set_id: str | None = None
    model_id: str | None = None
    problem_id: str | None = None
    study_name: str | None = None


@dataclass(frozen=True, slots=True)
class ArtifactSelector:
    chain_name: str | None = None
    dataset_name: str | None = None
    feature_set_id: str | None = None
    model_id: str | None = None
    problem_id: str | None = None
    variant: str | None = None
    study_name: str | None = None


def list_dataset_records(
    storage_root: Path,
    *,
    selector: DatasetSelector | None = None,
) -> list[CatalogDatasetRecord]:
    selector = selector or DatasetSelector()
    return _list_dataset_catalog_records(
        catalog_db_path(storage_root),
        chain_name=selector.chain_name,
        dataset_name=selector.dataset_name,
    )


def list_study_records(
    storage_root: Path,
    *,
    selector: StudySelector | None = None,
) -> list[CatalogStudyRecord]:
    selector = selector or StudySelector()
    return _list_study_catalog_records(
        catalog_db_path(storage_root),
        chain_name=selector.chain_name,
        dataset_name=selector.dataset_name,
        feature_set_id=selector.feature_set_id,
        model_id=selector.model_id,
        problem_id=selector.problem_id,
        study_name=selector.study_name,
    )


def list_artifact_records(
    storage_root: Path,
    *,
    selector: ArtifactSelector | None = None,
) -> list[CatalogArtifactRecord]:
    selector = selector or ArtifactSelector()
    return _list_artifact_catalog_records(
        catalog_db_path(storage_root),
        chain_name=selector.chain_name,
        dataset_name=selector.dataset_name,
        feature_set_id=selector.feature_set_id,
        model_id=selector.model_id,
        problem_id=selector.problem_id,
        variant=selector.variant,
        study_name=selector.study_name,
    )


def list_studies_for_dataset(
    storage_root: Path,
    *,
    dataset_id: str,
) -> list[CatalogStudyRecord]:
    return _list_studies_for_dataset_catalog_records(
        catalog_db_path(storage_root),
        dataset_id=dataset_id,
    )


def list_artifacts_for_dataset(
    storage_root: Path,
    *,
    dataset_id: str,
) -> list[CatalogArtifactRecord]:
    return _list_artifacts_for_dataset_catalog_records(
        catalog_db_path(storage_root),
        dataset_id=dataset_id,
    )


def list_artifacts_for_study(
    storage_root: Path,
    *,
    study_id: str,
) -> list[CatalogArtifactRecord]:
    return _list_artifacts_for_study_catalog_records(
        catalog_db_path(storage_root),
        study_id=study_id,
    )


def resolve_dataset_record(
    storage_root: Path,
    *,
    selector: DatasetSelector | None = None,
) -> CatalogDatasetRecord:
    return _resolve_one("dataset", list_dataset_records(storage_root, selector=selector))


def resolve_study_record(
    storage_root: Path,
    *,
    selector: StudySelector | None = None,
) -> CatalogStudyRecord:
    return _resolve_one("study", list_study_records(storage_root, selector=selector))


def resolve_artifact_record(
    storage_root: Path,
    *,
    selector: ArtifactSelector | None = None,
) -> CatalogArtifactRecord:
    return _resolve_one("artifact", list_artifact_records(storage_root, selector=selector))


def delete_dataset_record(
    storage_root: Path,
    *,
    selector: DatasetSelector | None = None,
    record: CatalogDatasetRecord | None = None,
    cascade: bool = False,
) -> CatalogDatasetRecord:
    record = record or resolve_dataset_record(storage_root, selector=selector)
    dependent_artifacts = list_artifacts_for_dataset(storage_root, dataset_id=record.dataset_id)
    dependent_studies = list_studies_for_dataset(storage_root, dataset_id=record.dataset_id)
    if (dependent_artifacts or dependent_studies) and not cascade:
        raise DeleteBlockedError(
            message="Dataset has dependent studies or artifacts. Re-run with --cascade.",
            artifact_records=dependent_artifacts,
            study_records=dependent_studies,
        )
    for artifact_record in dependent_artifacts:
        _delete_artifact_record(storage_root, artifact_record)
    for study_record in dependent_studies:
        _delete_study_record(storage_root, study_record)
    _delete_dataset_record(storage_root, record)
    return record


def delete_study_record(
    storage_root: Path,
    *,
    selector: StudySelector | None = None,
    record: CatalogStudyRecord | None = None,
    cascade: bool = False,
) -> CatalogStudyRecord:
    record = record or resolve_study_record(storage_root, selector=selector)
    dependent_artifacts = list_artifacts_for_study(storage_root, study_id=record.study_id)
    if dependent_artifacts and not cascade:
        raise DeleteBlockedError(
            message="Study has dependent artifacts. Re-run with --cascade.",
            artifact_records=dependent_artifacts,
        )
    for artifact_record in dependent_artifacts:
        _delete_artifact_record(storage_root, artifact_record)
    _delete_study_record(storage_root, record)
    return record


def delete_artifact_record(
    storage_root: Path,
    *,
    selector: ArtifactSelector | None = None,
    record: CatalogArtifactRecord | None = None,
) -> CatalogArtifactRecord:
    record = record or resolve_artifact_record(storage_root, selector=selector)
    _delete_artifact_record(storage_root, record)
    return record


def _delete_artifact_record(storage_root: Path, record: CatalogArtifactRecord) -> None:
    remove_path(record.root_path)
    _delete_artifact_catalog_record(catalog_db_path(storage_root), artifact_id=record.artifact_id)
    prune_empty_directories(record.root_path.parent, stop_at=storage_root / "artifacts")


def _delete_study_record(storage_root: Path, record: CatalogStudyRecord) -> None:
    remove_path(record.root_path)
    _delete_study_catalog_record(catalog_db_path(storage_root), study_id=record.study_id)
    prune_empty_directories(record.root_path.parent, stop_at=storage_root / "studies")


def _delete_dataset_record(storage_root: Path, record: CatalogDatasetRecord) -> None:
    remove_path(record.root_path)
    _delete_dataset_catalog_record(
        catalog_db_path(storage_root),
        dataset_id=record.dataset_id,
    )
    prune_empty_directories(record.root_path.parent, stop_at=storage_root / "corpora")


def _resolve_one(label: str, records: list[T]) -> T:
    if len(records) == 1:
        return records[0]
    raise SelectorResolutionError(kind=label, records=records)
