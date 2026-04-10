from __future__ import annotations

import yaml

from spice.acquisition.cryo import CryoRunResult, evaluation_range, history_range_for_chain
from spice.acquisition.provenance import source_manifest_path_for
from spice.acquisition.rpc_providers import RpcProviderName
from spice.acquisition.snapshots import activate_snapshot as mark_active_snapshot
from spice.acquisition.snapshots import record_snapshot
from spice.api import (
    acquire_snapshot,
    list_snapshots,
    load_config,
    resolve_artifact_dir,
    resolve_snapshot_paths,
    simulate_model,
    train_model,
)
from spice.core.constants import SIMULATION_REPORT_FILENAME, TRAIN_REPORT_FILENAME
from tests.support import (
    build_test_config,
    make_block_rows,
    make_evaluation_rows,
    make_history_rows,
    snapshot_dataset_dir,
    write_config,
    write_dataset_dir,
    write_raw_chunk,
)


def _install_snapshot(config, *, snapshot_name: str, active: bool = True) -> None:
    chain = config.resolve_chain("ethereum")
    history_dir = snapshot_dataset_dir(
        config.output_root,
        chain_name=chain.name.value,
        snapshot_name=snapshot_name,
        dataset_kind="enriched",
        segment="history",
    )
    evaluation_dir = snapshot_dataset_dir(
        config.output_root,
        chain_name=chain.name.value,
        snapshot_name=snapshot_name,
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
        snapshot_name=snapshot_name,
        pull_provider="publicnode",
        enrich_provider="publicnode",
        history_start_timestamp=history_range.start,
        history_end_timestamp=history_range.end,
        evaluation_start_timestamp=evaluation.start,
        evaluation_end_timestamp=evaluation.end,
    )
    if active:
        mark_active_snapshot(config.output_root, chain, snapshot_name)


class FakeJsonRpcClient:
    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def __enter__(self) -> FakeJsonRpcClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def get_block_gas_limits(self, block_numbers: list[int]) -> dict[int, int]:
        return {block_number: 30_000_000 for block_number in block_numbers}


def test_acquire_snapshot_writes_registry_and_activation(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    output_root = tmp_path / "artifacts"
    write_config(config_path, output_root=output_root)
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

    result = acquire_snapshot(
        config,
        "ethereum",
        snapshot_name="working",
        rpc_provider=RpcProviderName.PUBLICNODE,
        dry_run=False,
        config_path=config_path,
    )

    assert result.activated is True
    assert result.history.raw.validation is not None
    assert result.evaluation.raw.validation is not None
    assert result.history.raw.source_manifest_path == source_manifest_path_for(
        result.history.raw.output_dir
    )
    assert result.evaluation.enriched_source_manifest_path == source_manifest_path_for(
        result.evaluation.enriched_output_dir
    )
    snapshots = list_snapshots(config, "ethereum")
    assert len(snapshots) == 1
    assert snapshots[0].name == "working"
    assert snapshots[0].active is True


def test_acquire_snapshot_no_activate_preserves_previous_active(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    output_root = tmp_path / "artifacts"
    write_config(config_path, output_root=output_root)
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
        snapshot_name="working",
        rpc_provider=RpcProviderName.PUBLICNODE,
        dry_run=False,
        config_path=config_path,
    )
    acquire_snapshot(
        config,
        "ethereum",
        snapshot_name="candidate",
        rpc_provider=RpcProviderName.PUBLICNODE,
        dry_run=False,
        activate=False,
        config_path=config_path,
    )

    snapshots = {item.name: item for item in list_snapshots(config, "ethereum")}
    assert snapshots["working"].active is True
    assert snapshots["candidate"].active is False


def test_train_and_simulate_model_workflows_write_artifacts(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    output_root = tmp_path / "artifacts"
    write_config(config_path, output_root=output_root)
    config = load_config(config_path)
    _install_snapshot(config, snapshot_name="working", active=True)

    training_result = train_model(config, "lstm", device="cpu")

    assert training_result.training_report.chain == "ethereum"
    assert training_result.simulation_report is None
    assert (training_result.artifact_dir / TRAIN_REPORT_FILENAME).is_file()
    assert not (training_result.artifact_dir / SIMULATION_REPORT_FILENAME).exists()

    simulation_result = simulate_model(config, "lstm", device="cpu")

    assert simulation_result.report.total_events > 0
    assert (simulation_result.artifact_dir / SIMULATION_REPORT_FILENAME).is_file()


def test_train_model_evaluate_writes_simulation_report(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    output_root = tmp_path / "artifacts"
    write_config(config_path, output_root=output_root)
    config = load_config(config_path)
    _install_snapshot(config, snapshot_name="working", active=True)

    result = train_model(config, "lstm", device="cpu", evaluate=True)

    assert result.simulation_report is not None
    assert (result.artifact_dir / TRAIN_REPORT_FILENAME).is_file()
    assert (result.artifact_dir / SIMULATION_REPORT_FILENAME).is_file()


def test_resolvers_use_active_snapshot_and_run_convention(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    output_root = tmp_path / "artifacts"
    write_config(config_path, output_root=output_root)
    config = load_config(config_path)
    _install_snapshot(config, snapshot_name="working", active=True)

    paths = resolve_snapshot_paths(config)
    artifact_dir = resolve_artifact_dir(config, "lstm")

    assert paths.snapshot_name == "working"
    assert paths.enriched_history_dir.name == "history"
    assert artifact_dir == output_root / "runs" / "ethereum" / "lstm-36s"


def test_train_model_requires_chain_when_config_has_multiple_chains(tmp_path) -> None:
    config_path = tmp_path / "baseline.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                **build_test_config(tmp_path / "artifacts"),
                "max_delay_seconds": [36],
                "chains": [
                    {
                        "name": "ethereum",
                        "chain_id": 1,
                        "block_time_seconds": 12.0,
                        "history_days": 1,
                    },
                    {
                        "name": "polygon",
                        "chain_id": 137,
                        "block_time_seconds": 2.0,
                        "history_days": 1,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    config = load_config(config_path)

    try:
        train_model(config, "lstm", max_delay_seconds=36, device="cpu")
    except ValueError as exc:
        assert "chain_name is required" in str(exc)
    else:
        raise AssertionError("Expected train_model to reject ambiguous chain inference")


def test_train_model_requires_delay_when_config_has_multiple_values(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    payload = build_test_config(tmp_path / "artifacts")
    payload["max_delay_seconds"] = [12, 36]
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    config = load_config(config_path)

    try:
        train_model(config, "lstm", "ethereum", device="cpu")
    except ValueError as exc:
        assert "max_delay_seconds is required" in str(exc)
    else:
        raise AssertionError("Expected train_model to reject ambiguous delay inference")
