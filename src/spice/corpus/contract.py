"""Canonical Corpus values and block schema."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, SupportsInt, TypedDict, cast

import polars as pl
from pydantic import BaseModel, ConfigDict, Field

from ..config import CorpusRequest

if TYPE_CHECKING:
    from ..config.models import ChainSpec


class FinalizedAnchor(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        revalidate_instances="always",
    )

    block_number: int = Field(ge=0)
    block_hash: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]+$")


class Corpus(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=True,
        strict=True,
        revalidate_instances="always",
    )

    request: CorpusRequest
    finalized_anchor: FinalizedAnchor
    blocks: pl.DataFrame


_BLOCK_SCHEMA = pl.Schema(
    {
        "block_number": pl.Int64,
        "timestamp": pl.Int64,
        "chain_id": pl.Int64,
        "base_fee_per_gas": pl.Int64,
        "gas_used": pl.Int64,
        "gas_limit": pl.Int64,
        "tx_count": pl.Int64,
    }
)

_CANONICAL_BLOCK_SCHEMA = pl.Schema(
    {
        "block_number": pl.Int64,
        "timestamp": pl.Int64,
        "base_fee_per_gas": pl.Int64,
        "gas_used": pl.Int64,
        "chain_id": pl.Int64,
        "gas_limit": pl.Int64,
        "tx_count": pl.Int64,
        "block_size_bytes": pl.Int64,
        "blob_gas_used": pl.Int64,
        "excess_blob_gas": pl.Int64,
        "priority_fee_p10": pl.Int64,
        "priority_fee_p50": pl.Int64,
        "priority_fee_p90": pl.Int64,
        "priority_fee_spread": pl.Int64,
    }
)
_CANONICAL_BLOCK_COLUMNS = tuple(_CANONICAL_BLOCK_SCHEMA)

RpcBlock = Mapping[str, object]


class CanonicalBlockRow(TypedDict):
    block_number: int
    timestamp: int
    base_fee_per_gas: int | None
    gas_used: int
    chain_id: int
    gas_limit: int
    tx_count: int
    block_size_bytes: int | None
    blob_gas_used: int | None
    excess_blob_gas: int | None
    priority_fee_p10: int | None
    priority_fee_p50: int | None
    priority_fee_p90: int | None
    priority_fee_spread: int | None


def _as_int(value: object) -> int:
    if isinstance(value, str) and value.startswith("0x"):
        return int(value, 16)
    if isinstance(value, bytes | bytearray) and value.startswith(b"0x"):
        return int(value, 16)
    return int(cast(SupportsInt, value))


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return _as_int(value)


def build_canonical_block_row(
    block: RpcBlock,
    chain: ChainSpec,
    *,
    priority_fee_p10: int | None = None,
    priority_fee_p50: int | None = None,
    priority_fee_p90: int | None = None,
) -> CanonicalBlockRow:
    try:
        transactions = block.get("transactions")
        if not isinstance(transactions, list | tuple):
            raise TypeError("RPC block transactions field must be a sequence")
        priority_fee_spread = (
            None
            if priority_fee_p10 is None or priority_fee_p90 is None
            else priority_fee_p90 - priority_fee_p10
        )
        return CanonicalBlockRow(
            block_number=_as_int(block["number"]),
            timestamp=_as_int(block["timestamp"]),
            base_fee_per_gas=_optional_int(block.get("baseFeePerGas")),
            gas_used=_as_int(block["gasUsed"]),
            chain_id=chain.runtime.chain_id,
            gas_limit=_as_int(block["gasLimit"]),
            tx_count=len(transactions),
            block_size_bytes=_optional_int(block.get("size")),
            blob_gas_used=_optional_int(block.get("blobGasUsed")),
            excess_blob_gas=_optional_int(block.get("excessBlobGas")),
            priority_fee_p10=priority_fee_p10,
            priority_fee_p50=priority_fee_p50,
            priority_fee_p90=priority_fee_p90,
            priority_fee_spread=priority_fee_spread,
        )
    except KeyError as exc:
        raise KeyError(f"Missing RPC block field while extracting canonical row: {exc}") from exc


def canonicalize_block_frame(frame: pl.DataFrame) -> pl.DataFrame:
    return _select_canonical_columns(frame, strict_columns=False)


def _select_canonical_columns(
    frame: pl.DataFrame,
    *,
    strict_columns: bool,
) -> pl.DataFrame:
    missing = [
        column for column in _CANONICAL_BLOCK_COLUMNS if column not in frame.columns
    ]
    if missing:
        raise ValueError(
            "Block corpus is missing required columns for canonical output: "
            + ", ".join(missing)
        )
    if strict_columns:
        unexpected = [
            column for column in frame.columns if column not in _CANONICAL_BLOCK_COLUMNS
        ]
        if unexpected:
            raise ValueError(
                "Block corpus contains unexpected columns for canonical output: "
                + ", ".join(unexpected)
            )

    return frame.select(
        [
            pl.col(column).cast(dtype, strict=True).alias(column)
            for column, dtype in _CANONICAL_BLOCK_SCHEMA.items()
        ]
    )
