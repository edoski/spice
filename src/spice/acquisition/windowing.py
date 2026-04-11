"""History and evaluation window planning for acquisition."""

from __future__ import annotations

from collections.abc import Mapping
from math import ceil

from ..core.config import ExperimentConfig
from ..data.datasets import derive_dataset_geometry
from .cryo import TimestampRange, history_range_for_required_blocks
from .raw_validation import RawPullValidationReport


def required_history_block_count(config: ExperimentConfig) -> int:
    geometry = derive_dataset_geometry(
        lookback_seconds=config.lookback_seconds,
        max_delay_seconds=config.max_delay_seconds,
        block_time_seconds=config.chain.block_time_seconds,
    )
    return geometry.required_block_count(config.dataset.min_history_anchor_count)


def initial_history_range(
    config: ExperimentConfig,
    *,
    required_history_blocks: int,
) -> TimestampRange:
    return history_range_for_required_blocks(
        config.chain,
        config.pull,
        required_history_blocks=required_history_blocks,
        evaluation_start_timestamp=config.dataset.evaluation_start_timestamp,
    )


def expanded_history_range(
    current: TimestampRange,
    validation: RawPullValidationReport,
    *,
    config: ExperimentConfig,
    required_history_blocks: int,
) -> TimestampRange:
    missing_blocks = required_history_blocks - validation.row_count
    if missing_blocks <= 0:
        return current
    if (
        validation.first_timestamp is not None
        and validation.last_timestamp is not None
        and validation.row_count > 1
    ):
        seconds_per_block = max(
            config.chain.block_time_seconds,
            (validation.last_timestamp - validation.first_timestamp) / (validation.row_count - 1),
        )
    else:
        seconds_per_block = config.chain.block_time_seconds
    additional_blocks = missing_blocks + config.pull.chunk_size
    return TimestampRange(
        start=current.start - ceil(additional_blocks * seconds_per_block),
        end=current.end,
    )


def history_range_from_metadata(metadata: Mapping[str, object]) -> TimestampRange:
    history = metadata.get("windows", {}).get("history")
    if not isinstance(history, Mapping):
        raise ValueError("Dataset metadata is missing windows.history")
    return TimestampRange(
        start=int(history["start_timestamp"]),
        end=int(history["end_timestamp"]),
    )
