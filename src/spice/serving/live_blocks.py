"""Live Sepolia RPC access for serving."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import SupportsInt, cast

import polars as pl
from eth_typing import HexStr
from web3 import AsyncWeb3
from web3.exceptions import TransactionNotFound

from ..acquisition.rpc import BlockRpcClient
from ..acquisition.rpc.transport import build_async_web3
from ..corpus.contract import canonicalize_block_frame
from ..corpus.metadata import CorpusAcquisitionSourceRequirements
from .config import ServingConfig


@dataclass(frozen=True, slots=True)
class LiveBlockWindow:
    blocks: pl.DataFrame
    support_start_block: int
    support_end_block: int
    observed_block: int
    observed_timestamp: int


@dataclass(frozen=True, slots=True)
class LiveTransactionReceipt:
    tx_hash: str
    block_number: int
    gas_used: int


class LiveSepoliaClient:
    def __init__(self, config: ServingConfig, block_client: BlockRpcClient) -> None:
        self._config = config
        self._block_client = block_client
        self._web3: AsyncWeb3 = build_async_web3(config.rpc_endpoint, config.chain)

    async def close(self) -> None:
        await self._block_client.close()
        disconnect = getattr(self._web3.provider, "disconnect", None)
        if disconnect is not None:
            result = disconnect()
            if hasattr(result, "__await__"):
                await result

    async def fetch_confirmed_window(self, *, support_block_count: int) -> LiveBlockWindow:
        latest = await self._block_client.latest_block_header()
        observed_number = max(0, latest.number - self._config.confirmation_depth)
        observed = await self._block_client.block_header(observed_number)
        support_start = max(0, observed.number - support_block_count + 1)
        support_end = observed.number + 1
        rows = await self._block_client.get_block_rows(support_start, support_end)
        blocks = canonicalize_block_frame(pl.DataFrame(rows))
        return LiveBlockWindow(
            blocks=blocks,
            support_start_block=support_start,
            support_end_block=support_end,
            observed_block=observed.number,
            observed_timestamp=observed.timestamp,
        )

    async def latest_block_number(self) -> int:
        return (await self._block_client.latest_block_header()).number

    async def transaction_receipt(self, tx_hash: str) -> LiveTransactionReceipt | None:
        try:
            receipt = await self._web3.eth.get_transaction_receipt(cast(HexStr, tx_hash))
        except TransactionNotFound:
            return None
        payload = _mapping(receipt, "transaction receipt")
        block_number = _quantity_int(payload.get("blockNumber"))
        gas_used = _quantity_int(payload.get("gasUsed"))
        return LiveTransactionReceipt(
            tx_hash=tx_hash,
            block_number=block_number,
            gas_used=gas_used,
        )

    async def base_fee_per_gas(self, block_number: int) -> int:
        block = _mapping(await self._web3.eth.get_block(block_number, False), "block")
        value = block.get("baseFeePerGas")
        if value is None:
            raise ValueError(f"block {block_number} does not contain baseFeePerGas")
        return _quantity_int(value)


def build_live_sepolia_client(
    config: ServingConfig,
    runtime_source_requirements: CorpusAcquisitionSourceRequirements,
) -> LiveSepoliaClient:
    return LiveSepoliaClient(
        config,
        BlockRpcClient(
            config.rpc_endpoint,
            config.chain,
            runtime_source_requirements,
        ),
    )


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"unsupported {label} payload type: {type(value)!r}")
    return cast(Mapping[str, object], value)


def _quantity_int(value: object) -> int:
    if isinstance(value, str) and value.startswith("0x"):
        return int(value, 16)
    return int(cast(SupportsInt | str | bytes | bytearray, value))
