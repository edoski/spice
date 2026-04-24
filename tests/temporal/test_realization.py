from __future__ import annotations

import numpy as np
import pytest
import torch

from spice.prediction import DecodedOffsets
from spice.temporal import (
    coerce_realization_policy_config,
    compile_realization_policy_contract,
)
from spice.temporal.problem_store import CompiledProblemStore
from spice.temporal.semantics import ActionSpaceMode


def _realization_policy():
    return compile_realization_policy_contract(
        coerce_realization_policy_config({"id": "strict_deadline_miss"})
    )


def _store(action_space_mode: ActionSpaceMode) -> CompiledProblemStore:
    return CompiledProblemStore(
        feature_matrix=np.zeros((8, 1), dtype=np.float32),
        log_base_fees=np.log(np.array([100, 95, 90, 80, 75, 70, 60, 55], dtype=np.float32)),
        timestamps=np.arange(8, dtype=np.int64),
        anchor_rows=np.array([1, 4], dtype=np.int64),
        context_start_rows=np.array([0, 3], dtype=np.int64),
        candidate_start_rows=np.array([2, 5], dtype=np.int64),
        candidate_end_rows=np.array([4, 7], dtype=np.int64),
        action_space_mode=action_space_mode,
        max_candidate_slots=3,
    )


def test_strict_deadline_miss_rejects_negative_decoded_offsets() -> None:
    store = _store(ActionSpaceMode.REALIZED_PER_SAMPLE)

    with pytest.raises(ValueError, match="non-negative"):
        _realization_policy().realize_selections(
            store,
            DecodedOffsets(torch.tensor([-1, 0], dtype=torch.int64)),
            np.arange(store.n_samples, dtype=np.int64),
            np.array([0], dtype=np.int64),
        )


def test_fixed_ex_ante_overflow_realizes_first_post_window_row() -> None:
    store = _store(ActionSpaceMode.FIXED_EX_ANTE)

    realized = _realization_policy().realize_selections(
        store,
        DecodedOffsets(torch.tensor([2, 2], dtype=torch.int64)),
        np.arange(store.n_samples, dtype=np.int64),
        np.arange(store.n_samples, dtype=np.int64),
    )

    np.testing.assert_array_equal(realized.realized_rows, np.array([4, 7], dtype=np.int64))
    np.testing.assert_array_equal(realized.resolved_offsets, np.array([2, 2], dtype=np.int64))
    np.testing.assert_array_equal(realized.overflow_mask, np.array([True, True]))
