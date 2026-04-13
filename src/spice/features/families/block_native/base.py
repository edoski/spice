"""Block-native base Hamilton feature nodes."""

from __future__ import annotations

import math

import numpy as np
import polars as pl
from hamilton.function_modifiers import tag
from numpy.typing import NDArray

FloatVector = NDArray[np.float64]
IntVector = NDArray[np.int64]


def sorted_blocks(blocks: pl.DataFrame) -> pl.DataFrame:
    return blocks.sort("block_number")


def block_numbers(sorted_blocks: pl.DataFrame) -> IntVector:
    return sorted_blocks["block_number"].cast(pl.Int64).to_numpy().astype(np.int64, copy=False)


def timestamps(sorted_blocks: pl.DataFrame) -> IntVector:
    return sorted_blocks["timestamp"].cast(pl.Int64).to_numpy().astype(np.int64, copy=False)


def dataset_origin_block_number(block_numbers: IntVector) -> int:
    if block_numbers.size == 0:
        raise ValueError("block_numbers must be non-empty")
    return int(block_numbers[0])


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="0")
def log_base_fee(sorted_blocks: pl.DataFrame) -> FloatVector:
    return (
        sorted_blocks["base_fee_per_gas"]
        .cast(pl.Float64)
        .clip(lower_bound=1.0)
        .log()
        .to_numpy()
        .astype(np.float64, copy=False)
    )


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="0")
def gas_utilization(sorted_blocks: pl.DataFrame) -> FloatVector:
    return (
        sorted_blocks["gas_used"].cast(pl.Float64) / sorted_blocks["gas_limit"].cast(pl.Float64)
    ).to_numpy().astype(np.float64, copy=False)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="0")
def hour_sin(timestamps: IntVector) -> FloatVector:
    hours = (timestamps // 3600) % 24
    return np.sin(2.0 * math.pi * hours.astype(np.float64, copy=False) / 24.0)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="0")
def hour_cos(timestamps: IntVector) -> FloatVector:
    hours = (timestamps // 3600) % 24
    return np.cos(2.0 * math.pi * hours.astype(np.float64, copy=False) / 24.0)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="0")
def weekday_sin(timestamps: IntVector) -> FloatVector:
    weekdays = ((timestamps // 86_400) + 4) % 7
    return np.sin(2.0 * math.pi * weekdays.astype(np.float64, copy=False) / 7.0)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="0")
def weekday_cos(timestamps: IntVector) -> FloatVector:
    weekdays = ((timestamps // 86_400) + 4) % 7
    return np.cos(2.0 * math.pi * weekdays.astype(np.float64, copy=False) / 7.0)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="0")
def elapsed_blocks(
    block_numbers: IntVector,
    dataset_origin_block_number: int,
) -> FloatVector:
    return block_numbers.astype(np.float64, copy=False) - float(dataset_origin_block_number)
