from __future__ import annotations

import pytest

from spice.core.errors import StateLayoutError
from spice.storage.catalog import CatalogArtifactRecord, list_artifact_records
from spice.storage.catalog.store import upsert_artifact_record
from spice.storage.engine import RootKind, ensure_state_db, state_db_path
from spice.storage.layout import catalog_db_path
from spice.storage.roots import _delete_artifact_record


def _artifact_record(root_path):
    return CatalogArtifactRecord(
        artifact_id="art_1",
        dataset_id="cor_1",
        dataset_name="dataset",
        chain_name="ethereum",
        feature_set_id="features",
        prediction_id="prediction",
        model_id="model",
        problem_id="problem",
        variant="baseline",
        study_id=None,
        study_name=None,
        root_path=root_path,
        state_db_path=state_db_path(root_path),
    )


def test_delete_artifact_rejects_catalog_path_outside_storage_root(tmp_path) -> None:
    storage_root = tmp_path / "outputs"
    outside_root = tmp_path / "outside-artifact"
    outside_root.mkdir()

    with pytest.raises(StateLayoutError, match="outside storage artifacts root"):
        _delete_artifact_record(storage_root, _artifact_record(outside_root))

    assert outside_root.exists()


def test_delete_artifact_rejects_catalog_root_kind_mismatch(tmp_path) -> None:
    storage_root = tmp_path / "outputs"
    artifact_root = storage_root / "artifacts" / "ethereum" / "art_1"
    ensure_state_db(state_db_path(artifact_root), root_kind=RootKind.STUDY, tables=())

    with pytest.raises(StateLayoutError, match="Catalog root kind mismatch"):
        _delete_artifact_record(storage_root, _artifact_record(artifact_root))

    assert artifact_root.exists()


def test_delete_artifact_rejects_catalog_root_without_state_db(tmp_path) -> None:
    storage_root = tmp_path / "outputs"
    artifact_root = storage_root / "artifacts" / "ethereum" / "art_1"
    artifact_root.mkdir(parents=True)

    with pytest.raises(StateLayoutError, match="missing state DB"):
        _delete_artifact_record(storage_root, _artifact_record(artifact_root))

    assert artifact_root.exists()


def test_delete_artifact_keeps_catalog_record_when_filesystem_delete_fails(
    tmp_path,
    monkeypatch,
) -> None:
    storage_root = tmp_path / "outputs"
    artifact_root = storage_root / "artifacts" / "ethereum" / "art_1"
    ensure_state_db(state_db_path(artifact_root), root_kind=RootKind.ARTIFACT, tables=())
    record = _artifact_record(artifact_root)
    catalog_path = catalog_db_path(storage_root)
    upsert_artifact_record(
        catalog_path,
        artifact_id=record.artifact_id,
        dataset_id=record.dataset_id,
        dataset_name=record.dataset_name,
        chain_name=record.chain_name,
        feature_set_id=record.feature_set_id,
        prediction_id=record.prediction_id,
        model_id=record.model_id,
        problem_id=record.problem_id,
        variant=record.variant,
        study_id=record.study_id,
        study_name=record.study_name,
        root_path=record.root_path,
        state_db_path=record.state_db_path,
    )

    def fail_remove_path(path) -> None:
        del path
        raise OSError("delete failed")

    monkeypatch.setattr("spice.storage.roots.remove_path", fail_remove_path)

    with pytest.raises(OSError, match="delete failed"):
        _delete_artifact_record(storage_root, record)

    records = list_artifact_records(catalog_path)
    assert [stored.artifact_id for stored in records] == [record.artifact_id]
