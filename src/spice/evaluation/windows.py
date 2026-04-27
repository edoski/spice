"""Evaluator candidate-window helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..temporal.problem_store import CompiledProblemStore
from .contracts import IntVector


@dataclass(frozen=True, slots=True)
class CandidateWindowSummary:
    anchor_rows: IntVector
    baseline_rows: IntVector
    last_candidate_rows: IntVector
    optimum_rows: IntVector


def candidate_window_summary(
    store: CompiledProblemStore,
    sample_indices: IntVector,
) -> CandidateWindowSummary:
    resolved_indices = sample_indices.astype(np.int64, copy=False)
    anchor_rows = store.anchor_rows[resolved_indices].astype(np.int64, copy=False)
    baseline_rows = store.candidate_start_rows[resolved_indices].astype(np.int64, copy=False)
    candidate_end_rows = store.candidate_end_rows[resolved_indices].astype(np.int64, copy=False)
    candidate_counts = (candidate_end_rows - baseline_rows).astype(np.int64, copy=False)
    if np.any(candidate_counts <= 0):
        raise ValueError("evaluation requires at least one candidate row per sample")
    reachable_end_rows = np.minimum(
        candidate_end_rows,
        baseline_rows + int(store.max_candidate_slots),
    ).astype(np.int64, copy=False)
    last_candidate_rows = (reachable_end_rows - 1).astype(np.int64, copy=False)
    optimum_rows = np.empty(resolved_indices.shape[0], dtype=np.int64)
    for row, (start_row, end_row) in enumerate(
        zip(baseline_rows, reachable_end_rows, strict=True)
    ):
        optimum_rows[row] = int(
            start_row + np.argmin(store.log_base_fees[start_row:end_row])
        )
    return CandidateWindowSummary(
        anchor_rows=anchor_rows,
        baseline_rows=baseline_rows,
        last_candidate_rows=last_candidate_rows,
        optimum_rows=optimum_rows,
    )
