"""Catalog rebuild and root-level reindex helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from .artifact import load_artifact_manifest
from .catalog import (
    ensure_catalog_db,
    upsert_artifact_record,
    upsert_dataset_record,
    upsert_study_record,
)
from .corpus import load_dataset_manifest
from .engine import RootKind, detect_root_kind, state_db_path
from .layout import catalog_db_path
from .study_manifest import load_study_manifest


@dataclass(frozen=True, slots=True)
class CatalogRefreshSummary:
    dataset_roots: int = 0
    study_roots: int = 0
    artifact_roots: int = 0


def reindex_root(storage_root: Path, *, root_path: Path) -> RootKind:
    return upsert_root_record(catalog_db_path(storage_root), root_path=root_path)


def refresh_catalog(storage_root: Path) -> CatalogRefreshSummary:
    catalog_path = catalog_db_path(storage_root)
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    temp_catalog_path = catalog_path.parent / f".{catalog_path.name}.rebuild.{uuid4().hex}.tmp"
    if temp_catalog_path.exists():
        temp_catalog_path.unlink()
    summary = CatalogRefreshSummary()
    try:
        ensure_catalog_db(temp_catalog_path)
        for root_path in _dataset_roots(storage_root):
            upsert_root_record(temp_catalog_path, root_path=root_path)
            summary = CatalogRefreshSummary(
                dataset_roots=summary.dataset_roots + 1,
                study_roots=summary.study_roots,
                artifact_roots=summary.artifact_roots,
            )
        for root_path in _study_roots(storage_root):
            upsert_root_record(temp_catalog_path, root_path=root_path)
            summary = CatalogRefreshSummary(
                dataset_roots=summary.dataset_roots,
                study_roots=summary.study_roots + 1,
                artifact_roots=summary.artifact_roots,
            )
        for root_path in _artifact_roots(storage_root):
            upsert_root_record(temp_catalog_path, root_path=root_path)
            summary = CatalogRefreshSummary(
                dataset_roots=summary.dataset_roots,
                study_roots=summary.study_roots,
                artifact_roots=summary.artifact_roots + 1,
            )
        os.replace(temp_catalog_path, catalog_path)
        return summary
    except Exception:
        temp_catalog_path.unlink(missing_ok=True)
        raise


def upsert_root_record(catalog_path: Path, *, root_path: Path) -> RootKind:
    db_path = state_db_path(root_path)
    root_kind = detect_root_kind(db_path)
    if root_kind is RootKind.CORPUS:
        manifest = load_dataset_manifest(db_path)
        upsert_dataset_record(
            catalog_path,
            dataset_id=manifest.dataset.id,
            dataset_name=manifest.dataset.name,
            chain_name=manifest.chain.name,
            root_path=root_path,
            state_db_path=db_path,
        )
        return root_kind
    if root_kind is RootKind.STUDY:
        manifest = load_study_manifest(db_path)
        upsert_study_record(
            catalog_path,
            study_id=manifest.study_id,
            study_name=manifest.study_name,
            dataset_id=manifest.dataset_id,
            dataset_name=manifest.dataset_name,
            chain_name=manifest.chain_name,
            feature_set_id=manifest.feature_set.id,
            prediction_id=manifest.prediction.id,
            model_id=manifest.model.id,
            problem_id=manifest.problem.id,
            root_path=root_path,
            state_db_path=db_path,
        )
        return root_kind
    manifest = load_artifact_manifest(db_path)
    upsert_artifact_record(
        catalog_path,
        artifact_id=manifest.artifact_id,
        dataset_id=manifest.dataset_id,
        dataset_name=manifest.dataset_name,
        chain_name=manifest.chain.name,
        feature_set_id=manifest.feature_set_id,
        prediction_id=manifest.prediction_id,
        model_id=manifest.model.id,
        problem_id=manifest.problem_id,
        variant=manifest.variant.value,
        study_id=manifest.study_id,
        study_name=None if manifest.study is None else manifest.study.name,
        root_path=root_path,
        state_db_path=db_path,
    )
    return root_kind


def _dataset_roots(storage_root: Path) -> list[Path]:
    return _roots_under(storage_root / "corpora")


def _study_roots(storage_root: Path) -> list[Path]:
    return _roots_under(storage_root / "studies")


def _artifact_roots(storage_root: Path) -> list[Path]:
    return _roots_under(storage_root / "artifacts")


def _roots_under(parent: Path) -> list[Path]:
    if not parent.exists():
        return []
    roots: list[Path] = []
    chain_dirs = sorted(
        path
        for path in parent.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    )
    for chain_dir in chain_dirs:
        for root_dir in sorted(
            path for path in chain_dir.iterdir() if path.is_dir() and not path.name.startswith(".")
        ):
            if state_db_path(root_dir).is_file():
                roots.append(root_dir)
    return roots
