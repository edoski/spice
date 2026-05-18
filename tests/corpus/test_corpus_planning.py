from __future__ import annotations

import asyncio
import math
from typing import cast

from spice.acquisition import BlockPullPlan, BlockRange, TimestampRange
from spice.config import AcquireConfig, WorkflowTask, coerce_features_config
from spice.config.groups import load_named_group_payload
from spice.corpus.planning import (
    CorpusAcquisitionPlanningSpec,
    build_corpus_acquisition_planning_context,
)


def _load_acquire_config(load_workflow_config, tmp_path) -> AcquireConfig:
    return cast(
        AcquireConfig,
        load_workflow_config(WorkflowTask.ACQUIRE, workspace=tmp_path),
    )


def _planning_spec(config: AcquireConfig) -> CorpusAcquisitionPlanningSpec:
    return CorpusAcquisitionPlanningSpec(
        features=config.features,
        problem=config.problem,
        chain_runtime=config.chain.runtime,
        window_start_timestamp=config.corpus_window_start_timestamp,
        window_end_timestamp=config.corpus_window_end_timestamp,
    )


class _PlanningSource:
    def __init__(self) -> None:
        self.planned_windows: list[TimestampRange] = []

    async def close(self) -> None:
        return None

    async def estimate_recent_block_interval(self, sample_size: int = 128) -> float:
        del sample_size
        return 12.0

    async def plan_window(self, window: TimestampRange) -> BlockPullPlan:
        self.planned_windows.append(window)
        count = max(1, math.ceil((window.end - window.start) / 12))
        return BlockPullPlan(
            window=window,
            block_range=BlockRange(start=100, end=100 + count),
        )

    async def get_block_rows(self, start: int, end: int):
        del start, end
        raise AssertionError("planning must not fetch rows")


def test_initial_plan_uses_one_configured_corpus_window(
    tmp_path,
    load_workflow_config,
) -> None:
    config = _load_acquire_config(load_workflow_config, tmp_path)
    context = build_corpus_acquisition_planning_context(_planning_spec(config))
    source = _PlanningSource()

    plan = asyncio.run(context.initial_plan(source))

    window = TimestampRange(
        start=config.corpus_window_start_timestamp,
        end=config.corpus_window_end_timestamp,
    )
    assert plan.blocks_plan.window == window
    assert plan.requested_window_seconds == window.end - window.start
    assert source.planned_windows == [window]


def test_planning_derives_priority_fee_source_requirements(
    tmp_path,
    load_workflow_config,
) -> None:
    config = _load_acquire_config(load_workflow_config, tmp_path)
    priority_config = config.model_copy(
        update={
            "features": coerce_features_config(
                load_named_group_payload("core_fee_dynamics_with_priority_fee", "features")
            )
        }
    )

    baseline = build_corpus_acquisition_planning_context(_planning_spec(config))
    priority = build_corpus_acquisition_planning_context(_planning_spec(priority_config))

    assert baseline.source_requirements.required_columns >= {
        "block_number",
        "timestamp",
        "chain_id",
        "base_fee_per_gas",
        "gas_used",
        "gas_limit",
        "tx_count",
    }
    assert "priority_fee_percentiles" not in baseline.source_requirements.optional_enrichments
    assert "priority_fee_percentiles" in priority.source_requirements.optional_enrichments
    assert priority.source_requirements.required_columns >= {
        "priority_fee_p10",
        "priority_fee_p50",
        "priority_fee_p90",
        "priority_fee_spread",
    }
    assert priority.source_requirements.temporal_unit == "block"
    assert priority.source_requirements.ordering_key == "block_number"
    assert priority.source_requirements.partition_key == "chain_id"
