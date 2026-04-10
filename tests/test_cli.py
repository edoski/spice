from __future__ import annotations

from typer.testing import CliRunner

from spice.acquisition.cryo import CryoRunResult, evaluation_range, history_range_for_chain
from spice.acquisition.rpc_providers import RpcProviderName
from spice.acquisition.snapshots import activate_snapshot as mark_active_snapshot
from spice.acquisition.snapshots import record_snapshot
from spice.cli import app
from spice.core.constants import SIMULATION_REPORT_FILENAME, TRAIN_REPORT_FILENAME
from tests.support import (
    make_block_rows,
    make_evaluation_rows,
    make_history_rows,
    snapshot_dataset_dir,
    write_config,
    write_dataset_dir,
    write_raw_chunk,
)


class FakeJsonRpcClient:
    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def __enter__(self) -> FakeJsonRpcClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def get_block_gas_limits(self, block_numbers: list[int]) -> dict[int, int]:
        return {block_number: 30_000_000 for block_number in block_numbers}


def _install_active_snapshot(config) -> None:
    chain = config.resolve_chain("ethereum")
    history_dir = snapshot_dataset_dir(
        config.output_root,
        chain_name=chain.name.value,
        snapshot_name="working",
        dataset_kind="enriched",
        segment="history",
    )
    evaluation_dir = snapshot_dataset_dir(
        config.output_root,
        chain_name=chain.name.value,
        snapshot_name="working",
        dataset_kind="enriched",
        segment="evaluation",
    )
    write_dataset_dir(history_dir, make_history_rows())
    write_dataset_dir(evaluation_dir, make_evaluation_rows())
    history_range = history_range_for_chain(chain)
    evaluation = evaluation_range()
    record_snapshot(
        config.output_root,
        chain,
        snapshot_name="working",
        pull_provider="publicnode",
        enrich_provider="publicnode",
        history_start_timestamp=history_range.start,
        history_end_timestamp=history_range.end,
        evaluation_start_timestamp=evaluation.start,
        evaluation_end_timestamp=evaluation.end,
    )
    mark_active_snapshot(config.output_root, chain, "working")


def test_cli_acquire_dry_run_shows_history_and_evaluation(tmp_path, monkeypatch) -> None:
    runner = CliRunner()
    config_path = tmp_path / "config.yaml"
    output_root = tmp_path / "artifacts"
    write_config(config_path, output_root=output_root)

    monkeypatch.setattr(
        "spice.api.run_cryo",
        lambda *args, **kwargs: CryoRunResult(
            command=f"cryo {(kwargs['output_dir'] if 'output_dir' in kwargs else args[2]).name}",
            completed_chunks=0,
            expected_chunks=1,
        ),
    )

    result = runner.invoke(app, ["acquire", str(config_path), "--provider", "publicnode"])

    assert result.exit_code == 0
    assert "snapshot=working" in result.stdout
    assert "history_command=cryo history" in result.stdout
    assert "evaluation_command=cryo evaluation" in result.stdout


def test_cli_train_smoke(tmp_path) -> None:
    runner = CliRunner()
    config_path = tmp_path / "config.yaml"
    output_root = tmp_path / "artifacts"
    write_config(config_path, output_root=output_root)
    from spice.api import load_config

    config = load_config(config_path)
    _install_active_snapshot(config)

    result = runner.invoke(
        app,
        [
            "train",
            str(config_path),
            "lstm",
            "--device",
            "cpu",
        ],
    )

    assert result.exit_code == 0
    assert "artifact_dir=" in result.stdout
    assert "best_epoch=" in result.stdout
    artifact_dir = output_root / "runs" / "ethereum" / "lstm-36s"
    assert (artifact_dir / TRAIN_REPORT_FILENAME).is_file()
    assert not (artifact_dir / SIMULATION_REPORT_FILENAME).exists()


def test_cli_datasets_validate_and_activate(tmp_path, monkeypatch) -> None:
    runner = CliRunner()
    config_path = tmp_path / "config.yaml"
    output_root = tmp_path / "artifacts"
    write_config(config_path, output_root=output_root)
    from spice.api import acquire_snapshot, load_config

    config = load_config(config_path)

    def fake_run_cryo(*args, **kwargs):
        output_dir = kwargs["output_dir"] if "output_dir" in kwargs else args[2]
        timestamps = kwargs["timestamps"] if "timestamps" in kwargs else args[3]
        segment = output_dir.name
        rows = make_block_rows(
            4,
            start_block=1 if segment == "history" else 10_001,
            start_timestamp=timestamps.start,
            include_gas_limit=False,
        )
        write_raw_chunk(output_dir, chain_name="ethereum", rows=rows)
        return CryoRunResult(command=f"cryo {segment}", completed_chunks=1, expected_chunks=1)

    monkeypatch.setattr("spice.api.run_cryo", fake_run_cryo)
    monkeypatch.setattr("spice.api.JsonRpcClient", FakeJsonRpcClient)
    acquire_snapshot(
        config,
        "ethereum",
        snapshot_name="candidate",
        rpc_provider=RpcProviderName.PUBLICNODE,
        dry_run=False,
        activate=False,
        config_path=config_path,
    )
    list_result = runner.invoke(app, ["datasets", "list", str(config_path)])
    show_result = runner.invoke(app, ["datasets", "show", str(config_path), "candidate"])
    validate_result = runner.invoke(app, ["datasets", "validate", str(config_path), "candidate"])
    activate_result = runner.invoke(app, ["datasets", "activate", str(config_path), "candidate"])

    assert list_result.exit_code == 0
    assert "snapshot=candidate" in list_result.stdout
    assert show_result.exit_code == 0
    assert "snapshot_root=" in show_result.stdout
    assert validate_result.exit_code == 0
    assert "status=clean" in validate_result.stdout
    assert activate_result.exit_code == 0
    assert "snapshot=candidate" in activate_result.stdout
