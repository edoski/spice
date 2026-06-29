from __future__ import annotations

import asyncio
from pathlib import Path

from spice.config.models import ChainRuntimeSpec, ChainSpec, ResolvedRpcEndpointConfig
from spice.serving.config import ServingConfig
from spice.serving.live_blocks import LiveSepoliaClient


class FakeBlockClient:
    async def close(self) -> None:
        return None

    async def latest_block_header(self):
        return Header(number=105, timestamp=1_700_000_060)

    async def block_header(self, block_number: int):
        return Header(number=block_number, timestamp=1_700_000_000 + block_number)

    async def get_block_rows(self, start: int, end: int):
        return [
            {
                "block_number": block,
                "timestamp": 1_700_000_000 + block,
                "base_fee_per_gas": 1000 + block,
                "gas_used": 1,
                "chain_id": 11155111,
                "gas_limit": 30_000_000,
                "tx_count": 1,
                "block_size_bytes": 1,
                "blob_gas_used": None,
                "excess_blob_gas": None,
                "priority_fee_p10": None,
                "priority_fee_p50": None,
                "priority_fee_p90": None,
                "priority_fee_spread": None,
            }
            for block in range(start, end)
        ]


class Header:
    def __init__(self, *, number: int, timestamp: int) -> None:
        self.number = number
        self.timestamp = timestamp


class FakeProvider:
    async def disconnect(self) -> None:
        return None


class FakeWeb3:
    provider = FakeProvider()


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


def test_live_block_client_builds_confirmed_canonical_window(monkeypatch) -> None:
    monkeypatch.setattr("spice.serving.live_blocks.build_async_web3", lambda *_: FakeWeb3())
    client = LiveSepoliaClient(_config(), FakeBlockClient())

    window = asyncio.run(client.fetch_confirmed_window(support_block_count=4))

    assert window.observed_block == 103
    assert window.support_start_block == 100
    assert window.support_end_block == 104
    assert window.blocks.height == 4
    assert window.blocks["block_number"].to_list() == [100, 101, 102, 103]
