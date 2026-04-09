"""Alchemy environment helpers."""

from __future__ import annotations

import os

from dotenv import load_dotenv

from spice_temporal.config import ChainName
from spice_temporal.constants import PROJECT_ROOT

ALCHEMY_RPC_TEMPLATE = {
    "ethereum": "https://eth-mainnet.g.alchemy.com/v2/{api_key}",
    "polygon": "https://polygon-mainnet.g.alchemy.com/v2/{api_key}",
    "avalanche": "https://avax-mainnet.g.alchemy.com/v2/{api_key}",
}


def load_project_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env", override=False)


def get_alchemy_api_key() -> str:
    api_key = os.environ.get("ALCHEMY_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ALCHEMY_API_KEY in .env")
    return api_key


def resolve_rpc_url(chain_name: ChainName) -> str:
    return ALCHEMY_RPC_TEMPLATE[chain_name].format(api_key=get_alchemy_api_key())


def redact_sensitive_text(text: str) -> str:
    return text.replace(get_alchemy_api_key(), "***")
