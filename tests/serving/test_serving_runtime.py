from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from spice.config.models import ChainRuntimeSpec, ChainSpec, ResolvedRpcEndpointConfig
from spice.serving.config import ServingConfig
from spice.serving.runtime import load_serving_runtime


def _config() -> ServingConfig:
    return ServingConfig(
        storage_root=Path("."),
        artifact_id="art_1",
        chain=ChainSpec(
            name="sepolia",
            runtime=ChainRuntimeSpec(
                chain_id=11155111,
                uses_poa_extra_data=False,
                nominal_block_time_seconds=12.0,
            ),
        ),
        rpc_endpoint=ResolvedRpcEndpointConfig(
            provider_name="test",
            url="https://rpc.example",
            reference="test:sepolia",
            timeout_seconds=1.0,
            retry_count=0,
            backoff_factor=0.0,
        ),
        analytics_db_path=Path("serving.sqlite"),
        demo_contract_address="0x0000000000000000000000000000000000000001",
    )


def test_serving_runtime_rejects_artifact_for_different_chain(monkeypatch) -> None:
    monkeypatch.setattr(
        "spice.serving.runtime.resolve_artifact_record",
        lambda *_args, **_kw: object(),
    )
    monkeypatch.setattr(
        "spice.serving.runtime.artifact_root_handle_from_record",
        lambda *_: SimpleNamespace(root_path=Path(".")),
    )
    monkeypatch.setattr(
        "spice.serving.runtime.load_training_artifact",
        lambda _path: SimpleNamespace(manifest=SimpleNamespace(chain_name="ethereum")),
    )

    with pytest.raises(ValueError, match="artifact chain does not match"):
        load_serving_runtime(_config())
