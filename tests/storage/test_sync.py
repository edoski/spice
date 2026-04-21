from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from spice.core.errors import StateConflictError
from spice.storage.catalog import CatalogArtifactRecord, CatalogStudyRecord
from spice.storage.roots import ArtifactSelector, StudySelector
from spice.storage.sync import pull_artifact_from_cluster, push_study_to_cluster


def _target(remote_storage_root: Path) -> SimpleNamespace:
    return SimpleNamespace(
        spec=SimpleNamespace(paths=SimpleNamespace(storage_root=remote_storage_root))
    )


def _study_record(root_path: Path) -> CatalogStudyRecord:
    return CatalogStudyRecord(
        study_id="study-1",
        study_name="default",
        dataset_id="dataset-1",
        dataset_name="icdcs_2026",
        chain_name="ethereum",
        feature_set_id="icdcs_2026",
        prediction_id="candidate_offset_selection",
        model_id="lstm",
        problem_id="icdcs_2026",
        root_path=root_path,
        state_db_path=root_path / ".spice" / "state.sqlite",
    )


def _artifact_record(root_path: Path) -> CatalogArtifactRecord:
    return CatalogArtifactRecord(
        artifact_id="artifact-1",
        dataset_id="dataset-1",
        dataset_name="icdcs_2026",
        chain_name="ethereum",
        feature_set_id="icdcs_2026",
        prediction_id="candidate_offset_selection",
        model_id="lstm",
        problem_id="icdcs_2026",
        variant="baseline",
        study_id=None,
        study_name=None,
        root_path=root_path,
        state_db_path=root_path / ".spice" / "state.sqlite",
    )


def test_push_study_to_cluster_uses_canonical_destination_root(tmp_path, monkeypatch) -> None:
    local_storage_root = tmp_path / "outputs"
    record = _study_record(local_storage_root / "studies" / "ethereum" / "study-1")
    record.root_path.mkdir(parents=True)
    remote_storage_root = tmp_path / "remote-storage"
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "spice.storage.sync.load_execution_target", lambda: _target(remote_storage_root)
    )
    monkeypatch.setattr(
        "spice.storage.sync.resolve_study_record",
        lambda _root, *, selector: record,
    )
    monkeypatch.setattr(
        "spice.storage.sync._prepare_cluster_stage",
        lambda _target, *, destination_root, staged_root, replace: captured.update(
            {
                "destination_root": destination_root,
                "staged_root": staged_root,
                "replace": replace,
            }
        ),
    )
    monkeypatch.setattr(
        "spice.storage.sync.run_rsync_to_execution_target", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        "spice.storage.sync._finalize_cluster_stage",
        lambda *_args, **_kwargs: None,
    )

    pushed = push_study_to_cluster(
        storage_root=local_storage_root,
        selector=StudySelector(
            chain_name=record.chain_name,
            dataset_name=record.dataset_name,
            feature_set_id=record.feature_set_id,
            prediction_id=record.prediction_id,
            model_id=record.model_id,
            problem_id=record.problem_id,
            study_name=record.study_name,
        ),
        replace=False,
    )

    assert pushed == record
    assert captured["destination_root"] == (
        remote_storage_root / "studies" / record.chain_name / record.study_id
    )
    assert captured["replace"] is False


def test_pull_artifact_from_cluster_promotes_and_reindexes(tmp_path, monkeypatch) -> None:
    remote_root = tmp_path / "remote-storage" / "artifacts" / "ethereum" / "artifact-1"
    remote_root.mkdir(parents=True)
    (remote_root / "payload.txt").write_text("artifact payload", encoding="utf-8")
    record = _artifact_record(remote_root)
    local_storage_root = tmp_path / "local-outputs"
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "spice.storage.sync.load_execution_target", lambda: _target(tmp_path / "remote-storage")
    )
    monkeypatch.setattr(
        "spice.storage.sync._resolve_cluster_artifact_record",
        lambda _target, *, selector: record,
    )
    monkeypatch.setattr(
        "spice.storage.sync.run_rsync_from_execution_target",
        lambda _target, *, source_root, destination_root: shutil.copytree(
            source_root,
            destination_root,
            dirs_exist_ok=True,
        ),
    )
    monkeypatch.setattr(
        "spice.storage.sync.reindex_root",
        lambda storage_root, *, root_path: captured.update(
            {"storage_root": storage_root, "root_path": root_path}
        ),
    )

    pulled, dataset_present = pull_artifact_from_cluster(
        storage_root=local_storage_root,
        selector=ArtifactSelector(
            chain_name=record.chain_name,
            dataset_name=record.dataset_name,
            feature_set_id=record.feature_set_id,
            prediction_id=record.prediction_id,
            model_id=record.model_id,
            problem_id=record.problem_id,
            variant=record.variant,
        ),
        replace=False,
    )

    destination_root = local_storage_root / "artifacts" / record.chain_name / record.artifact_id
    assert pulled == record
    assert dataset_present is False
    assert (destination_root / "payload.txt").read_text(encoding="utf-8") == "artifact payload"
    assert captured == {
        "storage_root": local_storage_root,
        "root_path": destination_root,
    }


def test_pull_artifact_from_cluster_rejects_existing_destination(tmp_path, monkeypatch) -> None:
    record = _artifact_record(tmp_path / "remote-storage" / "artifacts" / "ethereum" / "artifact-1")
    destination_root = tmp_path / "outputs" / "artifacts" / record.chain_name / record.artifact_id
    destination_root.mkdir(parents=True)

    monkeypatch.setattr(
        "spice.storage.sync.load_execution_target", lambda: _target(tmp_path / "remote-storage")
    )
    monkeypatch.setattr(
        "spice.storage.sync._resolve_cluster_artifact_record",
        lambda _target, *, selector: record,
    )

    with pytest.raises(StateConflictError, match="Destination already exists"):
        pull_artifact_from_cluster(
            storage_root=tmp_path / "outputs",
            selector=ArtifactSelector(),
            replace=False,
        )
