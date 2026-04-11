"""Canonical schemas for raw and enriched block datasets."""

from __future__ import annotations

import pandera.polars as pa
import polars as pl

ENRICHED_BLOCK_SCHEMA = {
    "block_number": pl.Int64,
    "timestamp": pl.Int64,
    "base_fee_per_gas": pl.Int64,
    "gas_used": pl.Int64,
    "chain_id": pl.Int64,
    "gas_limit": pl.Int64,
}
ENRICHED_BLOCK_COLUMNS = tuple(ENRICHED_BLOCK_SCHEMA)
RAW_BLOCK_COLUMNS = tuple(column for column in ENRICHED_BLOCK_COLUMNS if column != "gas_limit")

ENRICHED_BLOCK_FRAME_SCHEMA = pa.DataFrameSchema(
    {
        column: pa.Column(dtype, nullable=False)
        for column, dtype in ENRICHED_BLOCK_SCHEMA.items()
    },
    strict=True,
    unique="block_number",
    checks=[
        pa.Check(
            lambda data: data.lazyframe.collect().height > 0,
            error="Block dataset is empty",
        ),
        pa.Check(
            lambda data: (
                data.lazyframe.select(pl.col("chain_id").n_unique()).collect().item() == 1
            ),
            error="Block dataset must contain exactly one chain_id",
        ),
    ],
)


def canonicalize_enriched_block_frame(frame: pl.DataFrame) -> pl.DataFrame:
    missing = [column for column in ENRICHED_BLOCK_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(
            "Block dataset is missing required columns for canonical enriched output: "
            + ", ".join(missing)
        )

    return frame.select(
        [
            pl.col(column).cast(dtype, strict=True).alias(column)
            for column, dtype in ENRICHED_BLOCK_SCHEMA.items()
        ]
    )
def validate_enriched_block_frame(frame: pl.DataFrame) -> None:
    ENRICHED_BLOCK_FRAME_SCHEMA.validate(frame)
