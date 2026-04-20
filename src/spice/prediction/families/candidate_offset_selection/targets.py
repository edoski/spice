"""Current-family target realization."""

from __future__ import annotations

import numpy as np
import torch
from numpy.typing import NDArray

from ....temporal.problem_store import CompiledProblemStore
from ....temporal.realization import CompiledRealizationPolicyContract
from .batch import PreparedCandidateSlateTargets

IntVector = NDArray[np.int64]


def prepare_candidate_slate_targets(
    store: CompiledProblemStore,
    sample_indices: IntVector,
    *,
    realization_policy: CompiledRealizationPolicyContract,
) -> PreparedCandidateSlateTargets:
    if sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")
    sample_indices = sample_indices.astype(np.int64, copy=False)
    supervised = realization_policy.prepare_supervised_targets(store, sample_indices)
    return PreparedCandidateSlateTargets(
        candidate_log_fees=torch.from_numpy(supervised.candidate_log_fees),
        candidate_mask=torch.from_numpy(supervised.candidate_mask),
        optimum_offsets=torch.from_numpy(supervised.optimum_offsets),
        optimum_log_fees=torch.from_numpy(supervised.optimum_log_fees),
        baseline_candidate_indices=torch.from_numpy(supervised.baseline_candidate_indices),
    )
