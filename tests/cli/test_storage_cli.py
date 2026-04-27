from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from spice.cli import app
from spice.storage.catalog.store import upsert_artifact_record
from spice.storage.layout import catalog_db_path

runner = CliRunner()


def _write_artifact_record(storage_root: Path, artifact_id: str) -> None:
    root_path = storage_root / "artifacts" / "ethereum" / artifact_id
    upsert_artifact_record(
        catalog_db_path(storage_root),
        artifact_id=artifact_id,
        dataset_id="cor_1",
        dataset_name="dataset",
        chain_name="ethereum",
        features_id="features",
        prediction_id="prediction",
        model_id="model",
        problem_id="problem",
        variant="baseline",
        study_id=None,
        study_name=None,
        root_path=root_path,
        state_db_path=root_path / ".spice" / "state.sqlite",
    )


def test_show_writes_success_to_stdout_and_ambiguous_detail_to_stderr(tmp_path: Path) -> None:
    storage_root = tmp_path / "outputs"
    _write_artifact_record(storage_root, "art_1")
    _write_artifact_record(storage_root, "art_2")

    success = runner.invoke(app, ["show", "artifact", "--storage-root", str(storage_root)])

    assert success.exit_code == 0, success.output
    assert "artifact list" in success.stdout
    assert "art_1" in success.stdout

    failure = runner.invoke(
        app,
        ["show", "artifact", "--storage-root", str(storage_root), "--detail", "epochs"],
    )

    assert failure.exit_code != 0
    assert "artifact matches" not in failure.stdout
    assert "artifact matches" in failure.stderr
