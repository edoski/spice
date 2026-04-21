"""Compact acquisition workflow field builders."""

from __future__ import annotations

from ..acquisition.rpc import BlockPullPlan
from ..config.models import AcquireConfig
from ..corpus.builders import DatasetBuildOutcome
from ..temporal.contracts import CompiledProblemContract


def acquire_dry_run_fields(
    config: AcquireConfig,
    *,
    contract: CompiledProblemContract,
    history_window_seconds: int,
    history_plan: BlockPullPlan,
    evaluation_plan: BlockPullPlan,
) -> list[tuple[str, str]]:
    del config, contract
    return [
        ("history_window", f"{history_window_seconds}s"),
        ("history_blocks", str(history_plan.expected_rows)),
        ("evaluation_blocks", str(evaluation_plan.expected_rows)),
    ]


def acquisition_result_fields(
    *,
    history_outcome: DatasetBuildOutcome,
    history_row_count: int,
    evaluation_outcome: DatasetBuildOutcome,
    evaluation_row_count: int,
) -> list[tuple[str, str]]:
    return [
        ("history", history_outcome.value),
        ("history_blocks", str(history_row_count)),
        ("evaluation", evaluation_outcome.value),
        ("evaluation_blocks", str(evaluation_row_count)),
    ]
