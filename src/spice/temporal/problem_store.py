"""Legacy problem-store value types retained for later reader deletion."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatMatrix = NDArray[np.float32]
FloatVector = NDArray[np.float32]
IntVector = NDArray[np.int64]


@dataclass(frozen=True, slots=True)
class ContextWindowSummary:
    context_start_rows: IntVector
    anchor_rows: IntVector
    context_lengths: IntVector


@dataclass(frozen=True, slots=True)
class CandidateWindowSummary:
    anchor_rows: IntVector
    candidate_start_rows: IntVector
    candidate_end_rows: IntVector
    candidate_counts: IntVector
    reachable_end_rows: IntVector


@dataclass(slots=True)
class CompiledProblemStore:
    feature_matrix: FloatMatrix
    log_base_fees: FloatVector
    timestamps: IntVector
    anchor_rows: IntVector
    context_start_rows: IntVector
    candidate_start_rows: IntVector
    candidate_end_rows: IntVector
    max_candidate_slots: int
    block_numbers: IntVector | None = None
