from __future__ import annotations

from pathlib import Path

import pytest

from spice.core.errors import StateConflictError
from spice.storage.engine import RootKind
from spice.storage.staging import PartialRootCommit, prepare_root_stage


def test_partial_root_commit_promotes_selected_paths_and_reindexes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    storage_root = tmp_path / "outputs"
    root_path = storage_root / "corpora" / "ethereum" / "dataset-1"
    source_dir = tmp_path / "stage" / "history"
    source_dir.mkdir(parents=True)
    (source_dir / "blocks.parquet").write_text("payload", encoding="utf-8")
    captured: dict[str, Path] = {}

    def fake_reindex_root(storage_root: Path, *, root_path: Path) -> RootKind:
        captured.update({"storage_root": storage_root, "root_path": root_path})
        return RootKind.CORPUS

    monkeypatch.setattr("spice.storage.staging.reindex_root", fake_reindex_root)

    commit = PartialRootCommit(storage_root=storage_root, root_path=root_path)
    commit.add(root_path / "history", source_dir)

    assert commit.commit() is RootKind.CORPUS
    assert (root_path / "history" / "blocks.parquet").read_text(encoding="utf-8") == "payload"
    assert captured == {"storage_root": storage_root, "root_path": root_path}


def test_prepare_root_stage_rejects_existing_destination_without_replace(tmp_path: Path) -> None:
    destination = tmp_path / "outputs" / "artifacts" / "ethereum" / "artifact-1"
    destination.mkdir(parents=True)

    with pytest.raises(StateConflictError, match="Destination already exists"):
        prepare_root_stage(destination_root=destination, replace=False)
