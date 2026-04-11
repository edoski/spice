from __future__ import annotations

import asyncio
from typing import Any, cast

import pytest
from web3.exceptions import Web3RPCError
from web3.middleware import ExtraDataToPOAMiddleware

from spice.acquisition.provider import build_async_web3
from spice.acquisition.rpc import BlockPullPlan, BlockRange, RpcController, TimestampRange, Web3BlockClient
from tests.support import make_chain_config, make_provider_config


def test_build_async_web3_uses_configured_http_endpoint() -> None:
    web3 = build_async_web3(
        make_provider_config(),
        make_chain_config(),
    )

    assert web3.provider is not None
    assert cast(Any, web3.provider).endpoint_uri == "https://rpc.example.test"


@pytest.mark.parametrize(
    ("endpoint", "expected_suffix"),
    [
        ("file:///tmp/geth.ipc", "/tmp/geth.ipc"),
        ("/tmp/geth.ipc", "/tmp/geth.ipc"),
    ],
)
def test_build_async_web3_supports_ipc_endpoints(endpoint: str, expected_suffix: str) -> None:
    web3 = build_async_web3(
        make_provider_config(endpoint=endpoint),
        make_chain_config(),
    )

    assert web3.provider is not None
    assert cast(Any, web3.provider).ipc_path.endswith(expected_suffix)


def test_build_async_web3_injects_poa_middleware_for_poa_extra_data_chains() -> None:
    web3 = build_async_web3(
        make_provider_config(),
        make_chain_config(uses_poa_extra_data=True),
    )

    assert ExtraDataToPOAMiddleware in web3.middleware_onion


def test_rpc_controller_requires_repeated_transient_failures_before_backoff() -> None:
    controller = RpcController(
        configured_batch_size=256,
        min_batch_size=64,
        concurrency_rungs=(8, 16, 24, 32, 48),
        configured_concurrency=48,
    )

    assert controller.record_transient_failure() is None
    assert controller.current_concurrency == 48
    assert controller.record_transient_failure() == 32
    assert controller.current_concurrency == 32
    assert controller.transient_backoffs == 1


def test_rpc_controller_recovers_one_rung_after_clean_window() -> None:
    controller = RpcController(
        configured_batch_size=256,
        min_batch_size=64,
        concurrency_rungs=(8, 16, 24, 32, 48),
        configured_concurrency=48,
    )
    controller.record_transient_failure()
    controller.record_transient_failure()

    assert controller.current_concurrency == 32
    for _ in range(63):
        assert controller.record_success() is None

    assert controller.record_success() == 48
    assert controller.current_concurrency == 48
    assert controller.concurrency_recoveries == 1


def test_rpc_controller_halves_batch_size_until_minimum() -> None:
    controller = RpcController(
        configured_batch_size=256,
        min_batch_size=64,
        concurrency_rungs=(8, 16, 24, 32, 48),
        configured_concurrency=48,
    )

    assert controller.record_oversize_failure() == 128
    assert controller.record_oversize_failure() == 64
    assert controller.record_oversize_failure() is None
    assert controller.current_batch_size == 64
    assert controller.oversize_backoffs == 2


def test_web3_block_client_uses_latest_block_for_head_resolution(monkeypatch) -> None:
    timestamps = {
        0: 100,
        1: 112,
        2: 124,
        3: 136,
    }

    class FakeEth:
        async def get_block(
            self,
            block_number: int | str,
            _full_transactions: bool = False,
        ) -> dict[str, int]:
            if block_number == "latest":
                block_number = 3
            number = int(block_number)
            return {
                "number": number,
                "timestamp": timestamps[number],
                "baseFeePerGas": 1,
                "gasUsed": 1,
                "gasLimit": 1,
            }

    class FakeWeb3:
        eth = FakeEth()

        def batch_requests(self):
            raise AssertionError("batch path not used in binary search")

    monkeypatch.setattr(
        "spice.acquisition.rpc.build_async_web3",
        lambda _provider, _chain: FakeWeb3(),
    )

    client = Web3BlockClient(make_provider_config(), make_chain_config())

    assert asyncio.run(client.find_first_block_at_or_after(100)) == 0
    assert asyncio.run(client.find_first_block_at_or_after(113)) == 2
    assert asyncio.run(client.find_first_block_at_or_after(149)) == 4
    assert asyncio.run(
        client.resolve_block_range(TimestampRange(start=112, end=136))
    ) == BlockRange(start=1, end=3)


def test_web3_block_client_plans_history_by_exact_block_count(monkeypatch) -> None:
    class FakeEth:
        async def get_block(
            self,
            block_number: int | str,
            _full_transactions: bool = False,
        ) -> dict[str, int]:
            if block_number == "latest":
                block_number = 6
            number = int(block_number)
            return {
                "number": number,
                "timestamp": 100 + number * 12,
                "baseFeePerGas": 1,
                "gasUsed": 1,
                "gasLimit": 1,
            }

    class FakeWeb3:
        eth = FakeEth()

        def batch_requests(self):
            raise AssertionError("batch path not used in planning")

    monkeypatch.setattr(
        "spice.acquisition.rpc.build_async_web3",
        lambda _provider, _chain: FakeWeb3(),
    )

    client = Web3BlockClient(make_provider_config(), make_chain_config())
    plan = asyncio.run(
        client.plan_history_window(
            end_timestamp=136,
            required_history_blocks=2,
            chunk_size=5,
        )
    )

    assert plan == BlockPullPlan(
        window=TimestampRange(start=112, end=136),
        block_range=BlockRange(start=1, end=3),
        expected_rows=2,
        expected_files=1,
    )


def test_web3_block_client_expands_history_plan_by_missing_blocks(monkeypatch) -> None:
    class FakeEth:
        async def get_block(
            self,
            block_number: int | str,
            _full_transactions: bool = False,
        ) -> dict[str, int]:
            if block_number == "latest":
                block_number = 40
            number = int(block_number)
            return {
                "number": number,
                "timestamp": 100 + number * 12,
                "baseFeePerGas": 1,
                "gasUsed": 1,
                "gasLimit": 1,
            }

    class FakeWeb3:
        eth = FakeEth()

        def batch_requests(self):
            raise AssertionError("batch path not used in planning")

    monkeypatch.setattr(
        "spice.acquisition.rpc.build_async_web3",
        lambda _provider, _chain: FakeWeb3(),
    )

    client = Web3BlockClient(make_provider_config(), make_chain_config())
    current = BlockPullPlan(
        window=TimestampRange(start=340, end=460),
        block_range=BlockRange(start=20, end=30),
        expected_rows=10,
        expected_files=2,
    )

    expanded = asyncio.run(
        client.expand_history_plan(
            current,
            observed_row_count=7,
            required_history_blocks=10,
            chunk_size=5,
        )
    )

    assert expanded == BlockPullPlan(
        window=TimestampRange(start=244, end=460),
        block_range=BlockRange(start=12, end=30),
        expected_rows=18,
        expected_files=4,
    )
