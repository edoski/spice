"""Mechanical evaluator engines."""

from __future__ import annotations

import numpy as np

from ..prediction.contracts import DecodedPredictionResult, require_decoded_offsets
from ..temporal.problem_store import CompiledProblemStore
from ..temporal.realization import CompiledRealizationPolicyContract
from .contracts import EvaluationSummary, IntVector
from .shared import candidate_window_summary, single_run_summary


def run_zero_stop_rollout_fullset(
    store: CompiledProblemStore,
    realization_policy: CompiledRealizationPolicyContract,
    decoded_result: DecodedPredictionResult,
    sample_indices: IntVector,
) -> EvaluationSummary:
    del realization_policy
    decoded_offsets = require_decoded_offsets(decoded_result)
    if sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")
    window_summary = candidate_window_summary(store, sample_indices)
    if not np.array_equal(window_summary.anchor_rows, window_summary.baseline_rows):
        raise ValueError("zero_stop_rollout_fullset requires current-row candidate windows")

    offsets = decoded_offsets.select(np.arange(sample_indices.shape[0], dtype=np.int64))
    row_to_position = np.full(store.n_rows, -1, dtype=np.int64)
    row_to_position[window_summary.anchor_rows] = np.arange(
        sample_indices.shape[0],
        dtype=np.int64,
    )
    max_available_row = int(window_summary.anchor_rows.max())
    realized_rows = np.empty(sample_indices.shape[0], dtype=np.int64)
    steps_to_stop = np.empty(sample_indices.shape[0], dtype=np.int64)
    zero_stop_mask = np.zeros(sample_indices.shape[0], dtype=np.bool_)
    terminal_without_zero_mask = np.zeros(sample_indices.shape[0], dtype=np.bool_)
    truncated_window_mask = np.zeros(sample_indices.shape[0], dtype=np.bool_)

    for index, (start_row, last_candidate_row) in enumerate(
        zip(window_summary.anchor_rows, window_summary.last_candidate_rows, strict=True)
    ):
        effective_stop_row = min(int(last_candidate_row), max_available_row)
        truncated_window_mask[index] = effective_stop_row < int(last_candidate_row)
        current_row = int(start_row)
        steps = 0
        while current_row <= effective_stop_row:
            current_position = int(row_to_position[current_row])
            if current_position < 0:
                raise ValueError(
                    "zero_stop_rollout_fullset requires one sample per anchor row inside "
                    "each candidate window"
                )
            if int(offsets[current_position]) == 0:
                realized_rows[index] = current_row
                steps_to_stop[index] = steps
                zero_stop_mask[index] = True
                break
            current_row += 1
            steps += 1
        else:
            realized_rows[index] = effective_stop_row
            steps_to_stop[index] = int(effective_stop_row - start_row)
            terminal_without_zero_mask[index] = True

    realized_total = float(
        np.exp(store.log_base_fees[realized_rows].astype(np.float64, copy=False)).sum()
    )
    baseline_total = float(
        np.exp(
            store.log_base_fees[window_summary.baseline_rows].astype(
                np.float64,
                copy=False,
            )
        ).sum()
    )
    optimum_total = float(
        np.exp(
            store.log_base_fees[window_summary.optimum_rows].astype(
                np.float64,
                copy=False,
            )
        ).sum()
    )
    if baseline_total <= 0.0:
        raise ValueError("baseline fee total must be positive")
    if optimum_total <= 0.0:
        raise ValueError("optimum fee total must be positive")
    return single_run_summary(
        metric_values={
            "profit_over_baseline": (baseline_total - realized_total) / baseline_total,
            "cost_over_optimum": (realized_total - optimum_total) / optimum_total,
            "baseline_cost_over_optimum": (baseline_total - optimum_total) / optimum_total,
            "realized_fee_sum": realized_total,
            "baseline_fee_sum": baseline_total,
            "optimum_fee_sum": optimum_total,
            "mean_steps_to_stop": float(steps_to_stop.mean(dtype=np.float64)),
            "zero_stop_rate": float(zero_stop_mask.mean(dtype=np.float64)),
            "terminal_without_zero_count": float(terminal_without_zero_mask.sum()),
        },
        n_events=int(sample_indices.shape[0]),
        metadata={
            "mode": "zero_stop_rollout_fullset",
            "zero_stop_count": int(zero_stop_mask.sum()),
            "terminal_without_zero_count": int(terminal_without_zero_mask.sum()),
            "truncated_window_count": int(truncated_window_mask.sum()),
        },
    )


def run_anchor_basefee_fullset(
    store: CompiledProblemStore,
    realization_policy: CompiledRealizationPolicyContract,
    decoded_result: DecodedPredictionResult,
    sample_indices: IntVector,
) -> EvaluationSummary:
    decoded_offsets = require_decoded_offsets(decoded_result)
    if sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")
    selected_positions = np.arange(sample_indices.shape[0], dtype=np.int64)
    realized = realization_policy.realize_selections(
        store,
        decoded_offsets,
        sample_indices,
        selected_positions,
    )
    anchor_rows = store.anchor_rows[sample_indices.astype(np.int64, copy=False)]
    realized_total = float(
        np.exp(store.log_base_fees[realized.realized_rows].astype(np.float64, copy=False)).sum()
    )
    anchor_total = float(
        np.exp(store.log_base_fees[anchor_rows].astype(np.float64, copy=False)).sum()
    )
    if anchor_total <= 0.0:
        raise ValueError("anchor fee total must be positive")
    requested_offsets = decoded_offsets.select(selected_positions)
    return single_run_summary(
        metric_values={
            "fee_delta_over_anchor": (anchor_total - realized_total) / anchor_total,
            "realized_fee_sum": realized_total,
            "anchor_fee_sum": anchor_total,
            "overflow_count": float(realized.overflow_mask.sum()),
            "zero_action_rate": float((requested_offsets == 0).mean(dtype=np.float64)),
        },
        n_events=int(sample_indices.shape[0]),
        metadata={
            "mode": "anchor_basefee_fullset",
            "overflow_count": int(realized.overflow_mask.sum()),
            "zero_action_count": int(np.count_nonzero(requested_offsets == 0)),
        },
    )
