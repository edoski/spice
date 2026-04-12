from __future__ import annotations

from typer.testing import CliRunner

from spice.cli import app
from spice.config import ChainName, RpcProviderName
from tests.support import write_override

runner = CliRunner()


def test_acquire_cli_loads_specs_and_applies_override_precedence(
    tmp_path,
    monkeypatch,
) -> None:
    config_path = write_override(
        tmp_path,
        {
            "chain": "polygon",
            "provider": "direct",
            "dataset": {
                "history_context_blocks": 640,
            },
        },
    )
    monkeypatch.setenv("AVALANCHE_RPC_URL", "https://avax.example.test")
    captured: dict[str, object] = {}

    def _capture(config) -> None:
        captured["config"] = config

    monkeypatch.setattr("spice.cli.acquire.run", _capture)

    result = runner.invoke(
        app,
        [
            "acquire",
            "--preset",
            "icdcs_2026",
            "--config",
            str(config_path),
            "--chain",
            "avalanche",
            "--storage-root",
            str(tmp_path / "outputs"),
        ],
    )

    assert result.exit_code == 0, result.stdout
    config = captured["config"]
    assert config.chain.name is ChainName.AVALANCHE
    assert config.provider.name is RpcProviderName.DIRECT
    assert config.provider.endpoint_for(config.chain.name) == "https://avax.example.test"
    assert config.dataset.id == "icdcs_2026"
    assert config.dataset.history_context_blocks == 640
    assert config.paths.output_root == tmp_path / "outputs"
    assert config.paths.history_dir == (
        tmp_path / "outputs" / "datasets" / "avalanche" / "icdcs_2026" / "history"
    )
