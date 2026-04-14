"""Paper-family target realization."""

from __future__ import annotations

import numpy as np
import torch
from numpy.typing import NDArray

from ....temporal.problem_store import CompiledProblemStore
from .batch import PreparedMinBlockFeeTargets

IntVector = NDArray[np.int64]


def prepare_min_block_fee_targets(
    store: CompiledProblemStore,
    sample_indices: IntVector,
) -> PreparedMinBlockFeeTargets:
    if sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")
    sample_indices = sample_indices.astype(np.int64, copy=False)
    anchor_rows = store.anchor_rows[sample_indices]
    candidate_ends = store.candidate_end_rows[sample_indices]
    candidate_counts = candidate_ends - (anchor_rows + 1)
    batch_size = int(sample_indices.shape[0])
    max_candidate_slots = int(candidate_counts.max())
    candidate_mask = np.zeros((batch_size, max_candidate_slots), dtype=np.bool_)
    min_block_offsets = np.zeros(batch_size, dtype=np.int64)
    min_block_log_fees = np.zeros(batch_size, dtype=np.float32)
    for row, sample_index in enumerate(sample_indices):
        anchor_row = int(store.anchor_rows[sample_index])
        candidate_end = int(store.candidate_end_rows[sample_index])
        candidate_values = store.log_base_fees[anchor_row + 1 : candidate_end]
        candidate_mask[row, : candidate_values.shape[0]] = True
        min_offset = int(np.argmin(candidate_values))
        min_block_offsets[row] = min_offset
        min_block_log_fees[row] = float(candidate_values[min_offset])
    return PreparedMinBlockFeeTargets(
        candidate_mask=torch.from_numpy(candidate_mask),
        min_block_offsets=torch.from_numpy(min_block_offsets),
        min_block_log_fees=torch.from_numpy(min_block_log_fees),
    )
