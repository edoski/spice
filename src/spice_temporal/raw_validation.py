"""Validation helpers for raw cryo block pulls."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from spice_temporal.io import iter_block_files, load_rows

RAW_BLOCK_FILENAME_RE = re.compile(
    r"^(?P<chain>[a-z0-9_]+)__blocks__(?P<start>\d+)_to_(?P<end>\d+)$"
)
CRYO_DEFAULT_CHUNK_SIZE = 1_000
EDGE_TIMESTAMP_TOLERANCE_ROWS = 1


@dataclass(slots=True)
class RawFileSummary:
    path: Path
    filename_chain: str
    range_start: int
    range_end: int
    row_count: int
    first_block_number: int
    last_block_number: int
    first_timestamp: int
    last_timestamp: int
    chain_id_mismatch_count: int
    duplicate_count: int
    non_sequential_transition_count: int
    below_start_count: int
    above_end_count: int
    internal_timestamp_violation: bool


@dataclass(slots=True)
class RawPullValidationReport:
    dataset_path: Path
    expected_start_timestamp: int
    expected_end_timestamp: int
    file_count: int = 0
    row_count: int = 0
    first_block_number: int | None = None
    last_block_number: int | None = None
    first_timestamp: int | None = None
    last_timestamp: int | None = None
    gap_count: int = 0
    overlap_count: int = 0
    duplicate_count: int = 0
    chain_id_mismatch_count: int = 0
    below_start_count: int = 0
    above_end_count: int = 0
    status: str = "clean"
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _read_lightweight_columns(path: Path) -> tuple[list[int], list[int], list[int]]:
    if path.suffix.lower() == ".parquet":
        try:
            import pyarrow.parquet as pq
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Reading parquet files requires pyarrow. Install project dependencies first."
            ) from exc

        table = pq.read_table(path, columns=["block_number", "timestamp", "chain_id"])
        return (
            [int(value) for value in table["block_number"].to_pylist()],
            [int(value) for value in table["timestamp"].to_pylist()],
            [int(value) for value in table["chain_id"].to_pylist()],
        )

    rows = load_rows(path)
    return (
        [int(row["block_number"]) for row in rows],
        [int(row["timestamp"]) for row in rows],
        [int(row["chain_id"]) for row in rows],
    )


def _summarize_file(
    path: Path,
    *,
    expected_chain_name: str,
    expected_chain_id: int,
    expected_start_timestamp: int,
    expected_end_timestamp: int,
) -> RawFileSummary:
    match = RAW_BLOCK_FILENAME_RE.match(path.stem)
    if match is None:
        raise ValueError(
            f"Malformed raw block filename: {path.name}. "
            "Expected <chain>__blocks__<start>_to_<end>."
        )

    filename_chain = match.group("chain")
    range_start = int(match.group("start"))
    range_end = int(match.group("end"))
    if filename_chain != expected_chain_name:
        raise ValueError(
            f"Raw block filename chain mismatch for {path.name}: "
            f"expected {expected_chain_name}, got {filename_chain}"
        )
    if range_end < range_start:
        raise ValueError(f"Invalid raw block filename range in {path.name}")

    block_numbers, timestamps, chain_ids = _read_lightweight_columns(path)
    if not block_numbers:
        raise ValueError(f"Raw block file is empty: {path.name}")

    below_start_count = 0
    above_end_count = 0
    first_in_range_seen = False
    above_end_started = False
    internal_timestamp_violation = False
    for timestamp in timestamps:
        if timestamp < expected_start_timestamp:
            below_start_count += 1
            if first_in_range_seen:
                internal_timestamp_violation = True
        elif timestamp >= expected_end_timestamp:
            above_end_count += 1
            above_end_started = True
        else:
            if above_end_started:
                internal_timestamp_violation = True
            first_in_range_seen = True

    duplicate_count = 0
    non_sequential_transition_count = 0
    for left, right in zip(block_numbers, block_numbers[1:], strict=False):
        if right == left:
            duplicate_count += 1
        elif right != left + 1:
            non_sequential_transition_count += 1

    return RawFileSummary(
        path=path,
        filename_chain=filename_chain,
        range_start=range_start,
        range_end=range_end,
        row_count=len(block_numbers),
        first_block_number=block_numbers[0],
        last_block_number=block_numbers[-1],
        first_timestamp=timestamps[0],
        last_timestamp=timestamps[-1],
        chain_id_mismatch_count=sum(1 for chain_id in chain_ids if chain_id != expected_chain_id),
        duplicate_count=duplicate_count,
        non_sequential_transition_count=non_sequential_transition_count,
        below_start_count=below_start_count,
        above_end_count=above_end_count,
        internal_timestamp_violation=internal_timestamp_violation,
    )


def validate_raw_pull(
    dataset_path: Path,
    *,
    expected_chain_name: str,
    expected_chain_id: int,
    expected_start_timestamp: int,
    expected_end_timestamp: int,
    expected_chunk_size: int = CRYO_DEFAULT_CHUNK_SIZE,
) -> RawPullValidationReport:
    report = RawPullValidationReport(
        dataset_path=dataset_path,
        expected_start_timestamp=expected_start_timestamp,
        expected_end_timestamp=expected_end_timestamp,
    )
    files = iter_block_files(dataset_path)
    summaries: list[RawFileSummary] = []
    for path in files:
        try:
            summaries.append(
                _summarize_file(
                    path,
                    expected_chain_name=expected_chain_name,
                    expected_chain_id=expected_chain_id,
                    expected_start_timestamp=expected_start_timestamp,
                    expected_end_timestamp=expected_end_timestamp,
                )
            )
        except ValueError as exc:
            report.errors.append(str(exc))
    summaries.sort(key=lambda summary: (summary.range_start, summary.range_end, str(summary.path)))
    report.file_count = len(summaries)

    previous_summary: RawFileSummary | None = None
    previous_last_block_number: int | None = None
    for summary in summaries:
        report.row_count += summary.row_count
        report.chain_id_mismatch_count += summary.chain_id_mismatch_count
        report.duplicate_count += summary.duplicate_count
        report.below_start_count += summary.below_start_count
        report.above_end_count += summary.above_end_count

        if report.first_block_number is None:
            report.first_block_number = summary.first_block_number
            report.first_timestamp = summary.first_timestamp
        report.last_block_number = summary.last_block_number
        report.last_timestamp = summary.last_timestamp

        expected_row_count = summary.range_end - summary.range_start + 1
        if summary.row_count != expected_row_count:
            report.errors.append(
                f"{summary.path.name}: row_count={summary.row_count} does not match "
                f"filename range size={expected_row_count}"
            )
        if summary.row_count > expected_chunk_size:
            report.errors.append(
                f"{summary.path.name}: row_count={summary.row_count} "
                f"exceeds chunk_size={expected_chunk_size}"
            )
        if summary.non_sequential_transition_count:
            report.errors.append(
                f"{summary.path.name}: detected "
                f"{summary.non_sequential_transition_count} non-sequential "
                "block transition(s) inside the file"
            )
        if summary.first_block_number != summary.range_start:
            report.errors.append(
                f"{summary.path.name}: first block {summary.first_block_number} does not match "
                f"filename start {summary.range_start}"
            )
        if summary.last_block_number != summary.range_end:
            report.errors.append(
                f"{summary.path.name}: last block {summary.last_block_number} does not match "
                f"filename end {summary.range_end}"
            )
        if summary.internal_timestamp_violation:
            report.errors.append(
                f"{summary.path.name}: timestamps drift outside the expected window "
                "away from dataset edges"
            )

        if previous_summary is not None:
            if summary.range_start > previous_summary.range_end + 1:
                report.gap_count += 1
            elif summary.range_start <= previous_summary.range_end:
                report.overlap_count += 1

        if previous_last_block_number is not None:
            if summary.first_block_number == previous_last_block_number:
                report.duplicate_count += 1
            elif summary.first_block_number < previous_last_block_number:
                report.errors.append(
                    f"{summary.path.name}: first block {summary.first_block_number} "
                    "is out of order "
                    f"after previous block {previous_last_block_number}"
                )

        previous_summary = summary
        previous_last_block_number = summary.last_block_number

    if report.gap_count:
        report.errors.append(f"Detected {report.gap_count} block-range gap(s) across files")
    if report.overlap_count:
        report.errors.append(f"Detected {report.overlap_count} overlapping file-range pair(s)")
    if report.duplicate_count:
        report.errors.append(
            f"Detected {report.duplicate_count} duplicate block_number transition(s)"
        )
    if report.chain_id_mismatch_count:
        report.errors.append(
            f"Detected {report.chain_id_mismatch_count} row(s) with chain_id different "
            f"from {expected_chain_id}"
        )

    if report.below_start_count or report.above_end_count:
        if (
            report.below_start_count <= EDGE_TIMESTAMP_TOLERANCE_ROWS
            and report.above_end_count <= EDGE_TIMESTAMP_TOLERANCE_ROWS
            and not report.errors
        ):
            report.warnings.append(
                "Observed only tiny edge timestamp drift consistent with cryo boundary resolution"
            )
        else:
            report.errors.append(
                f"Detected out-of-range timestamps: below_start={report.below_start_count}, "
                f"above_end={report.above_end_count}"
            )

    if report.errors:
        report.status = "error"
    elif report.warnings:
        report.status = "warning"
    else:
        report.status = "clean"
    return report


def format_raw_pull_validation_report(report: RawPullValidationReport) -> list[str]:
    lines = [
        f"dataset_path={report.dataset_path}",
        f"expected_start_timestamp={report.expected_start_timestamp}",
        f"expected_end_timestamp={report.expected_end_timestamp}",
        f"file_count={report.file_count}",
        f"row_count={report.row_count}",
        f"first_block_number={report.first_block_number}",
        f"last_block_number={report.last_block_number}",
        f"first_timestamp={report.first_timestamp}",
        f"last_timestamp={report.last_timestamp}",
        f"gap_count={report.gap_count}",
        f"overlap_count={report.overlap_count}",
        f"duplicate_count={report.duplicate_count}",
        f"chain_id_mismatch_count={report.chain_id_mismatch_count}",
        f"below_start_count={report.below_start_count}",
        f"above_end_count={report.above_end_count}",
        f"status={report.status}",
    ]
    lines.extend(f"warning={warning}" for warning in report.warnings)
    lines.extend(f"error={error}" for error in report.errors)
    return lines
