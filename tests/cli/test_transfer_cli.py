from __future__ import annotations

from typer.testing import CliRunner

from spice.cli.app import app
from spice.execution.transfer_transaction import TransferredRoot
from spice.storage.catalog.materialization import materialize_catalog_root
from spice.storage.engine import RootKind
from tests.catalog_helpers import artifact_record, dataset_record

runner = CliRunner()


def test_transfer_push_dataset_command_routes_to_dataset_transfer(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}
    record = dataset_record(tmp_path / "outputs" / "corpora" / "ethereum" / "dataset-1")

    class FakeTransaction:
        def push_root(self, root_kind: RootKind, root_id: str, *, replace: bool):
            captured["root_kind"] = root_kind
            captured["root_id"] = root_id
            captured["replace"] = replace
            return TransferredRoot(
                root_kind=root_kind,
                source_record=record,
                destination_record=record,
                source_root=materialize_catalog_root(tmp_path / "outputs", record).root_path,
                destination_root=materialize_catalog_root(tmp_path / "outputs", record).root_path,
            )

    monkeypatch.setattr(
        "spice.cli.commands.transfer.open_storage_transfer_transaction",
        lambda target, *, local_storage_root: (
            captured.update({"target": target, "local_storage_root": local_storage_root})
            or FakeTransaction()
        ),
    )

    result = runner.invoke(
        app,
        [
            "transfer",
            "push",
            "dataset",
            "--dataset-id",
            record.dataset_id,
            "--storage-root",
            str(tmp_path / "outputs"),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert captured["target"] == "disi_l40"
    assert captured["root_kind"] is RootKind.CORPUS
    assert captured["root_id"] == record.dataset_id
    assert "push dataset=dataset dataset_id=dataset-1" in result.stdout


def test_transfer_pull_artifact_command_uses_pulled_envelope(monkeypatch, tmp_path) -> None:
    record = artifact_record(tmp_path / "outputs" / "artifacts" / "ethereum" / "artifact-1")
    pulled = TransferredRoot(
        root_kind=RootKind.ARTIFACT,
        source_record=record,
        destination_record=record,
        source_root=materialize_catalog_root(tmp_path / "outputs", record).root_path,
        destination_root=materialize_catalog_root(tmp_path / "outputs", record).root_path,
    )

    class FakeTransaction:
        def pull_root(self, root_kind: RootKind, root_id: str, *, replace: bool):
            del root_kind, root_id, replace
            return pulled

    monkeypatch.setattr(
        "spice.cli.commands.transfer.open_storage_transfer_transaction",
        lambda _target, *, local_storage_root: FakeTransaction(),
    )
    monkeypatch.setattr(
        "spice.cli.commands.transfer.artifact_local_dependency_warnings",
        lambda _root, _record: (
            "matching local dataset root is missing; local inspection still needs that dataset",
        ),
    )

    result = runner.invoke(app, ["transfer", "pull", "artifact", "--artifact-id", "artifact-1"])

    assert result.exit_code == 0, result.stdout
    assert "pull artifact=artifact-1" in result.stdout
    assert "matching local dataset root is missing" in result.stderr
