"""Corpus split materialization session."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ...acquisition import (
    AcquisitionPullController,
    BlockPullPlan,
    BlockRange,
    BlockSource,
    TimestampRange,
)
from ..io import load_block_frame
from ..validation import (
    BlockDatasetValidationReport,
    validate_exact_window_frame,
)
from ._models import (
    CorpusSplitIntent,
    CorpusSplitKind,
    CorpusSplitMaterializationResult,
    CorpusSplitMaterializationSpec,
    CorpusSplitOutcome,
    StatusCallback,
    ValidationCallback,
    _SplitDatasetCandidate,
    _SplitDatasetFacts,
    _SplitPullRange,
)
from ._parquet_io import (
    filter_block_range,
    load_split_candidate,
    materialize_dataset,
    materialize_dataset_from_sources,
    plan_pull_dir,
    pull_plan_range_to_dir,
    pull_plan_to_frame,
    reusable_block_files_and_edges,
    reused_result,
    staged_result,
)


@dataclass(frozen=True, slots=True)
class CorpusSplitMaterializationSession:
    materialization: CorpusSplitMaterializationSpec
    block_source: BlockSource
    controller: AcquisitionPullController
    status: StatusCallback | None = None

    async def fulfill(
        self,
        intent: CorpusSplitIntent,
    ) -> CorpusSplitMaterializationResult:
        return await _ensure_split(
            intent,
            materialization=self.materialization,
            block_source=self.block_source,
            controller=self.controller,
            status=self.status,
        )


def noop_status(message: str) -> None:
    del message


async def _ensure_split(
    intent: CorpusSplitIntent,
    *,
    materialization: CorpusSplitMaterializationSpec,
    block_source: BlockSource,
    controller: AcquisitionPullController,
    status: StatusCallback | None,
) -> CorpusSplitMaterializationResult:
    if intent.kind is not CorpusSplitKind.BLOCKS:
        raise ValueError(f"Unsupported corpus split kind: {intent.kind}")
    emit = status or noop_status
    existing = load_split_candidate(
        intent.output_dir,
        expected_chain_id=materialization.expected_chain_id,
        required_columns=materialization.required_columns,
    )
    staged = load_split_candidate(
        intent.working_dir / intent.kind.value,
        expected_chain_id=materialization.expected_chain_id,
        required_columns=materialization.required_columns,
    )
    return await _materialize_split(
        existing=existing,
        staged=staged,
        kind=intent.kind,
        plan=intent.plan,
        working_dir=intent.working_dir,
        materialization=materialization,
        block_source=block_source,
        controller=controller,
        emit=emit,
        validate_result=_split_validator(
            intent.kind,
            plan=intent.plan,
            materialization=materialization,
        ),
    )


def _split_validator(
    kind: CorpusSplitKind,
    *,
    plan: BlockPullPlan,
    materialization: CorpusSplitMaterializationSpec,
) -> ValidationCallback:
    if kind is CorpusSplitKind.BLOCKS:
        return lambda validation, dataset_dir: validate_blocks_result(
            validation,
            blocks_dir=dataset_dir,
            blocks_plan=plan,
            expected_chain_id=materialization.expected_chain_id,
            required_columns=materialization.required_columns,
        )
    raise ValueError(f"Unsupported corpus split kind: {kind}")


async def _materialize_split(
    *,
    existing: _SplitDatasetCandidate | None,
    staged: _SplitDatasetCandidate | None,
    plan: BlockPullPlan,
    kind: CorpusSplitKind,
    working_dir: Path,
    materialization: CorpusSplitMaterializationSpec,
    block_source: BlockSource,
    controller: AcquisitionPullController,
    emit: StatusCallback,
    validate_result: ValidationCallback,
) -> CorpusSplitMaterializationResult:
    staged_reuse = _staged_reuse_result(
        kind.value,
        staged=staged,
        existing=existing,
        validate_result=validate_result,
    )
    if staged_reuse is not None:
        emit(f"{kind.value} reused staged dataset")
        return staged_reuse

    committed = await _reuse_or_extend_blocks(
        existing=existing,
        plan=plan,
        kind=kind,
        working_dir=working_dir,
        materialization=materialization,
        block_source=block_source,
        controller=controller,
        emit=emit,
        validate_result=validate_result,
    )
    if committed is not None:
        return committed

    return await _materialize_full_split(
        kind.value,
        existing=existing,
        kind=kind,
        plan=plan,
        working_dir=working_dir,
        materialization=materialization,
        block_source=block_source,
        controller=controller,
        emit=emit,
        validate_result=validate_result,
    )


async def _reuse_or_extend_blocks(
    *,
    existing: _SplitDatasetCandidate | None,
    plan: BlockPullPlan,
    kind: CorpusSplitKind,
    working_dir: Path,
    materialization: CorpusSplitMaterializationSpec,
    block_source: BlockSource,
    controller: AcquisitionPullController,
    emit: StatusCallback,
    validate_result: ValidationCallback,
) -> CorpusSplitMaterializationResult | None:
    if existing is not None and existing.facts.status == "clean":
        existing_start = _required_first_block(existing.facts)
        existing_end = _required_end_block(existing.facts)
        target_start = plan.block_range.start
        target_end = plan.block_range.end

        if existing_start == target_start and existing_end == target_end:
            existing_validation = _target_validation(existing, validate_result)
            if existing_validation is not None:
                emit("blocks reused committed dataset")
                return reused_result(existing, validation=existing_validation)

        overlap_start = max(existing_start, target_start)
        overlap_end = min(existing_end, target_end)
        if overlap_end > overlap_start:
            reusable_range = BlockRange(start=overlap_start, end=overlap_end)
            if reusable_range_matches_target_window(
                existing,
                reusable_range,
                plan.window,
            ):
                pull_ranges: list[_SplitPullRange] = []
                if target_start < overlap_start:
                    pull_ranges.append(
                        _SplitPullRange(
                            label="blocks-prefix",
                            block_range=BlockRange(start=target_start, end=overlap_start),
                        )
                    )
                if overlap_end < target_end:
                    pull_ranges.append(
                        _SplitPullRange(
                            label="blocks-suffix",
                            block_range=BlockRange(start=overlap_end, end=target_end),
                        )
                    )
                return await _extend_committed_blocks(
                    existing=existing,
                    reusable_range=reusable_range,
                    pull_ranges=tuple(pull_ranges),
                    kind=kind,
                    plan=plan,
                    working_dir=working_dir,
                    materialization=materialization,
                    block_source=block_source,
                    controller=controller,
                    emit=emit,
                    validate_result=validate_result,
                )
    return None


async def _extend_committed_blocks(
    *,
    existing: _SplitDatasetCandidate,
    reusable_range: BlockRange,
    pull_ranges: tuple[_SplitPullRange, ...],
    kind: CorpusSplitKind,
    plan: BlockPullPlan,
    working_dir: Path,
    materialization: CorpusSplitMaterializationSpec,
    block_source: BlockSource,
    controller: AcquisitionPullController,
    emit: StatusCallback,
    validate_result: ValidationCallback,
) -> CorpusSplitMaterializationResult:
    source_dirs: list[Path] = []
    source_files, frames = reusable_block_files_and_edges(
        existing.path,
        block_range=reusable_range,
    )
    for pull_range in pull_ranges:
        source_dirs.append(
            await pull_plan_range_to_dir(
                block_source=block_source,
                pull_range=pull_range,
                window=plan.window,
                working_dir=working_dir,
                materialization=materialization,
                controller=controller,
            )
        )
    emit("blocks extending committed dataset")
    return materialize_dataset_from_sources(
        mode=kind.value,
        materialization=materialization,
        working_dir=working_dir,
        validate_result=validate_result,
        source_dirs=source_dirs,
        source_files=source_files,
        frames=frames,
        outcome=CorpusSplitOutcome.EXTENDED,
    )


async def _materialize_full_split(
    label: str,
    *,
    existing: _SplitDatasetCandidate | None,
    kind: CorpusSplitKind,
    plan: BlockPullPlan,
    working_dir: Path,
    materialization: CorpusSplitMaterializationSpec,
    block_source: BlockSource,
    controller: AcquisitionPullController,
    emit: StatusCallback,
    validate_result: ValidationCallback,
) -> CorpusSplitMaterializationResult:
    emit(f"{label} downloading")
    frame = await pull_plan_to_frame(
        block_source=block_source,
        plan=plan,
        output_dir=plan_pull_dir(working_dir, label=kind.value, plan=plan),
        materialization=materialization,
        controller=controller,
    )
    return materialize_dataset(
        mode=kind.value,
        materialization=materialization,
        working_dir=working_dir,
        validate_result=validate_result,
        frames=(frame,),
        outcome=(
            CorpusSplitOutcome.REBUILT
            if existing is not None
            else CorpusSplitOutcome.CREATED
        ),
    )


def _staged_reuse_result(
    kind: str,
    *,
    staged: _SplitDatasetCandidate | None,
    existing: _SplitDatasetCandidate | None,
    validate_result: ValidationCallback,
) -> CorpusSplitMaterializationResult | None:
    if staged is None:
        return None
    if staged.facts.status != "clean":
        raise RuntimeError(f"Cannot resume invalid staged {kind} dataset: {staged.validation}")
    staged_validation = _target_validation(staged, validate_result)
    if staged_validation is None:
        return None
    return staged_result(
        staged,
        validation=staged_validation,
        outcome=(
            CorpusSplitOutcome.REBUILT
            if existing is not None
            else CorpusSplitOutcome.CREATED
        ),
    )


def _target_validation(
    candidate: _SplitDatasetCandidate,
    validate_target: Callable[[BlockDatasetValidationReport, Path], None],
) -> BlockDatasetValidationReport | None:
    if candidate.facts.status != "clean":
        return None
    validation = candidate.validation.model_copy(deep=True)
    try:
        validate_target(validation, candidate.path)
    except ValueError:
        return None
    return validation


def _required_first_block(facts: _SplitDatasetFacts) -> int:
    if facts.first_block_number is None:
        raise ValueError("validated corpus is missing the first block number")
    return facts.first_block_number


def _required_end_block(facts: _SplitDatasetFacts) -> int:
    if facts.last_block_number is None:
        raise ValueError("validated corpus is missing the last block number")
    return facts.last_block_number + 1


def validate_blocks_result(
    validation: BlockDatasetValidationReport,
    *,
    blocks_dir: Path,
    blocks_plan: BlockPullPlan,
    expected_chain_id: int,
    required_columns: frozenset[str],
) -> None:
    exact_validation = validate_exact_window_frame(
        load_block_frame(blocks_dir),
        dataset_path=blocks_dir,
        expected_chain_id=expected_chain_id,
        expected_start_timestamp=blocks_plan.window.start,
        expected_end_timestamp=blocks_plan.window.end,
        required_columns=required_columns,
    )
    if exact_validation.status != "clean":
        raise ValueError(f"Canonical blocks corpus validation failed: {exact_validation}")
    if exact_validation.first_block_number != blocks_plan.block_range.start:
        raise ValueError(
            "Blocks corpus does not start at the requested block boundary: "
            f"expected first block {blocks_plan.block_range.start}, "
            f"got {exact_validation.first_block_number}"
        )
    if exact_validation.last_block_number != blocks_plan.block_range.end - 1:
        raise ValueError(
            "Blocks corpus does not end at the requested block boundary: "
            f"expected last block {blocks_plan.block_range.end - 1}, "
            f"got {exact_validation.last_block_number}"
        )
    validation.status = exact_validation.status
    validation.below_start_count = exact_validation.below_start_count
    validation.above_end_count = exact_validation.above_end_count
    validation.expected_start_timestamp = exact_validation.expected_start_timestamp
    validation.expected_end_timestamp = exact_validation.expected_end_timestamp
    validation.errors = list(exact_validation.errors)


def reusable_range_matches_target_window(
    candidate: _SplitDatasetCandidate,
    block_range: BlockRange,
    window: TimestampRange,
) -> bool:
    frame = filter_block_range(load_block_frame(candidate.path), block_range)
    if frame.height == 0:
        return False
    timestamps: list[int] = []
    for value in frame["timestamp"].to_list():
        if type(value) is not int:
            return False
        timestamps.append(value)
    return min(timestamps) >= window.start and max(timestamps) < window.end
