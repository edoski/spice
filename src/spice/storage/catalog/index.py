"""Derived catalog index service for storage roots."""

from __future__ import annotations

import os
from dataclasses import dataclass, fields
from pathlib import Path
from typing import TypeVar
from uuid import uuid4

from ...core.errors import SelectorResolutionError
from ..engine import RootKind, detect_root_kind, state_db_path
from ..layout import catalog_db_path
from ..selectors import ArtifactSelector, DatasetSelector, StudySelector
from .records import CatalogArtifactRecord, CatalogDatasetRecord, CatalogRecord, CatalogStudyRecord
from .registry import (
    ARTIFACT_ROOT_SPEC,
    DATASET_ROOT_SPEC,
    STUDY_ROOT_SPEC,
    CatalogRootKindSpec,
    ensure_catalog_db,
    spec_for_root_kind,
)

T = TypeVar("T", bound=CatalogRecord)
SelectorT = TypeVar("SelectorT", DatasetSelector, StudySelector, ArtifactSelector)


@dataclass(frozen=True, slots=True)
class CatalogRefreshSummary:
    dataset_roots: int = 0
    study_roots: int = 0
    artifact_roots: int = 0


@dataclass(frozen=True, slots=True)
class ReindexedCatalogRoot:
    root_kind: RootKind
    record: CatalogRecord


def list_dataset_records(
    storage_root: Path,
    *,
    selector: DatasetSelector | None = None,
) -> list[CatalogDatasetRecord]:
    return _list_catalog_records(
        storage_root,
        selector=selector or DatasetSelector(),
        spec=DATASET_ROOT_SPEC,
    )


def list_study_records(
    storage_root: Path,
    *,
    selector: StudySelector | None = None,
) -> list[CatalogStudyRecord]:
    return _list_catalog_records(
        storage_root,
        selector=selector or StudySelector(),
        spec=STUDY_ROOT_SPEC,
    )


def list_artifact_records(
    storage_root: Path,
    *,
    selector: ArtifactSelector | None = None,
) -> list[CatalogArtifactRecord]:
    return _list_catalog_records(
        storage_root,
        selector=selector or ArtifactSelector(),
        spec=ARTIFACT_ROOT_SPEC,
    )


def list_studies_for_dataset(
    storage_root: Path,
    *,
    dataset_id: str,
) -> list[CatalogStudyRecord]:
    return STUDY_ROOT_SPEC.list_records(
        catalog_db_path(storage_root),
        filters={"dataset_id": dataset_id},
        order_by=("study_name",),
    )


def list_artifacts_for_dataset(
    storage_root: Path,
    *,
    dataset_id: str,
) -> list[CatalogArtifactRecord]:
    return ARTIFACT_ROOT_SPEC.list_records(
        catalog_db_path(storage_root),
        filters={"dataset_id": dataset_id},
        order_by=("variant", "model_id"),
    )


def list_artifacts_for_study(
    storage_root: Path,
    *,
    study_id: str,
) -> list[CatalogArtifactRecord]:
    return ARTIFACT_ROOT_SPEC.list_records(
        catalog_db_path(storage_root),
        filters={"study_id": study_id},
        order_by=("variant", "model_id"),
    )


def resolve_dataset_record(
    storage_root: Path,
    *,
    selector: DatasetSelector | None = None,
) -> CatalogDatasetRecord:
    return _resolve_catalog_record(
        "dataset",
        storage_root,
        selector=selector or DatasetSelector(),
        spec=DATASET_ROOT_SPEC,
    )


def resolve_study_record(
    storage_root: Path,
    *,
    selector: StudySelector | None = None,
) -> CatalogStudyRecord:
    return _resolve_catalog_record(
        "study",
        storage_root,
        selector=selector or StudySelector(),
        spec=STUDY_ROOT_SPEC,
    )


def resolve_artifact_record(
    storage_root: Path,
    *,
    selector: ArtifactSelector | None = None,
) -> CatalogArtifactRecord:
    return _resolve_catalog_record(
        "artifact",
        storage_root,
        selector=selector or ArtifactSelector(),
        spec=ARTIFACT_ROOT_SPEC,
    )


def reindex_catalog_root(storage_root: Path, *, root_path: Path) -> ReindexedCatalogRoot:
    return _reindex_catalog_root(catalog_db_path(storage_root), root_path=root_path)


def refresh_catalog(storage_root: Path) -> CatalogRefreshSummary:
    catalog_path = catalog_db_path(storage_root)
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    temp_catalog_path = catalog_path.parent / f".{catalog_path.name}.rebuild.{uuid4().hex}.tmp"
    if temp_catalog_path.exists():
        temp_catalog_path.unlink()
    try:
        ensure_catalog_db(temp_catalog_path)
        counts = {"dataset_roots": 0, "study_roots": 0, "artifact_roots": 0}
        for spec, count_key in (
            (DATASET_ROOT_SPEC, "dataset_roots"),
            (STUDY_ROOT_SPEC, "study_roots"),
            (ARTIFACT_ROOT_SPEC, "artifact_roots"),
        ):
            for root_path in _roots_under(storage_root / spec.parent_name):
                _reindex_catalog_root(temp_catalog_path, root_path=root_path)
                counts[count_key] += 1
        os.replace(temp_catalog_path, catalog_path)
        return CatalogRefreshSummary(**counts)
    except Exception:
        temp_catalog_path.unlink(missing_ok=True)
        raise


def _reindex_catalog_root(catalog_path: Path, *, root_path: Path) -> ReindexedCatalogRoot:
    db_path = state_db_path(root_path)
    root_kind = detect_root_kind(db_path)
    spec = spec_for_root_kind(root_kind)
    record = spec.manifest_to_record(root_path, db_path)
    spec.upsert(catalog_path, record)
    return ReindexedCatalogRoot(root_kind=root_kind, record=record)


def _roots_under(parent: Path) -> list[Path]:
    if not parent.exists():
        return []
    roots: list[Path] = []
    chain_dirs = sorted(
        path for path in parent.iterdir() if path.is_dir() and not path.name.startswith(".")
    )
    for chain_dir in chain_dirs:
        for root_dir in sorted(
            path for path in chain_dir.iterdir() if path.is_dir() and not path.name.startswith(".")
        ):
            if state_db_path(root_dir).is_file():
                roots.append(root_dir)
    return roots


def _resolve_one(label: str, records: list[T]) -> T:
    if len(records) == 1:
        return records[0]
    raise SelectorResolutionError(kind=label, records=records)


def _selector_kwargs(selector: SelectorT) -> dict[str, str | None]:
    return {
        field.name: value
        for field in fields(selector)
        if (value := getattr(selector, field.name)) is not None
    }


def _list_catalog_records(
    storage_root: Path,
    *,
    selector: SelectorT,
    spec: CatalogRootKindSpec[T],
) -> list[T]:
    return spec.list_records(catalog_db_path(storage_root), filters=_selector_kwargs(selector))


def _resolve_catalog_record(
    label: str,
    storage_root: Path,
    *,
    selector: SelectorT,
    spec: CatalogRootKindSpec[T],
) -> T:
    return _resolve_one(
        label,
        _list_catalog_records(storage_root, selector=selector, spec=spec),
    )
