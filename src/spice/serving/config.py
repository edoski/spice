"""Environment-backed serving configuration."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ..config import ChainSpec, ResolvedRpcEndpointConfig
from ..config import typed_groups as typed

DEFAULT_CHAIN_NAME = "sepolia"
DEFAULT_ANALYTICS_DB = ".spice/serving.sqlite"
DEFAULT_CONFIRMATION_DEPTH = 2
DEFAULT_BATCH_SIZE = 1
DEFAULT_PREDICTION_TTL_SECONDS = 600
SEPOLIA_CHAIN_ID = 11155111


@dataclass(frozen=True, slots=True)
class ServingConfig:
    storage_root: Path
    artifact_id: str
    chain: ChainSpec
    rpc_endpoint: ResolvedRpcEndpointConfig
    analytics_db_path: Path
    demo_contract_address: str
    artifact_chain_name: str | None = None
    confirmation_depth: int = DEFAULT_CONFIRMATION_DEPTH
    batch_size: int = DEFAULT_BATCH_SIZE
    prediction_ttl_seconds: int = DEFAULT_PREDICTION_TTL_SECONDS


def load_serving_config(environ: Mapping[str, str] | None = None) -> ServingConfig:
    env = os.environ if environ is None else environ
    chain_name = env.get("SPICE_SERVING_CHAIN_NAME", DEFAULT_CHAIN_NAME)
    chain = typed.load(typed.CHAIN, chain_name)
    if chain.runtime.chain_id != SEPOLIA_CHAIN_ID:
        raise ValueError(
            "SPICE serving MVP requires Sepolia chain_id "
            f"{SEPOLIA_CHAIN_ID}, got {chain.runtime.chain_id}"
        )

    storage_root = _required_path(env, "SPICE_SERVING_STORAGE_ROOT")
    artifact_id = _required(env, "SPICE_SERVING_ARTIFACT_ID")
    artifact_chain_name = env.get("SPICE_SERVING_ARTIFACT_CHAIN_NAME", chain.name)
    rpc_url = _required(env, "SPICE_SERVING_RPC_URL")
    analytics_db_path = Path(env.get("SPICE_SERVING_ANALYTICS_DB", DEFAULT_ANALYTICS_DB))
    demo_contract_address = _required(env, "SPICE_SERVING_DEMO_CONTRACT_ADDRESS")
    _validate_contract_address(demo_contract_address)
    confirmation_depth = int(
        env.get("SPICE_SERVING_CONFIRMATION_DEPTH", DEFAULT_CONFIRMATION_DEPTH)
    )
    if confirmation_depth < 0:
        raise ValueError("SPICE_SERVING_CONFIRMATION_DEPTH must be non-negative")

    return ServingConfig(
        storage_root=storage_root,
        artifact_id=artifact_id,
        chain=chain,
        rpc_endpoint=ResolvedRpcEndpointConfig(
            provider_name="serving",
            url=rpc_url,
            reference=f"serving:{chain.name}",
            timeout_seconds=30.0,
            retry_count=3,
            backoff_factor=0.125,
        ),
        analytics_db_path=analytics_db_path,
        demo_contract_address=demo_contract_address,
        artifact_chain_name=artifact_chain_name,
        confirmation_depth=confirmation_depth,
    )


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name)
    if value is None or value == "":
        raise ValueError(f"{name} is required")
    return value


def _required_path(env: Mapping[str, str], name: str) -> Path:
    return Path(_required(env, name)).expanduser()


def _validate_contract_address(value: str) -> None:
    if not value.startswith("0x") or len(value) != 42:
        raise ValueError("SPICE_SERVING_DEMO_CONTRACT_ADDRESS must be an EVM address")
