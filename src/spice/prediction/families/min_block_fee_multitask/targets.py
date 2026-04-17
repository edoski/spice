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
    fixed_class_space = store.fixed_candidate_class_space
    max_candidate_slots = (
        int(store.max_candidate_slots) if fixed_class_space else int(candidate_counts.max())
    )
    candidate_mask = np.zeros((batch_size, max_candidate_slots), dtype=np.bool_)
    if store.precomputed_min_block_offsets is not None:
        min_block_offsets = store.precomputed_min_block_offsets[sample_indices].astype(
            np.int64,
            copy=False,
        )
    else:
        min_block_offsets = np.zeros(batch_size, dtype=np.int64)
    if store.precomputed_min_block_log_fees is not None:
        min_block_log_fees = store.precomputed_min_block_log_fees[sample_indices].astype(
            np.float32,
            copy=False,
        )
    else:
        min_block_log_fees = np.zeros(batch_size, dtype=np.float32)
    for row, sample_index in enumerate(sample_indices):
        anchor_row = int(store.anchor_rows[sample_index])
        candidate_end = int(store.candidate_end_rows[sample_index])
        candidate_values = store.log_base_fees[anchor_row + 1 : candidate_end]
        candidate_mask[row, : candidate_values.shape[0]] = True
        if (
            store.precomputed_min_block_offsets is None
            or store.precomputed_min_block_log_fees is None
        ):
            min_offset = int(np.argmin(candidate_values))
            if fixed_class_space:
                min_offset = min(min_offset, max_candidate_slots - 1)
            min_block_offsets[row] = min_offset
            min_block_log_fees[row] = float(candidate_values[min_offset])
    return PreparedMinBlockFeeTargets(
        candidate_mask=torch.from_numpy(candidate_mask),
        min_block_offsets=torch.from_numpy(min_block_offsets),
        min_block_log_fees=torch.from_numpy(min_block_log_fees),
    )
