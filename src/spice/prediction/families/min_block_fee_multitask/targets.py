"""Paper-family target realization."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from ....temporal.problem_store import CompiledProblemStore
from ....temporal.realization import CompiledRealizationPolicyContract
from ...contracts import StagedPreparedTargets
from .batch import (
    estimate_min_block_fee_target_storage_bytes,
    materialize_min_block_fee_targets,
)

IntVector = NDArray[np.int64]


def prepare_min_block_fee_targets(
    store: CompiledProblemStore,
    sample_indices: IntVector,
    *,
    realization_policy: CompiledRealizationPolicyContract,
) -> StagedPreparedTargets:
    if sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")
    return StagedPreparedTargets(
        store=store,
        sample_indices=sample_indices.astype(np.int64, copy=False),
        realization_policy=realization_policy,
        estimated_storage_bytes=estimate_min_block_fee_target_storage_bytes(
            sample_count=int(sample_indices.shape[0]),
            max_candidate_slots=int(store.max_candidate_slots),
        ),
        materialize_fn=materialize_min_block_fee_targets,
    )
