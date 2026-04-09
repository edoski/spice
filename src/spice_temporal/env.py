"""Environment loading and RPC URL resolution."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from spice_temporal.constants import PROJECT_ROOT

ALCHEMY_RPC_TEMPLATE = {
    "ETH_RPC_URL": "https://eth-mainnet.g.alchemy.com/v2/{api_key}",
    "POLYGON_RPC_URL": "https://polygon-mainnet.g.alchemy.com/v2/{api_key}",
    "AVAX_RPC_URL": "https://avax-mainnet.g.alchemy.com/v2/{api_key}",
}


def load_project_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env", override=False)


def resolve_rpc_url(env_var: str) -> str | None:
    explicit = os.environ.get(env_var)
    if explicit:
        return explicit

    api_key = os.environ.get("ALCHEMY_API_KEY")
    template = ALCHEMY_RPC_TEMPLATE.get(env_var)
    if api_key and template:
        derived = template.format(api_key=api_key)
        os.environ.setdefault(env_var, derived)
        return derived
    return None


def env_file_path() -> Path:
    return PROJECT_ROOT / ".env"
