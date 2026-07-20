"""Canonical Corpus values and block schema."""

from __future__ import annotations

import polars as pl
from pydantic import BaseModel, ConfigDict, Field

from ..config import CorpusRequest


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
