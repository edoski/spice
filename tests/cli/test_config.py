from __future__ import annotations

from typer.testing import CliRunner

from spice.cli import app
from spice.storage.ids import corpus_storage_id

runner = CliRunner()


def test_acquire_cli_loads_specs_and_applies_selector_overrides(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _capture(config) -> None:
        captured["config"] = config

    monkeypatch.setattr("spice.workflows.acquire.run", _capture)

    result = runner.invoke(
        app,
        [
            "acquire",
            "--preset",
            "icdcs_2026",
            "--chain",
            "avalanche",
            "--provider",
            "publicnode",
            "--storage-root",
            str(tmp_path / "outputs"),
        ],
    )

    assert result.exit_code == 0, result.stdout
    config = captured["config"]
    assert config.chain.name == "avalanche"
    assert config.chain.runtime.chain_id == 43114
    assert config.provider.name == "publicnode"
    assert config.provider.rpc.timeout_seconds == 30.0
    assert (
        config.provider.endpoint_for(config.chain.name)
        == "https://avalanche-c-chain-rpc.publicnode.com"
    )
    assert config.acquisition.rpc.batch_size == 256
    assert config.dataset.name == "icdcs_2026"
    assert config.problem.sample_count == 400000
    assert config.feature_set.id == "icdcs_2026"
    assert config.paths.output_root == tmp_path / "outputs"
    assert config.paths.history_dir == (
        tmp_path
        / "outputs"
        / "corpora"
        / "avalanche"
        / corpus_storage_id(chain_name="avalanche", dataset_name="icdcs_2026")
        / "history"
    )
