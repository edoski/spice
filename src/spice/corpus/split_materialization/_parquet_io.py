"""Corpus split parquet IO, reuse, and pull mechanics."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from shutil import copy2

import polars as pl

from ...acquisition import (
    AcquisitionPullController,
    BlockPullPlan,
    BlockRange,
    BlockSource,
    TimestampRange,
    pull_block_range,
)
from ...core.files import remove_path
from ..contract import CanonicalBlockRow, canonicalize_block_frame
from ..io import iter_block_files, load_block_frame, write_block_file
from ..validation import (
    BlockDatasetValidationReport,
    validate_contiguous_block_frame,
)
from ._models import (
    CorpusSplitMaterializationResult,
    CorpusSplitMaterializationSpec,
    CorpusSplitOutcome,
    ValidationCallback,
    _SplitDatasetCandidate,
    _SplitDatasetFacts,
    _SplitPullRange,
)


@dataclass(slots=True)
class ParquetBlockPullSink:
    output_dir: Path
    materialization: CorpusSplitMaterializationSpec
    pending_rows: list[CanonicalBlockRow]

    @classmethod
    def create(
        cls,
        output_dir: Path,
        *,
        materialization: CorpusSplitMaterializationSpec,
    ) -> ParquetBlockPullSink:
        return cls(output_dir=output_dir, materialization=materialization, pending_rows=[])

    def completed_prefix_end(self, plan: BlockPullPlan) -> int:
        return completed_prefix_end(
            self.output_dir,
            plan=plan,
            expected_chain_id=self.materialization.expected_chain_id,
            required_columns=self.materialization.required_columns,
        )

    def write_rows(self, rows: list[CanonicalBlockRow]) -> None:
        self.pending_rows.extend(rows)
        while len(self.pending_rows) >= self.materialization.chunk_size:
            write_block_rows_chunk(
                self.output_dir,
                chain_name=self.materialization.chain_name,
                rows=self.pending_rows[: self.materialization.chunk_size],
            )
            self.pending_rows = self.pending_rows[self.materialization.chunk_size :]

    def finish(self) -> None:
        if self.pending_rows:
            write_block_rows_chunk(
                self.output_dir,
                chain_name=self.materialization.chain_name,
                rows=self.pending_rows,
            )
            self.pending_rows = []


def load_split_candidate(
    path: Path,
    *,
    expected_chain_id: int,
    required_columns: frozenset[str] = frozenset(),
) -> _SplitDatasetCandidate | None:
    if not _has_block_files(path):
        return None
    try:
        frame = load_block_frame(path)
    except Exception as exc:
        validation = BlockDatasetValidationReport(
            dataset_path=path,
            status="error",
            errors=[str(exc)],
        )
        return _split_candidate(
            path=path,
            validation=validation,
            file_count=len(iter_block_files(path)),
        )
    validation = validate_contiguous_block_frame(
        frame,
        dataset_path=path,
        expected_chain_id=expected_chain_id,
        required_columns=required_columns,
    )
    return _split_candidate(
        path=path,
        validation=validation,
        file_count=len(iter_block_files(path)),
    )


def reused_result(
    existing: _SplitDatasetCandidate,
    *,
    validation: BlockDatasetValidationReport | None = None,
) -> CorpusSplitMaterializationResult:
    return CorpusSplitMaterializationResult(
        path=existing.path,
        validation=existing.validation if validation is None else validation,
        file_count=existing.file_count,
        promote_dir=None,
        outcome=CorpusSplitOutcome.REUSED,
    )


def staged_result(
    existing: _SplitDatasetCandidate,
    *,
    outcome: CorpusSplitOutcome,
    validation: BlockDatasetValidationReport | None = None,
) -> CorpusSplitMaterializationResult:
    return CorpusSplitMaterializationResult(
        path=existing.path,
        validation=existing.validation if validation is None else validation,
        file_count=existing.file_count,
        promote_dir=existing.path,
        outcome=outcome,
    )


def materialize_dataset(
    *,
    mode: str,
    materialization: CorpusSplitMaterializationSpec,
    working_dir: Path,
    validate_result: ValidationCallback,
    frames: Sequence[pl.DataFrame] | None = None,
    outcome: CorpusSplitOutcome,
) -> CorpusSplitMaterializationResult:
    dataset_dir = working_dir / mode
    if frames is not None:
        remove_path(dataset_dir)
        file_count = write_block_dataset_dir(
            dataset_dir,
            frame=combined_frame(*frames),
            chunk_size=materialization.chunk_size,
            chain_name=materialization.chain_name,
        )
    else:
        file_count = len(iter_block_files(dataset_dir))
    validation = validate_block_dataset(
        dataset_dir,
        expected_chain_id=materialization.expected_chain_id,
        required_columns=materialization.required_columns,
    )
    validate_result(validation, dataset_dir)
    return CorpusSplitMaterializationResult(
        path=dataset_dir,
        validation=validation,
        file_count=file_count,
        promote_dir=dataset_dir,
        outcome=outcome,
    )


def materialize_dataset_from_sources(
    *,
    mode: str,
    materialization: CorpusSplitMaterializationSpec,
    working_dir: Path,
    validate_result: ValidationCallback,
    source_dirs: Sequence[Path] = (),
    source_files: Sequence[Path] = (),
    frames: Sequence[pl.DataFrame] = (),
    outcome: CorpusSplitOutcome,
) -> CorpusSplitMaterializationResult:
    dataset_dir = working_dir / mode
    remove_path(dataset_dir)
    dataset_dir.mkdir(parents=True, exist_ok=True)
    for source_dir in source_dirs:
        for source_file in iter_block_files(source_dir):
            copy2(source_file, dataset_dir / source_file.name)
    for source_file in source_files:
        copy2(source_file, dataset_dir / source_file.name)
    for frame in frames:
        if frame.height > 0:
            write_block_dataset_dir(
                dataset_dir,
                frame=frame,
                chunk_size=materialization.chunk_size,
                chain_name=materialization.chain_name,
            )
    validation = validate_block_dataset(
        dataset_dir,
        expected_chain_id=materialization.expected_chain_id,
        required_columns=materialization.required_columns,
    )
    validate_result(validation, dataset_dir)
    return CorpusSplitMaterializationResult(
        path=dataset_dir,
        validation=validation,
        file_count=len(iter_block_files(dataset_dir)),
        promote_dir=dataset_dir,
        outcome=outcome,
    )


def reusable_block_files_and_edges(
    dataset_dir: Path,
    *,
    block_range: BlockRange,
) -> tuple[list[Path], list[pl.DataFrame]]:
    reusable_files: list[Path] = []
    edge_frames: list[pl.DataFrame] = []
    for block_file in iter_block_files(dataset_dir):
        frame = load_block_frame(block_file)
        start_block = int(frame["block_number"][0])
        end_block = int(frame["block_number"][-1]) + 1
        if end_block <= block_range.start or start_block >= block_range.end:
            continue
        if start_block >= block_range.start and end_block <= block_range.end:
            reusable_files.append(block_file)
            continue
        edge = filter_block_range(frame, block_range)
        if edge.height > 0:
            edge_frames.append(edge)
    return reusable_files, edge_frames


async def pull_plan_to_frame(
    *,
    block_source: BlockSource,
    plan: BlockPullPlan,
    output_dir: Path,
    materialization: CorpusSplitMaterializationSpec,
    controller: AcquisitionPullController,
) -> pl.DataFrame:
    await pull_block_range(
        block_source,
        plan=plan,
        controller=controller,
        sink=ParquetBlockPullSink.create(output_dir, materialization=materialization),
    )
    return load_block_frame(output_dir)


async def pull_plan_to_dir(
    *,
    block_source: BlockSource,
    plan: BlockPullPlan,
    output_dir: Path,
    materialization: CorpusSplitMaterializationSpec,
    controller: AcquisitionPullController,
) -> Path:
    await pull_block_range(
        block_source,
        plan=plan,
        controller=controller,
        sink=ParquetBlockPullSink.create(output_dir, materialization=materialization),
    )
    return output_dir


def plan_pull_dir(working_dir: Path, *, label: str, plan: BlockPullPlan) -> Path:
    return (
        working_dir
        / "pulls"
        / f"{label}__{plan.block_range.start}_to_{plan.block_range.end}"
    )


async def pull_plan_range_to_dir(
    *,
    block_source: BlockSource,
    pull_range: _SplitPullRange,
    window: TimestampRange,
    working_dir: Path,
    materialization: CorpusSplitMaterializationSpec,
    controller: AcquisitionPullController,
) -> Path:
    plan = BlockPullPlan(window=window, block_range=pull_range.block_range)
    return await pull_plan_to_dir(
        block_source=block_source,
        plan=plan,
        output_dir=plan_pull_dir(working_dir, label=pull_range.label, plan=plan),
        materialization=materialization,
        controller=controller,
    )


def validate_block_dataset(
    path: Path,
    *,
    expected_chain_id: int,
    required_columns: frozenset[str] = frozenset(),
) -> BlockDatasetValidationReport:
    try:
        frame = load_block_frame(path)
    except Exception as exc:  # pragma: no cover - workflow smoke tests cover this path
        return BlockDatasetValidationReport(dataset_path=path, status="error", errors=[str(exc)])
    return validate_contiguous_block_frame(
        frame,
        dataset_path=path,
        expected_chain_id=expected_chain_id,
        required_columns=required_columns,
    )


def filter_block_range(frame: pl.DataFrame, block_range: BlockRange) -> pl.DataFrame:
    return frame.filter(
        (pl.col("block_number") >= block_range.start)
        & (pl.col("block_number") < block_range.end)
    ).sort("block_number")


def write_block_dataset_dir(
    output_dir: Path,
    *,
    frame: pl.DataFrame,
    chunk_size: int,
    chain_name: str,
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    sorted_frame = frame.sort("block_number")
    file_count = 0
    for start_index in range(0, sorted_frame.height, chunk_size):
        chunk = sorted_frame.slice(start_index, min(chunk_size, sorted_frame.height - start_index))
        start_block = int(chunk["block_number"][0])
        end_block = int(chunk["block_number"][-1])
        write_block_file(
            output_dir / f"{chain_name}__blocks__{start_block}_to_{end_block}.parquet",
            chunk,
        )
        file_count += 1
    return file_count


def completed_prefix_end(
    output_dir: Path,
    *,
    plan: BlockPullPlan,
    expected_chain_id: int,
    required_columns: frozenset[str],
) -> int:
    if not output_dir.exists():
        return plan.block_range.start
    try:
        frame = load_block_frame(output_dir)
    except ValueError as exc:
        if "No parquet block files found" in str(exc):
            return plan.block_range.start
        raise RuntimeError(
            f"Cannot resume from invalid partial block dataset: {output_dir}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"Cannot resume from invalid partial block dataset: {output_dir}"
        ) from exc

    validation = validate_contiguous_block_frame(
        frame,
        dataset_path=output_dir,
        expected_chain_id=expected_chain_id,
        required_columns=required_columns,
    )
    if validation.status != "clean":
        raise RuntimeError(f"Cannot resume from invalid partial block dataset: {validation}")
    if validation.first_block_number != plan.block_range.start:
        raise RuntimeError(
            "Cannot resume partial block corpus with a different start block: "
            f"expected {plan.block_range.start}, got {validation.first_block_number}"
        )
    if validation.last_block_number is None:
        return plan.block_range.start
    if validation.last_block_number >= plan.block_range.end:
        return plan.block_range.end
    return validation.last_block_number + 1


def write_block_rows_chunk(
    output_dir: Path,
    *,
    chain_name: str,
    rows: Sequence[CanonicalBlockRow],
) -> Path:
    frame = canonicalize_block_frame(pl.DataFrame(rows))
    start_block = int(frame["block_number"][0])
    end_block = int(frame["block_number"][-1])
    destination = output_dir / f"{chain_name}__blocks__{start_block}_to_{end_block}.parquet"
    write_block_file(destination, frame)
    return destination


def combined_frame(*frames: pl.DataFrame) -> pl.DataFrame:
    return pl.concat([frame for frame in frames if frame.height > 0], how="vertical").sort(
        "block_number"
    )


def _split_candidate(
    *,
    path: Path,
    validation: BlockDatasetValidationReport,
    file_count: int,
) -> _SplitDatasetCandidate:
    return _SplitDatasetCandidate(
        path=path,
        validation=validation,
        facts=_SplitDatasetFacts(
            status=validation.status,
            first_block_number=validation.first_block_number,
            last_block_number=validation.last_block_number,
        ),
        file_count=file_count,
    )


def _has_block_files(path: Path) -> bool:
    try:
        return bool(iter_block_files(path))
    except ValueError:
        return False
