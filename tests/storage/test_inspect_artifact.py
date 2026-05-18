from __future__ import annotations

from pathlib import Path

from spice.storage.catalog.index import upsert_catalog_record
from spice.storage.catalog.materialization import materialize_catalog_root
from spice.storage.engine import RootKind, ensure_state_db, state_db_path
from spice.storage.inspect_artifact import artifact_local_dependency_warnings
from tests.catalog_helpers import artifact_record, dataset_record


def test_artifact_dependency_warning_reports_missing_dataset(tmp_path: Path) -> None:
    artifact = artifact_record(tmp_path / "outputs" / "artifacts" / "ethereum" / "artifact-1")

    assert artifact_local_dependency_warnings(tmp_path / "outputs", artifact) == (
        "matching local corpus root is missing; local inspection still needs that corpus",
    )


def test_artifact_dependency_warning_accepts_cataloged_dataset_root(tmp_path: Path) -> None:
    storage_root = tmp_path / "outputs"
    artifact = artifact_record(storage_root / "artifacts" / "ethereum" / "artifact-1")
    corpus = dataset_record(
        storage_root / "corpora" / artifact.chain_name / artifact.corpus_id,
        corpus_id=artifact.corpus_id,
        corpus_name=artifact.corpus_name,
        chain_name=artifact.chain_name,
    )
    location = materialize_catalog_root(storage_root, corpus)
    ensure_state_db(state_db_path(location.root_path), root_kind=RootKind.CORPUS, tables=())
    upsert_catalog_record(storage_root, corpus)

    assert artifact_local_dependency_warnings(storage_root, artifact) == ()
