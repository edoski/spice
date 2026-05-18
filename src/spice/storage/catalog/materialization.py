"""Catalog record materialization and canonical catalog paths."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...core.errors import StateLayoutError
from ..artifact import load_artifact_manifest
from ..corpus import load_corpus_manifest
from ..engine import RootKind, state_db_path
from ..study_manifest import load_study_manifest
from .records import CatalogArtifactRecord, CatalogCorpusRecord, CatalogRecord, CatalogStudyRecord
from .registry import spec_for_record


@dataclass(frozen=True, slots=True)
class CatalogRootLocation:
    root_path: Path
    state_db_path: Path


def catalog_record_from_root(
    root_path: Path,
    db_path: Path,
    root_kind: RootKind,
) -> CatalogRecord:
    if root_kind is RootKind.CORPUS:
        return _build_dataset_record(root_path, db_path)
    if root_kind is RootKind.STUDY:
        return _build_study_record(root_path, db_path)
    if root_kind is RootKind.ARTIFACT:
        return _build_artifact_record(root_path, db_path)
    raise ValueError(f"Unsupported catalog root kind: {root_kind}")


def materialize_catalog_root(storage_root: Path, record: CatalogRecord) -> CatalogRootLocation:
    root_path = spec_for_record(record).root_path_for_record(storage_root, record)
    return CatalogRootLocation(root_path=root_path, state_db_path=state_db_path(root_path))


def validate_catalog_root_location(
    storage_root: Path,
    *,
    root_path: Path,
    record: CatalogRecord,
) -> None:
    expected = materialize_catalog_root(storage_root, record).root_path.resolve()
    actual = root_path.resolve()
    if actual != expected:
        raise StateLayoutError(
            "Catalog root path does not match manifest identity: "
            f"expected {expected}, got {actual}"
        )


def _build_dataset_record(root_path: Path, db_path: Path) -> CatalogCorpusRecord:
    del root_path
    manifest = load_corpus_manifest(db_path)
    return CatalogCorpusRecord(
        corpus_id=manifest.corpus.id,
        corpus_name=manifest.corpus.name,
        chain_name=manifest.chain.name,
    )


def _build_study_record(root_path: Path, db_path: Path) -> CatalogStudyRecord:
    del root_path
    manifest = load_study_manifest(db_path)
    return CatalogStudyRecord(
        study_id=manifest.study_id,
        study_name=manifest.study_name,
        corpus_id=manifest.corpus_id,
        corpus_name=manifest.corpus_name,
        chain_name=manifest.chain_name,
        features_id=manifest.features.id,
        prediction_id=manifest.prediction.id,
        model_id=manifest.model.id,
        problem_id=manifest.problem.id,
    )


def _build_artifact_record(root_path: Path, db_path: Path) -> CatalogArtifactRecord:
    del root_path
    manifest = load_artifact_manifest(db_path)
    return CatalogArtifactRecord(
        artifact_id=manifest.artifact_id,
        corpus_id=manifest.corpus_id,
        corpus_name=manifest.corpus_name,
        chain_name=manifest.chain_name,
        features_id=manifest.features_id,
        prediction_id=manifest.prediction_id,
        model_id=manifest.model.id,
        problem_id=manifest.problem_id,
        variant=manifest.variant.value,
        study_id=manifest.study_id,
        study_name=None if manifest.study is None else manifest.study.name,
    )
