"""Evaluation dataset builder."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from ...acquisition.rpc import BlockPullPlan, BlockRange, RpcController, Web3BlockClient
from ...config import AcquireConfig
from ...core.reporting import Reporter
from ...corpus.io import iter_block_files
from .shared import (
    DatasetBuildOutcome,
    DatasetBuildResult,
    StageUpdateCallback,
    block_range_end,
    block_range_start,
    combined_frame,
    filter_block_range,
    load_existing_dataset,
    noop_stage_update,
    partial_plan,
    pull_plan_to_frame,
    validate_block_dataset,
    validate_evaluation_result,
    write_block_dataset_dir,
)


async def ensure_evaluation_dataset(
    *,
    config: AcquireConfig,
    block_client: Web3BlockClient,
    output_dir: Path,
    working_dir: Path,
    evaluation_plan: BlockPullPlan,
    rpc_controller: RpcController,
    reporter: Reporter,
    stage_update: StageUpdateCallback | None = None,
) -> DatasetBuildResult:
    chunk_size = config.acquisition.chunk_size
    update_stage = stage_update or noop_stage_update
    update_stage("planning", "checking existing dataset")
    existing = load_existing_dataset(output_dir, expected_chain_id=config.chain.runtime.chain_id)
    target_start = evaluation_plan.block_range.start
    target_end = evaluation_plan.block_range.end

    if existing is not None and existing.validation.status == "clean":
        if existing.frame is None:
            raise RuntimeError("clean evaluation validation requires an in-memory frame")
        existing_start = block_range_start(existing.validation)
        existing_end = block_range_end(existing.validation)
        if existing_start == target_start and existing_end == target_end:
            validation = existing.validation.model_copy(deep=True)
            update_stage("planning", "validating cached dataset")
            validate_evaluation_result(
                validation,
                evaluation_dir=output_dir,
                evaluation_plan=evaluation_plan,
                expected_chain_id=config.chain.runtime.chain_id,
            )
            return DatasetBuildResult(
                path=output_dir,
                validation=validation,
                file_count=existing.file_count,
                promote_dir=None,
                pulled_blocks=False,
                outcome=DatasetBuildOutcome.REUSED,
            )

        overlap_start = max(existing_start, target_start)
        overlap_end = min(existing_end, target_end)
        if overlap_end > overlap_start:
            frames: list[pl.DataFrame] = []
            pulled_blocks = False

            prefix_plan = partial_plan(
                block_client,
                start_block=target_start,
                end_block=overlap_start,
                window=evaluation_plan.window,
                chunk_size=chunk_size,
            )
            if prefix_plan is not None:
                frames.append(
                    await pull_plan_to_frame(
                        block_client=block_client,
                        plan=prefix_plan,
                        output_dir=working_dir / "evaluation-prefix",
                        chunk_size=chunk_size,
                        rpc_controller=rpc_controller,
                        reporter=reporter,
                    )
                )
                pulled_blocks = True

            frames.append(
                filter_block_range(
                    existing.frame,
                    BlockRange(start=overlap_start, end=overlap_end),
                )
            )

            suffix_plan = partial_plan(
                block_client,
                start_block=overlap_end,
                end_block=target_end,
                window=evaluation_plan.window,
                chunk_size=chunk_size,
            )
            if suffix_plan is not None:
                frames.append(
                    await pull_plan_to_frame(
                        block_client=block_client,
                        plan=suffix_plan,
                        output_dir=working_dir / "evaluation-suffix",
                        chunk_size=chunk_size,
                        rpc_controller=rpc_controller,
                        reporter=reporter,
                    )
                )
                pulled_blocks = True

            update_stage("planning", "extending cached dataset")
            update_stage("planning", "writing merged dataset")
            evaluation_frame = combined_frame(*frames)
            file_count = write_block_dataset_dir(
                working_dir / "evaluation",
                frame=evaluation_frame,
                chunk_size=chunk_size,
                chain_name=config.chain.name,
            )
            update_stage("planning", "validating dataset")
            validation = validate_block_dataset(
                working_dir / "evaluation",
                expected_chain_id=config.chain.runtime.chain_id,
            )
            validate_evaluation_result(
                validation,
                evaluation_dir=working_dir / "evaluation",
                evaluation_plan=evaluation_plan,
                expected_chain_id=config.chain.runtime.chain_id,
            )
            return DatasetBuildResult(
                path=working_dir / "evaluation",
                validation=validation,
                file_count=file_count,
                promote_dir=working_dir / "evaluation",
                pulled_blocks=pulled_blocks,
                outcome=DatasetBuildOutcome.EXTENDED,
            )

    update_stage("planning", "preparing download")
    await pull_plan_to_frame(
        block_client=block_client,
        plan=evaluation_plan,
        output_dir=working_dir / "evaluation",
        chunk_size=chunk_size,
        rpc_controller=rpc_controller,
        reporter=reporter,
    )
    update_stage("planning", "validating dataset")
    validation = validate_block_dataset(
        working_dir / "evaluation",
        expected_chain_id=config.chain.runtime.chain_id,
    )
    validate_evaluation_result(
        validation,
        evaluation_dir=working_dir / "evaluation",
        evaluation_plan=evaluation_plan,
        expected_chain_id=config.chain.runtime.chain_id,
    )
    return DatasetBuildResult(
        path=working_dir / "evaluation",
        validation=validation,
        file_count=len(iter_block_files(working_dir / "evaluation")),
        promote_dir=working_dir / "evaluation",
        pulled_blocks=True,
        outcome=(
            DatasetBuildOutcome.REBUILT
            if existing is not None
            else DatasetBuildOutcome.CREATED
        ),
    )
