"""Canonical schemas for block datasets."""

from __future__ import annotations

import pandera.polars as pa
import polars as pl

BLOCK_SCHEMA = {
    "block_number": pl.Int64,
    "timestamp": pl.Int64,
    "base_fee_per_gas": pl.Int64,
    "gas_used": pl.Int64,
    "chain_id": pl.Int64,
    "gas_limit": pl.Int64,
}
BLOCK_COLUMNS = tuple(BLOCK_SCHEMA)

BLOCK_FRAME_SCHEMA = pa.DataFrameSchema(
    {
        column: pa.Column(dtype, nullable=False)
        for column, dtype in BLOCK_SCHEMA.items()
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


def canonicalize_block_frame(frame: pl.DataFrame) -> pl.DataFrame:
    missing = [column for column in BLOCK_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(
            "Block dataset is missing required columns for canonical output: "
            + ", ".join(missing)
        )

    return frame.select(
        [
            pl.col(column).cast(dtype, strict=True).alias(column)
            for column, dtype in BLOCK_SCHEMA.items()
        ]
    )


def validate_block_frame(frame: pl.DataFrame) -> None:
    BLOCK_FRAME_SCHEMA.validate(frame)
