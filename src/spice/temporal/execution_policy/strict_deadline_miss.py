"""Strict bounded-delay execution policy."""

from __future__ import annotations

import numpy as np
from pydantic import field_validator

from ..problem_store import CompiledProblemStore
from ..semantics import BaselineRowMode
from .base import (
    CompiledExecutionPolicyContract,
    DecodedOffsetBatch,
    ExecutionPolicyConfig,
    IntVector,
    PreparedActionSpace,
    PreparedTemporalOutcomeFacts,
    RealizedSelectionBatch,
)


class StrictDeadlineMissConfig(ExecutionPolicyConfig):
    id: str = "strict_deadline_miss"

    @field_validator("id")
    @classmethod
    def validate_strict_deadline_miss_id(cls, value: str) -> str:
        value = ExecutionPolicyConfig.validate_id(value)
        if value != "strict_deadline_miss":
            raise ValueError("problem.execution_policy.id must be strict_deadline_miss")
        return value


def _prepare_action_space(
    store: CompiledProblemStore,
    sample_indices: IntVector,
) -> PreparedActionSpace:
    resolved_sample_indices = sample_indices.astype(np.int64, copy=False)
    return PreparedActionSpace(
        sample_indices=resolved_sample_indices,
        max_candidate_slots=store.max_candidate_slots,
        action_mask=np.ones(
            (resolved_sample_indices.shape[0], store.max_candidate_slots),
            dtype=np.bool_,
        ),
    )


def _reachable_optimum(
    store: CompiledProblemStore,
    *,
    start_row: int,
    reachable_end_row: int,
) -> int:
    candidate_values = store.log_base_fees[start_row:reachable_end_row]
    offset = int(np.argmin(candidate_values))
    return int(start_row + offset)


def _prepare_outcome_facts(
    store: CompiledProblemStore,
    action_space: PreparedActionSpace,
) -> PreparedTemporalOutcomeFacts:
    sample_indices = action_space.sample_indices
    if sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")
    if action_space.max_candidate_slots != store.max_candidate_slots:
        raise ValueError("Action Space action width does not match store")
    resolved_indices = sample_indices.astype(np.int64, copy=False)
    window_summary = store.candidate_windows(resolved_indices)
    batch_size = int(resolved_indices.shape[0])
    max_candidate_slots = int(action_space.max_candidate_slots)
    action_outcome_rows = np.empty((batch_size, max_candidate_slots), dtype=np.int64)
    action_outcome_log_fees = np.empty((batch_size, max_candidate_slots), dtype=np.float32)
    reachable_action_mask = np.zeros((batch_size, max_candidate_slots), dtype=np.bool_)
    overflow_mask = np.zeros((batch_size, max_candidate_slots), dtype=np.bool_)
    baseline_rows = window_summary.candidate_start_rows.astype(np.int64, copy=True)
    for row, (start_row, end_row, candidate_count) in enumerate(
        zip(
            window_summary.candidate_start_rows,
            window_summary.candidate_end_rows,
            window_summary.candidate_counts,
            strict=True,
        )
    ):
        slot_count = min(int(candidate_count), max_candidate_slots)
        physical_offsets = np.arange(slot_count, dtype=np.int64)
        action_outcome_rows[row, :slot_count] = int(start_row) + physical_offsets
        action_outcome_log_fees[row, :slot_count] = store.log_base_fees[
            action_outcome_rows[row, :slot_count]
        ]
        reachable_action_mask[row, :slot_count] = True
        if int(candidate_count) < max_candidate_slots:
            if int(end_row) >= store.n_rows:
                raise ValueError(
                    "strict_deadline_miss requires a post-window row "
                    "for overflow outcome facts"
                )
            action_outcome_rows[row, candidate_count:] = int(end_row)
            action_outcome_log_fees[row, candidate_count:] = store.log_base_fees[int(end_row)]
            overflow_mask[row, candidate_count:] = True
    return PreparedTemporalOutcomeFacts(
        action_outcome_rows=action_outcome_rows,
        action_outcome_log_fees=action_outcome_log_fees,
        reachable_action_mask=reachable_action_mask,
        baseline_rows=baseline_rows,
        overflow_mask=overflow_mask,
    )


def _realize_selections(
    store: CompiledProblemStore,
    decoded_offsets: DecodedOffsetBatch,
    action_space: PreparedActionSpace,
    selected_positions: IntVector,
) -> RealizedSelectionBatch:
    sample_indices = action_space.sample_indices
    selected_sample_indices = sample_indices[selected_positions]
    window_summary = store.candidate_windows(selected_sample_indices)
    requested_offsets = decoded_offsets.select(selected_positions).astype(np.int64, copy=False)
    overflow_mask = requested_offsets >= window_summary.candidate_counts
    overflow_without_post_window = np.any(
        window_summary.candidate_end_rows[overflow_mask] >= store.n_rows
    )
    if np.any(overflow_mask) and overflow_without_post_window:
        raise ValueError(
            "strict_deadline_miss requires a post-window row "
            "for overflow execution"
        )
    resolved_offsets = requested_offsets.copy()
    realized_rows = window_summary.candidate_start_rows + requested_offsets
    if np.any(overflow_mask):
        resolved_offsets[overflow_mask] = window_summary.candidate_counts[overflow_mask]
        realized_rows[overflow_mask] = window_summary.candidate_end_rows[overflow_mask]
    optimum_rows = np.empty(selected_sample_indices.shape[0], dtype=np.int64)
    for row, (start_row, reachable_end_row) in enumerate(
        zip(window_summary.candidate_start_rows, window_summary.reachable_end_rows, strict=True)
    ):
        optimum_rows[row] = _reachable_optimum(
            store,
            start_row=int(start_row),
            reachable_end_row=int(reachable_end_row),
        )
    return RealizedSelectionBatch(
        realized_rows=realized_rows,
        baseline_rows=window_summary.candidate_start_rows,
        optimum_rows=optimum_rows,
        requested_offsets=requested_offsets,
        resolved_offsets=resolved_offsets,
        overflow_mask=overflow_mask,
    )


def compile_execution_policy(
    config: StrictDeadlineMissConfig,
) -> CompiledExecutionPolicyContract:
    if config.id != "strict_deadline_miss":
        raise ValueError("execution_policy.id must be strict_deadline_miss")
    return CompiledExecutionPolicyContract(
        execution_policy_id="strict_deadline_miss",
        baseline_row_mode=BaselineRowMode.FIRST_CANDIDATE,
        requires_post_window_row=True,
        prepare_action_space_fn=_prepare_action_space,
        prepare_outcome_facts_fn=_prepare_outcome_facts,
        realize_selections_fn=_realize_selections,
    )
