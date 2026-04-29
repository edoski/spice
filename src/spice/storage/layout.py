"""Pure canonical storage layout helpers."""

from __future__ import annotations

from pathlib import Path

_CATALOG_DB_FILENAME = "catalog.sqlite"
CORPORA_ROOT_NAME = "corpora"
STUDIES_ROOT_NAME = "studies"
ARTIFACTS_ROOT_NAME = "artifacts"
STATE_DIR_NAME = ".spice"


def catalog_db_path(storage_root: Path) -> Path:
    return storage_root / STATE_DIR_NAME / _CATALOG_DB_FILENAME


def corpus_root_path(storage_root: Path, *, chain_name: str, corpus_id: str) -> Path:
    return storage_root / CORPORA_ROOT_NAME / chain_name / corpus_id


def study_root_path(storage_root: Path, *, chain_name: str, study_id: str) -> Path:
    return storage_root / STUDIES_ROOT_NAME / chain_name / study_id


def artifact_root_path(storage_root: Path, *, chain_name: str, artifact_id: str) -> Path:
    return storage_root / ARTIFACTS_ROOT_NAME / chain_name / artifact_id
