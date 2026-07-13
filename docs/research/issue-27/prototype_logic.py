"""Disposable exact-root acquisition prototype for GitHub issue 27.

This module uses synthetic blocks and OS-temp roots only. It is not production code.
"""

from __future__ import annotations

import asyncio
import ctypes
import errno
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, cast

import polars as pl

HEX_64 = re.compile(r"[0-9a-f]{64}\Z")
SOURCE_SCHEMA = {
    "block_number": pl.Int64,
    "block_hash": pl.String,
    "parent_hash": pl.String,
    "timestamp": pl.Int64,
    "chain_id": pl.Int64,
    "base_fee_per_gas": pl.Int64,
    "gas_used": pl.Int64,
    "gas_limit": pl.Int64,
    "tx_count": pl.Int64,
}
STAGE_SCHEMA = {**SOURCE_SCHEMA, "definition_sha256": pl.String}
PAYLOAD_SCHEMA = {
    name: dtype
    for name, dtype in SOURCE_SCHEMA.items()
    if name not in {"block_hash", "parent_hash"}
}
SOURCE_COLUMNS = tuple(SOURCE_SCHEMA)
STAGE_COLUMNS = tuple(STAGE_SCHEMA)
PAYLOAD_COLUMNS = tuple(PAYLOAD_SCHEMA)
MANIFEST_KEYS = {
    "corpus_id",
    "definition",
    "files",
    "finalized_block_number",
    "finalized_block_hash",
}
PROTOTYPE_CANONICAL_CHUNK_ROWS = 3


class ContractError(RuntimeError):
    """The candidate cannot satisfy the exact corpus contract."""


class ReacquireRequired(ContractError):
    """Existing bytes failed new validation and must not be repaired."""


@dataclass(frozen=True, slots=True)
class Regime:
    name: str
    start_block: int

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ContractError("regime.name must be a non-empty string")
        _require_exact_int("regime.start_block", self.start_block, minimum=0)


@dataclass(frozen=True, slots=True)
class CorpusDefinition:
    chain_id: int
    regime: Regime
    first_block: int
    last_block: int

    def __post_init__(self) -> None:
        for name, value in (
            ("chain_id", self.chain_id),
            ("regime.start_block", self.regime.start_block),
            ("first_block", self.first_block),
            ("last_block", self.last_block),
        ):
            _require_exact_int(name, value, minimum=0)
        if self.first_block < self.regime.start_block:
            raise ContractError("first_block precedes regime.start_block")
        if self.last_block < self.first_block:
            raise ContractError("last_block precedes first_block")

    def payload(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "first_block": self.first_block,
            "last_block": self.last_block,
            "regime": {
                "name": self.regime.name,
                "start_block": self.regime.start_block,
            },
        }


@dataclass(frozen=True, slots=True)
class Header:
    number: int
    block_hash: str
    parent_hash: str


@dataclass(frozen=True, slots=True)
class StageAssessment:
    next_block: int
    complete: bool
    row_count: int
    last_hash: str | None
    last_timestamp: int | None
    relative_files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PayloadAssessment:
    complete: bool
    row_count: int
    relative_files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PullObservation:
    resumed_at: int
    completed_through: int
    provider_calls: int
    acquisition_retries: int
    max_live_rows: int


@dataclass(frozen=True, slots=True)
class Candidate:
    path: Path
    corpus_id: str
    identity_bytes: bytes


@dataclass(frozen=True, slots=True)
class Publication:
    outcome: str
    canonical_path: Path
    candidate_preserved: bool


@dataclass(slots=True)
class SyntheticProvider:
    """A fake provider seam. Any real retry stays behind this seam."""

    chain_id: int
    last_available: int
    finalized_number: int
    terminal_fail_blocks: set[int] = field(default_factory=set)
    anchor_reread_mismatch: bool = False
    calls: dict[int, int] = field(default_factory=dict, init=False)
    cancelled_calls: int = field(default=0, init=False)
    _rows: dict[int, dict[str, object]] = field(default_factory=dict, init=False)
    _finalized_was_read: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.finalized_number > self.last_available:
            raise ValueError("finalized_number exceeds synthetic range")
        parent_hash = hashlib.sha256(b"synthetic-parent").hexdigest()
        for number in range(self.last_available + 1):
            block_hash = hashlib.sha256(
                f"{self.chain_id}:{number}:{parent_hash}".encode()
            ).hexdigest()
            self._rows[number] = {
                "block_number": number,
                "block_hash": block_hash,
                "parent_hash": parent_hash,
                "timestamp": 1_700_000_000 + number * 2,
                "chain_id": self.chain_id,
                "base_fee_per_gas": 1_000_000_000 + number,
                "gas_used": 15_000_000 + number,
                "gas_limit": 30_000_000,
                "tx_count": 100 + number % 11,
            }
            parent_hash = block_hash

    async def block(self, number: int) -> dict[str, object]:
        self.calls[number] = self.calls.get(number, 0) + 1
        try:
            # Later blocks often finish first. Acquisition must still write in order.
            await asyncio.sleep((2 - number % 3) * 0.002)
        except asyncio.CancelledError:
            self.cancelled_calls += 1
            raise
        if number in self.terminal_fail_blocks:
            raise OSError(f"provider exhausted its runtime retry policy for block {number}")
        try:
            return dict(self._rows[number])
        except KeyError as exc:
            raise ContractError(f"synthetic block {number} is unavailable") from exc

    async def header(self, number: int) -> Header:
        row = await self.block(number)
        block_hash = str(row["block_hash"])
        if (
            self.anchor_reread_mismatch
            and self._finalized_was_read
            and number == self.finalized_number
        ):
            block_hash = hashlib.sha256(f"changed:{block_hash}".encode()).hexdigest()
        return Header(number, block_hash, str(row["parent_hash"]))

    async def finalized_header(self) -> Header:
        row = self._rows[self.finalized_number]
        self._finalized_was_read = True
        return Header(
            self.finalized_number,
            str(row["block_hash"]),
            str(row["parent_hash"]),
        )


def _require_exact_int(name: str, value: object, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractError(f"{name} must be an exact integer")
    if minimum is not None and value < minimum:
        raise ContractError(f"{name} must be >= {minimum}")
    return value


def _require_hash(name: str, value: object) -> str:
    if not isinstance(value, str) or HEX_64.fullmatch(value) is None:
        raise ContractError(f"{name} must be 64 lowercase hexadecimal characters")
    return value


def _definition_sha256(definition: CorpusDefinition) -> str:
    canonical_bytes = json.dumps(
        definition.payload(),
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


def _require_schema(frame: pl.DataFrame, schema: dict[str, pl.DataType], label: str) -> None:
    if tuple(frame.columns) != tuple(schema):
        raise ContractError(
            f"{label} columns mismatch: expected {tuple(schema)}, got {tuple(frame.columns)}"
        )
    actual = dict(frame.schema)
    if actual != schema:
        raise ContractError(f"{label} schema mismatch: expected {schema}, got {actual}")
    if frame.height == 0:
        raise ContractError(f"{label} must not be empty")
    if any(frame[column].null_count() for column in frame.columns):
        raise ContractError(f"{label} contains null values")


def _validate_payload_row(
    row: dict[str, object],
    definition: CorpusDefinition,
    expected_number: int,
    *,
    label: str,
) -> int:
    if set(row) != set(PAYLOAD_COLUMNS):
        raise ContractError(f"{label} row keys mismatch")
    number = _require_exact_int("block_number", row["block_number"], minimum=0)
    if number != expected_number or number > definition.last_block:
        raise ContractError(
            f"{label} block order/range mismatch: expected {expected_number}, got {number}"
        )
    chain_id = _require_exact_int("chain_id", row["chain_id"], minimum=0)
    if chain_id != definition.chain_id:
        raise ContractError(
            f"{label} chain_id mismatch at block {number}: "
            f"expected {definition.chain_id}, got {chain_id}"
        )
    timestamp = _require_exact_int("timestamp", row["timestamp"], minimum=0)
    domain_values: dict[str, int] = {}
    for field_name in (
        "base_fee_per_gas",
        "gas_used",
        "gas_limit",
        "tx_count",
    ):
        value = _require_exact_int(field_name, row[field_name], minimum=0)
        domain_values[field_name] = value
        if field_name in {"base_fee_per_gas", "gas_limit"} and value == 0:
            raise ContractError(f"{field_name} must be positive at block {number}")
    if domain_values["gas_used"] > domain_values["gas_limit"]:
        raise ContractError(f"gas_used exceeds gas_limit at block {number}")
    return timestamp


def _validate_source_row(
    row: dict[str, object],
    definition: CorpusDefinition,
    expected_number: int,
    *,
    label: str,
) -> tuple[str, str, int]:
    if set(row) != set(SOURCE_COLUMNS):
        raise ContractError(f"{label} row keys mismatch")
    payload_row = {name: row[name] for name in PAYLOAD_COLUMNS}
    timestamp = _validate_payload_row(
        payload_row,
        definition,
        expected_number,
        label=label,
    )
    block_hash = _require_hash("block_hash", row["block_hash"])
    parent_hash = _require_hash("parent_hash", row["parent_hash"])
    return block_hash, parent_hash, timestamp


def _validate_stage_row(
    row: dict[str, object],
    definition: CorpusDefinition,
    expected_number: int,
    *,
    label: str,
) -> tuple[str, str, int]:
    if set(row) != set(STAGE_COLUMNS):
        raise ContractError(f"{label} row keys mismatch")
    binding = _require_hash("definition_sha256", row["definition_sha256"])
    expected_binding = _definition_sha256(definition)
    if binding != expected_binding:
        raise ContractError(
            f"{label} definition_sha256 mismatch: expected {expected_binding}, got {binding}"
        )
    source_row = {name: row[name] for name in SOURCE_COLUMNS}
    return _validate_source_row(
        source_row,
        definition,
        expected_number,
        label=label,
    )


def _chunk_name(first_block: int, last_block: int) -> str:
    return f"{first_block:020d}-{last_block:020d}.parquet"


def _parse_chunk_name(path: Path) -> tuple[int, int]:
    match = re.fullmatch(r"(\d{20})-(\d{20})\.parquet", path.name)
    if match is None:
        raise ContractError(f"invalid chunk path: {path.name}")
    return int(match.group(1)), int(match.group(2))


def _sync_file(path: Path) -> None:
    _require_regular_file(path, "sync file")
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _sync_dir(path: Path) -> None:
    _require_real_directory(path, "sync directory")
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_parquet_no_replace(path: Path, frame: pl.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    try:
        frame.write_parquet(temporary, compression="zstd", statistics=True)
        _sync_file(temporary)
        os.link(temporary, path)
        _sync_dir(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _path_exists(path: Path) -> bool:
    return os.path.lexists(path)


def _require_regular_file(path: Path, label: str) -> None:
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise ContractError(f"{label} is unavailable: {path}") from exc
    if not stat.S_ISREG(mode):
        raise ContractError(f"{label} must be a direct regular file: {path}")


def _require_real_directory(path: Path, label: str) -> None:
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise ContractError(f"{label} is unavailable: {path}") from exc
    if not stat.S_ISDIR(mode):
        raise ContractError(f"{label} must be a direct directory: {path}")


def _read_chunks(directory: Path) -> list[Path]:
    if not _path_exists(directory):
        return []
    _require_real_directory(directory, "chunk directory")
    unexpected = []
    for entry in directory.iterdir():
        try:
            mode = entry.lstat().st_mode
        except OSError:
            unexpected.append(entry)
            continue
        if not stat.S_ISREG(mode):
            unexpected.append(entry)
    if unexpected:
        raise ContractError(f"unexpected non-regular chunk entries: {unexpected}")
    files = sorted(directory.iterdir(), key=lambda path: path.name.encode("utf-8"))
    for path in files:
        if path.suffix != ".parquet":
            raise ContractError(f"unexpected stage file: {path.name}")
        _parse_chunk_name(path)
    return files


def inspect_stage(stage_blocks: Path, definition: CorpusDefinition) -> StageAssessment:
    expected_number = definition.first_block
    previous_hash: str | None = None
    previous_timestamp: int | None = None
    row_count = 0
    relative_files: list[str] = []

    for path in _read_chunks(stage_blocks):
        frame = pl.read_parquet(path)
        _require_schema(frame, STAGE_SCHEMA, path.name)
        first_from_name, last_from_name = _parse_chunk_name(path)
        if first_from_name != expected_number:
            raise ContractError(
                f"stage is not an exact prefix: expected block {expected_number}, "
                f"got chunk {path.name}"
            )
        rows = frame.iter_rows(named=True)
        first_seen: int | None = None
        last_seen: int | None = None
        for row in rows:
            number = expected_number
            block_hash, parent_hash, timestamp = _validate_stage_row(
                row,
                definition,
                number,
                label="stage",
            )
            if previous_hash is not None and parent_hash != previous_hash:
                raise ContractError(f"parent link mismatch at block {number}")
            if previous_timestamp is not None and timestamp < previous_timestamp:
                raise ContractError(f"timestamp decreases at block {number}")
            first_seen = number if first_seen is None else first_seen
            last_seen = number
            expected_number += 1
            row_count += 1
            previous_hash = block_hash
            previous_timestamp = timestamp
        if (first_seen, last_seen) != (first_from_name, last_from_name):
            raise ContractError(f"chunk filename does not match its rows: {path.name}")
        relative_files.append(path.name)

    return StageAssessment(
        next_block=expected_number,
        complete=expected_number == definition.last_block + 1,
        row_count=row_count,
        last_hash=previous_hash,
        last_timestamp=previous_timestamp,
        relative_files=tuple(relative_files),
    )


def inspect_payload(payload_blocks: Path, definition: CorpusDefinition) -> PayloadAssessment:
    expected_number = definition.first_block
    previous_timestamp: int | None = None
    row_count = 0
    relative_files: list[str] = []

    for path in _read_chunks(payload_blocks):
        frame = pl.read_parquet(path)
        _require_schema(frame, PAYLOAD_SCHEMA, path.name)
        first_from_name, last_from_name = _parse_chunk_name(path)
        if first_from_name != expected_number:
            raise ContractError(
                f"payload is not exact and contiguous: expected block {expected_number}, "
                f"got chunk {path.name}"
            )
        first_seen: int | None = None
        last_seen: int | None = None
        for row in frame.iter_rows(named=True):
            number = expected_number
            timestamp = _validate_payload_row(
                row,
                definition,
                number,
                label="payload",
            )
            if previous_timestamp is not None and timestamp < previous_timestamp:
                raise ContractError(f"payload timestamp decreases at block {number}")
            first_seen = number if first_seen is None else first_seen
            last_seen = number
            expected_number += 1
            row_count += 1
            previous_timestamp = timestamp
        if (first_seen, last_seen) != (first_from_name, last_from_name):
            raise ContractError(f"payload chunk filename does not match rows: {path.name}")
        relative_files.append(path.name)

    return PayloadAssessment(
        complete=expected_number == definition.last_block + 1,
        row_count=row_count,
        relative_files=tuple(relative_files),
    )


def _stage_frame(
    rows: list[dict[str, object]],
    definition: CorpusDefinition,
) -> pl.DataFrame:
    binding = _definition_sha256(definition)
    bound_rows = [{**row, "definition_sha256": binding} for row in rows]
    return pl.DataFrame(bound_rows, schema=STAGE_SCHEMA, orient="row")


def _payload_frame(rows: list[dict[str, object]]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=PAYLOAD_SCHEMA, orient="row")


async def acquire_missing(
    definition: CorpusDefinition,
    stage_blocks: Path,
    provider: SyntheticProvider,
    *,
    chunk_rows: int,
    concurrency: int,
) -> PullObservation:
    if chunk_rows <= 0 or concurrency <= 0:
        raise ValueError("chunk_rows and concurrency must be positive runtime values")
    assessment = inspect_stage(stage_blocks, definition)
    resumed_at = assessment.next_block
    if assessment.complete:
        return PullObservation(resumed_at, definition.last_block, 0, 0, 0)

    next_write = resumed_at
    next_schedule = resumed_at
    previous_hash = assessment.last_hash
    previous_timestamp = assessment.last_timestamp
    in_flight: dict[asyncio.Task[dict[str, object]], int] = {}
    ready: dict[int, dict[str, object]] = {}
    chunk: list[dict[str, object]] = []
    max_live_rows = 0
    calls_before = sum(provider.calls.values())

    try:
        while next_write <= definition.last_block:
            # The numeric window bounds completed-result memory even if its first call is slow.
            window_end = min(definition.last_block + 1, next_write + concurrency)
            while next_schedule < window_end and len(in_flight) < concurrency:
                task = asyncio.create_task(provider.block(next_schedule))
                in_flight[task] = next_schedule
                next_schedule += 1
            if not in_flight:
                raise ContractError("ordered acquisition stalled")
            done, _ = await asyncio.wait(in_flight, return_when=asyncio.FIRST_COMPLETED)
            terminal: BaseException | None = None
            completed: list[tuple[int, dict[str, object]]] = []
            for task in done:
                requested = in_flight.pop(task)
                try:
                    row = task.result()
                except BaseException as exc:  # cancellation below must include every task
                    terminal = terminal or exc
                    continue
                try:
                    _validate_source_row(
                        row,
                        definition,
                        requested,
                        label="provider",
                    )
                except ContractError as exc:
                    terminal = terminal or exc
                    continue
                completed.append((requested, row))
            if terminal is not None:
                raise ContractError(str(terminal)) from terminal
            for requested, row in completed:
                ready[requested] = row
            while next_write in ready:
                row = ready.pop(next_write)
                block_hash, parent_hash, timestamp = _validate_source_row(
                    row,
                    definition,
                    next_write,
                    label="provider",
                )
                if previous_hash is not None and parent_hash != previous_hash:
                    raise ContractError(f"provider parent link mismatch at block {next_write}")
                if previous_timestamp is not None and timestamp < previous_timestamp:
                    raise ContractError(f"provider timestamp decreases at block {next_write}")
                chunk.append(row)
                previous_hash = block_hash
                previous_timestamp = timestamp
                next_write += 1
                if len(chunk) == chunk_rows:
                    first = _require_exact_int("block_number", chunk[0]["block_number"])
                    last = _require_exact_int("block_number", chunk[-1]["block_number"])
                    _write_parquet_no_replace(
                        stage_blocks / _chunk_name(first, last),
                        _stage_frame(chunk, definition),
                    )
                    chunk = []
            max_live_rows = max(max_live_rows, len(in_flight) + len(ready) + len(chunk))

        if chunk:
            first = _require_exact_int("block_number", chunk[0]["block_number"])
            last = _require_exact_int("block_number", chunk[-1]["block_number"])
            _write_parquet_no_replace(
                stage_blocks / _chunk_name(first, last),
                _stage_frame(chunk, definition),
            )
    finally:
        for task in in_flight:
            task.cancel()
        if in_flight:
            await asyncio.gather(*in_flight, return_exceptions=True)

    final = inspect_stage(stage_blocks, definition)
    if not final.complete:
        raise ContractError("acquisition returned without a complete exact prefix")
    return PullObservation(
        resumed_at=resumed_at,
        completed_through=definition.last_block,
        provider_calls=sum(provider.calls.values()) - calls_before,
        acquisition_retries=0,
        max_live_rows=max_live_rows,
    )


async def import_existing_payload(
    existing_blocks: Path,
    definition: CorpusDefinition,
    stage_blocks: Path,
    provider: SyntheticProvider,
) -> None:
    """Validate old Parquet through fresh row/header comparison; never repair it."""

    try:
        target = inspect_stage(stage_blocks, definition)
    except Exception as exc:
        raise ReacquireRequired(
            f"import target failed definition-bound validation; use a fresh stage: {exc}"
        ) from exc
    if target.row_count != 0:
        raise ReacquireRequired("existing Parquet import requires a fresh empty target stage")

    expected = definition.first_block
    previous_hash: str | None = None
    previous_timestamp: int | None = None
    files = _read_chunks(existing_blocks)
    if not files:
        raise ReacquireRequired("existing Parquet has no payload files")
    try:
        for path in files:
            frame = pl.read_parquet(path)
            _require_schema(frame, PAYLOAD_SCHEMA, path.name)
            first_from_name, last_from_name = _parse_chunk_name(path)
            if first_from_name != expected:
                raise ContractError("existing Parquet is not an exact contiguous prefix")
            enriched: list[dict[str, object]] = []
            for payload_row in frame.iter_rows(named=True):
                number = expected
                _validate_payload_row(
                    payload_row,
                    definition,
                    number,
                    label="existing",
                )
                source_row = await provider.block(number)
                block_hash, parent_hash, timestamp = _validate_source_row(
                    source_row,
                    definition,
                    number,
                    label="fresh source",
                )
                for field in PAYLOAD_COLUMNS:
                    if payload_row[field] != source_row[field]:
                        raise ContractError(
                            f"existing {field} differs from fresh source at block {number}"
                        )
                if previous_hash is not None and parent_hash != previous_hash:
                    raise ContractError(f"fresh parent link mismatch at block {number}")
                if previous_timestamp is not None and timestamp < previous_timestamp:
                    raise ContractError(f"fresh timestamp decreases at block {number}")
                enriched.append(source_row)
                previous_hash = block_hash
                previous_timestamp = timestamp
                expected += 1
            enriched_bounds = (
                _require_exact_int("block_number", enriched[0]["block_number"]),
                _require_exact_int("block_number", enriched[-1]["block_number"]),
            )
            if enriched_bounds != (
                first_from_name,
                last_from_name,
            ):
                raise ContractError(f"existing chunk name mismatch: {path.name}")
            _write_parquet_no_replace(
                stage_blocks / path.name,
                _stage_frame(enriched, definition),
            )
        if expected != definition.last_block + 1:
            raise ContractError("existing Parquet does not cover the exact definition")
        if not inspect_stage(stage_blocks, definition).complete:
            raise ContractError("fresh stage did not validate")
    except Exception as exc:
        message = f"fresh validation failed; reacquire, do not repair: {exc}"
        raise ReacquireRequired(message) from exc


async def _validate_finality(
    definition: CorpusDefinition,
    assessment: StageAssessment,
    provider: SyntheticProvider,
) -> Header:
    if not assessment.complete or assessment.last_hash is None:
        raise ContractError("only a complete validated stage can finalize")
    anchor = _validate_header(await provider.finalized_header(), label="finalized anchor")
    if anchor.number < definition.last_block:
        raise ContractError("finalized anchor precedes corpus last block")

    previous_hash = assessment.last_hash
    if anchor.number == definition.last_block:
        if anchor.block_hash != previous_hash:
            raise ContractError("corpus last-block hash differs from finalized anchor")
    else:
        # Stream only the missing ancestry headers. Memory stays O(1).
        for number in range(definition.last_block + 1, anchor.number):
            header = _validate_header(
                await provider.header(number),
                expected_number=number,
                label="ancestry header",
            )
            if header.parent_hash != previous_hash:
                raise ContractError(f"finalized ancestry breaks at block {number}")
            previous_hash = header.block_hash
        if anchor.parent_hash != previous_hash:
            raise ContractError("corpus last block is not an ancestor of finalized anchor")

    reread = _validate_header(
        await provider.header(anchor.number),
        expected_number=anchor.number,
        label="numbered anchor reread",
    )
    if reread != anchor:
        raise ContractError("finalized anchor changed on immediate numbered reread")
    return anchor


def _validate_header(
    header: Header,
    *,
    label: str,
    expected_number: int | None = None,
) -> Header:
    if not isinstance(header, Header):
        raise ContractError(f"{label} has the wrong shape")
    number = _require_exact_int(f"{label}.number", header.number, minimum=0)
    block_hash = _require_hash(f"{label}.block_hash", header.block_hash)
    parent_hash = _require_hash(f"{label}.parent_hash", header.parent_hash)
    if expected_number is not None and number != expected_number:
        raise ContractError(
            f"{label} number mismatch: expected {expected_number}, got {number}"
        )
    return Header(number, block_hash, parent_hash)


def _file_row(path: Path, relative_path: str) -> dict[str, object]:
    _require_regular_file(path, "payload file")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "relative_path": relative_path,
        "byte_length": path.stat().st_size,
        "full_sha256": digest.hexdigest(),
    }


def _identity_bytes(
    definition: CorpusDefinition,
    file_rows: object,
) -> bytes:
    if not isinstance(file_rows, list):
        raise ContractError("inventory must be a list")
    expected_keys = {"relative_path", "byte_length", "full_sha256"}
    previous: bytes | None = None
    checked_rows: list[dict[str, object]] = []
    for item in file_rows:
        if not isinstance(item, dict):
            raise ContractError("inventory rows must be objects")
        row = cast(dict[str, object], item)
        if set(row) != expected_keys:
            raise ContractError("inventory row keys mismatch")
        relative_path = row["relative_path"]
        if not isinstance(relative_path, str):
            raise ContractError("inventory path must be a string")
        pure_path = PurePosixPath(relative_path)
        if (
            "\\" in relative_path
            or "\x00" in relative_path
            or pure_path.is_absolute()
            or pure_path.as_posix() != relative_path
            or len(pure_path.parts) != 2
            or pure_path.parts[0] != "blocks"
            or any(part in {"", ".", ".."} for part in pure_path.parts)
        ):
            raise ContractError(
                "inventory paths must be direct relative POSIX files under blocks/"
            )
        _parse_chunk_name(Path(pure_path.parts[1]))
        path_bytes = relative_path.encode("utf-8")
        if previous is not None and path_bytes <= previous:
            raise ContractError("inventory rows must be strictly UTF-8-byte sorted")
        previous = path_bytes
        _require_exact_int("byte_length", row["byte_length"], minimum=0)
        _require_hash("full_sha256", row["full_sha256"])
        checked_rows.append(row)
    projection = {"definition": definition.payload(), "files": checked_rows}
    return json.dumps(
        projection,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _write_manifest(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=True, allow_nan=False, sort_keys=True, indent=2)
        + "\n",
        encoding="utf-8",
    )
    _sync_file(path)


def _require_package_shape(root: Path) -> None:
    _require_real_directory(root, "corpus package")
    entries = {entry.name: entry for entry in root.iterdir()}
    if set(entries) != {"blocks", "manifest.json"}:
        raise ContractError("corpus package entries must be exactly blocks and manifest.json")
    _require_real_directory(entries["blocks"], "payload directory")
    _require_regular_file(entries["manifest.json"], "manifest")


def _reject_json_constant(value: str) -> object:
    raise ContractError(f"manifest contains invalid JSON constant {value}")


def _strict_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, value in pairs:
        if key in payload:
            raise ContractError(f"manifest contains duplicate key {key}")
        payload[key] = value
    return payload


async def build_candidate(
    definition: CorpusDefinition,
    stage_blocks: Path,
    corpora_root: Path,
    provider: SyntheticProvider,
) -> Candidate:
    assessment = inspect_stage(stage_blocks, definition)
    anchor = await _validate_finality(definition, assessment, provider)
    corpora_root.mkdir(parents=True, exist_ok=True)
    _require_real_directory(corpora_root, "corpora root")
    candidate_path = corpora_root / f".candidate-{uuid.uuid4().hex}"
    payload_dir = candidate_path / "blocks"
    payload_dir.mkdir(parents=True)
    file_rows: list[dict[str, object]] = []
    canonical_rows: list[dict[str, object]] = []

    def write_canonical_chunk() -> None:
        if not canonical_rows:
            return
        first = _require_exact_int("block_number", canonical_rows[0]["block_number"])
        last = _require_exact_int("block_number", canonical_rows[-1]["block_number"])
        output = payload_dir / _chunk_name(first, last)
        _write_parquet_no_replace(output, _payload_frame(canonical_rows))
        file_rows.append(_file_row(output, f"blocks/{output.name}"))
        canonical_rows.clear()

    try:
        for stage_file in _read_chunks(stage_blocks):
            stage_frame = pl.read_parquet(stage_file)
            _require_schema(stage_frame, STAGE_SCHEMA, stage_file.name)
            for stage_row in stage_frame.iter_rows(named=True):
                canonical_rows.append(
                    {column: stage_row[column] for column in PAYLOAD_COLUMNS}
                )
                if len(canonical_rows) == PROTOTYPE_CANONICAL_CHUNK_ROWS:
                    write_canonical_chunk()
        write_canonical_chunk()
        file_rows.sort(key=lambda row: str(row["relative_path"]).encode("utf-8"))
        identity_bytes = _identity_bytes(definition, file_rows)
        corpus_id = hashlib.sha256(identity_bytes).hexdigest()
        _write_manifest(
            candidate_path / "manifest.json",
            {
                "corpus_id": corpus_id,
                "definition": definition.payload(),
                "files": file_rows,
                "finalized_block_number": anchor.number,
                "finalized_block_hash": anchor.block_hash,
            },
        )
        _sync_dir(payload_dir)
        _sync_dir(candidate_path)
        return Candidate(candidate_path, corpus_id, identity_bytes)
    except Exception:
        shutil.rmtree(candidate_path, ignore_errors=True)
        raise


def _definition_from_payload(payload: object) -> CorpusDefinition:
    if not isinstance(payload, dict) or set(payload) != {
        "chain_id",
        "first_block",
        "last_block",
        "regime",
    }:
        raise ContractError("manifest definition shape mismatch")
    regime_payload = payload["regime"]
    if not isinstance(regime_payload, dict) or set(regime_payload) != {"name", "start_block"}:
        raise ContractError("manifest regime shape mismatch")
    regime_name = regime_payload["name"]
    if not isinstance(regime_name, str) or not regime_name:
        raise ContractError("manifest regime.name must be a non-empty string")
    return CorpusDefinition(
        chain_id=_require_exact_int("chain_id", payload["chain_id"], minimum=0),
        regime=Regime(
            name=regime_name,
            start_block=_require_exact_int(
                "regime.start_block", regime_payload["start_block"], minimum=0
            ),
        ),
        first_block=_require_exact_int("first_block", payload["first_block"], minimum=0),
        last_block=_require_exact_int("last_block", payload["last_block"], minimum=0),
    )


def load_identity_bytes(
    root: Path,
    *,
    expected_corpus_id: str | None = None,
    require_root_name: bool = True,
) -> bytes:
    _require_package_shape(root)
    try:
        manifest = json.loads(
            (root / "manifest.json").read_text(encoding="utf-8"),
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_json_constant,
        )
    except Exception as exc:
        raise ContractError(f"cannot load canonical manifest: {exc}") from exc
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_KEYS:
        raise ContractError("canonical manifest keys mismatch")
    corpus_id = _require_hash("corpus_id", manifest["corpus_id"])
    anchor_number = _require_exact_int(
        "finalized_block_number",
        manifest["finalized_block_number"],
        minimum=0,
    )
    _require_hash("finalized_block_hash", manifest["finalized_block_hash"])
    definition = _definition_from_payload(manifest["definition"])
    if anchor_number < definition.last_block:
        raise ContractError("finalized anchor precedes the declared last block")
    files = manifest["files"]
    manifest_identity = _identity_bytes(definition, files)
    actual_files = _read_chunks(root / "blocks")
    actual_rows = [_file_row(path, f"blocks/{path.name}") for path in actual_files]
    actual_rows.sort(key=lambda row: str(row["relative_path"]).encode("utf-8"))
    if files != actual_rows:
        raise ContractError("canonical inventory differs from payload bytes")
    if not inspect_payload(root / "blocks", definition).complete:
        raise ContractError("canonical payload does not cover the exact definition")
    actual_identity = _identity_bytes(definition, actual_rows)
    if actual_identity != manifest_identity:
        raise ContractError("canonical inventory identity mismatch")
    if hashlib.sha256(manifest_identity).hexdigest() != corpus_id:
        raise ContractError("canonical corpus id does not match identity projection")
    if expected_corpus_id is not None and corpus_id != expected_corpus_id:
        raise ContractError("manifest corpus id differs from the expected candidate id")
    if require_root_name and root.name != corpus_id:
        raise ContractError("canonical directory name differs from corpus id")
    return manifest_identity


def _exclusive_rename(source: Path, destination: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    if sys.platform == "darwin" and hasattr(libc, "renamex_np"):
        renamex = libc.renamex_np
        renamex.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        renamex.restype = ctypes.c_int
        result = renamex(source_bytes, destination_bytes, 0x00000004)  # RENAME_EXCL
    elif hasattr(libc, "renameat2"):
        renameat2 = libc.renameat2
        renameat2.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        renameat2.restype = ctypes.c_int
        result = renameat2(-100, source_bytes, -100, destination_bytes, 1)
    else:
        raise ContractError("host lacks a checked exclusive directory rename primitive")
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), destination)


def publish_no_replace(candidate: Candidate, corpora_root: Path) -> Publication:
    _require_real_directory(corpora_root, "corpora root")
    if candidate.path.parent != corpora_root or not candidate.path.name.startswith(
        ".candidate-"
    ):
        raise ContractError("candidate must be an owned hidden sibling of its canonical root")
    candidate_identity = load_identity_bytes(
        candidate.path,
        expected_corpus_id=candidate.corpus_id,
        require_root_name=False,
    )
    if candidate_identity != candidate.identity_bytes:
        raise ContractError("candidate changed before publication")
    canonical = corpora_root / candidate.corpus_id

    def inspect_existing() -> Publication:
        try:
            existing_identity = load_identity_bytes(canonical)
        except Exception as exc:
            raise ContractError(
                f"same-id canonical content is invalid/conflicting; preserve both: {exc}"
            ) from exc
        if existing_identity != candidate.identity_bytes:
            raise ContractError("same-id canonical identity differs; preserve both")
        shutil.rmtree(candidate.path)
        _sync_dir(corpora_root)
        return Publication("no_op", canonical, False)

    if _path_exists(canonical):
        return inspect_existing()
    try:
        _exclusive_rename(candidate.path, canonical)
    except OSError as exc:
        if exc.errno in {errno.EEXIST, errno.ENOTEMPTY} and _path_exists(canonical):
            return inspect_existing()
        raise ContractError(
            "publication outcome is ambiguous after exclusive rename error; preserve and "
            "inspect every visible canonical or unpublished path"
        ) from exc
    try:
        _sync_dir(corpora_root)
        if load_identity_bytes(canonical) != candidate.identity_bytes:
            raise ContractError("published canonical reload mismatch")
    except Exception as exc:
        raise ContractError(
            "publication outcome is ambiguous after exclusive rename; preserve and inspect "
            "the visible canonical path without speculative deletion"
        ) from exc
    return Publication("published", canonical, False)


def write_payload_fixture(
    directory: Path,
    definition: CorpusDefinition,
    provider: SyntheticProvider,
    *,
    chunk_rows: int,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    rows = [
        provider._rows[number]
        for number in range(definition.first_block, definition.last_block + 1)
    ]
    for offset in range(0, len(rows), chunk_rows):
        chunk = rows[offset : offset + chunk_rows]
        frame = _payload_frame(
            [
                {column: row[column] for column in PAYLOAD_COLUMNS}
                for row in chunk
            ]
        )
        first = _require_exact_int("block_number", chunk[0]["block_number"])
        last = _require_exact_int("block_number", chunk[-1]["block_number"])
        _write_parquet_no_replace(directory / _chunk_name(first, last), frame)


def as_jsonable(value: object) -> object:
    if hasattr(value, "__dataclass_fields__"):
        return {
            key: as_jsonable(item)
            for key, item in asdict(cast(Any, value)).items()
        }
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [as_jsonable(item) for item in value]
    return value
