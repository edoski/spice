from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from spice.core.errors import StateLayoutError
from spice.storage.artifact import load_artifact_manifest
from spice.storage.catalog.store import upsert_dataset_record
from spice.storage.engine import DATASET_ROOT_KIND, ensure_state_db, state_db_path
from spice.storage.layout import catalog_db_path
from spice.storage.schema import DATASET_TABLES


def _dataset_timestamps(path: Path, dataset_id: str) -> tuple[int, int]:
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "select created_at, updated_at from dataset_index where dataset_id = ?",
            (dataset_id,),
        ).fetchone()
    assert row is not None
    return int(row[0]), int(row[1])


def test_catalog_upsert_keeps_created_at_stable(tmp_path: Path, monkeypatch) -> None:
    from spice.storage.catalog import store

    storage_root = tmp_path / "outputs"
    catalog_path = catalog_db_path(storage_root)
    timestamps = iter([100, 200])
    monkeypatch.setattr(store, "_now_timestamp", lambda: next(timestamps))

    state_db_path = storage_root / "corpora" / "ethereum" / "dataset-1" / ".spice" / "state.sqlite"
    upsert_dataset_record(
        catalog_path,
        dataset_id="dataset-1",
        dataset_name="old",
        chain_name="ethereum",
        root_path=storage_root / "corpora" / "ethereum" / "dataset-1",
        state_db_path=state_db_path,
    )
    upsert_dataset_record(
        catalog_path,
        dataset_id="dataset-1",
        dataset_name="new",
        chain_name="ethereum",
        root_path=storage_root / "corpora" / "ethereum" / "dataset-1",
        state_db_path=state_db_path,
    )

    assert _dataset_timestamps(catalog_path, "dataset-1") == (100, 200)


def test_artifact_reader_rejects_corpus_root_kind(tmp_path: Path) -> None:
    root = tmp_path / "outputs" / "corpora" / "ethereum" / "dataset-1"
    db_path = state_db_path(root)
    ensure_state_db(db_path, root_kind=DATASET_ROOT_KIND, tables=DATASET_TABLES)

    with pytest.raises(StateLayoutError, match="root kind mismatch"):
        load_artifact_manifest(db_path)
