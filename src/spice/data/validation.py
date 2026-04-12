"""Shared validation for canonical block datasets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import polars as pl
from pydantic import Field

from .validation_base import ValidationModel, ValidationStatus, finalize_validation_status

VALIDATION_COLUMNS = ("block_number", "timestamp", "chain_id")


@dataclass(slots=True)
class BlockFrameSummary:
    row_count: int
    first_block_number: int
    last_block_number: int
    first_timestamp: int
    last_timestamp: int
    chain_ids: tuple[int, ...]
    duplicate_count: int
    gap_count: int


@dataclass(slots=True)
class ExactWindowCounts:
    below_start_count: int
    above_end_count: int


@dataclass(slots=True)
class BlockFrameAssessment:
    chain_id: int | None
    errors: tuple[str, ...]


class BlockDatasetValidationReport(ValidationModel):
    dataset_path: Path
    expected_start_timestamp: int | None = None
    expected_end_timestamp: int | None = None
    row_count: int = 0
    first_block_number: int | None = None
    last_block_number: int | None = None
    first_timestamp: int | None = None
    last_timestamp: int | None = None
    chain_id: int | None = None
    duplicate_count: int = 0
    gap_count: int = 0
    below_start_count: int = 0
    above_end_count: int = 0
    status: ValidationStatus = "clean"
    errors: list[str] = Field(default_factory=list)


def _coerce_validation_frame(frame: pl.DataFrame) -> pl.DataFrame:
    missing = [column for column in VALIDATION_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(
            "Block dataset is missing required validation columns: " + ", ".join(missing)
        )
    return frame.select(
        [
            pl.col("block_number").cast(pl.Int64, strict=True),
            pl.col("timestamp").cast(pl.Int64, strict=True),
            pl.col("chain_id").cast(pl.Int64, strict=True),
        ]
    ).sort("block_number")


def summarize_block_frame(frame: pl.DataFrame) -> BlockFrameSummary:
    validation_frame = _coerce_validation_frame(frame)
    if validation_frame.height == 0:
        raise ValueError("Block dataset is empty")

    block_numbers = [int(value) for value in validation_frame["block_number"].to_list()]
    timestamps = [int(value) for value in validation_frame["timestamp"].to_list()]
    chain_ids = tuple(sorted({int(value) for value in validation_frame["chain_id"].to_list()}))

    duplicate_count = 0
    gap_count = 0
    for left, right in zip(block_numbers, block_numbers[1:], strict=False):
        if right == left:
            duplicate_count += 1
        elif right != left + 1:
            gap_count += 1

    return BlockFrameSummary(
        row_count=len(block_numbers),
        first_block_number=block_numbers[0],
        last_block_number=block_numbers[-1],
        first_timestamp=timestamps[0],
        last_timestamp=timestamps[-1],
        chain_ids=chain_ids,
        duplicate_count=duplicate_count,
        gap_count=gap_count,
    )


def assess_block_frame_summary(
    summary: BlockFrameSummary,
    *,
    expected_chain_id: int,
) -> BlockFrameAssessment:
    errors: list[str] = []
    chain_id: int | None = None
    if len(summary.chain_ids) != 1:
        errors.append("Block dataset must contain exactly one chain_id")
    else:
        chain_id = summary.chain_ids[0]
        if chain_id != expected_chain_id:
            errors.append(
                f"Block dataset chain_id mismatch: expected {expected_chain_id}, got {chain_id}"
            )

    if summary.duplicate_count:
        errors.append(
            f"Detected {summary.duplicate_count} duplicate block_number transition(s)"
        )
    if summary.gap_count:
        errors.append(f"Detected {summary.gap_count} block-number gap(s)")
    return BlockFrameAssessment(chain_id=chain_id, errors=tuple(errors))


def exact_window_counts(
    summary: BlockFrameSummary,
    *,
    frame: pl.DataFrame,
    expected_start_timestamp: int,
    expected_end_timestamp: int,
) -> ExactWindowCounts:
    timestamps = [int(value) for value in frame["timestamp"].to_list()]
    return ExactWindowCounts(
        below_start_count=sum(
            1 for timestamp in timestamps if timestamp < expected_start_timestamp
        ),
        above_end_count=sum(1 for timestamp in timestamps if timestamp >= expected_end_timestamp),
    )


def _apply_summary(
    report: BlockDatasetValidationReport,
    summary: BlockFrameSummary,
    *,
    expected_chain_id: int,
) -> None:
    report.row_count = summary.row_count
    report.first_block_number = summary.first_block_number
    report.last_block_number = summary.last_block_number
    report.first_timestamp = summary.first_timestamp
    report.last_timestamp = summary.last_timestamp
    report.duplicate_count = summary.duplicate_count
    report.gap_count = summary.gap_count

    assessment = assess_block_frame_summary(
        summary,
        expected_chain_id=expected_chain_id,
    )
    report.chain_id = assessment.chain_id
    report.errors.extend(assessment.errors)


def validate_contiguous_block_frame(
    frame: pl.DataFrame,
    *,
    dataset_path: Path,
    expected_chain_id: int,
) -> BlockDatasetValidationReport:
    report = BlockDatasetValidationReport(dataset_path=dataset_path)
    try:
        summary = summarize_block_frame(frame)
    except Exception as exc:
        report.errors.append(str(exc))
        finalize_validation_status(report)
        return report

    _apply_summary(report, summary, expected_chain_id=expected_chain_id)
    finalize_validation_status(report)
    return report


def validate_exact_window_frame(
    frame: pl.DataFrame,
    *,
    dataset_path: Path,
    expected_chain_id: int,
    expected_start_timestamp: int,
    expected_end_timestamp: int,
) -> BlockDatasetValidationReport:
    report = BlockDatasetValidationReport(
        dataset_path=dataset_path,
        expected_start_timestamp=expected_start_timestamp,
        expected_end_timestamp=expected_end_timestamp,
    )
    try:
        validation_frame = _coerce_validation_frame(frame)
        summary = summarize_block_frame(validation_frame)
    except Exception as exc:
        report.errors.append(str(exc))
        finalize_validation_status(report)
        return report

    _apply_summary(report, summary, expected_chain_id=expected_chain_id)
    counts = exact_window_counts(
        summary,
        frame=validation_frame,
        expected_start_timestamp=expected_start_timestamp,
        expected_end_timestamp=expected_end_timestamp,
    )
    report.below_start_count = counts.below_start_count
    report.above_end_count = counts.above_end_count
    if report.below_start_count or report.above_end_count:
        report.errors.append(
            f"Detected out-of-range timestamps: below_start={report.below_start_count}, "
            f"above_end={report.above_end_count}"
        )
    finalize_validation_status(report)
    return report
