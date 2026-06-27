from __future__ import annotations

import numpy as np
import torch

from spice.modeling.representations import prepare_sequence_input
from spice.temporal import PreparedActionSpace
from spice.temporal.problem_store import CompiledProblemStore


def _test_store() -> CompiledProblemStore:
    return CompiledProblemStore(
        feature_matrix=np.array(
            [
                [-1.0, 0.0, 0.1],
                [-2.0, 0.1, 0.2],
                [0.5, 0.2, 0.3],
                [1.5, 0.3, 0.4],
                [-0.2, 0.4, 0.5],
                [2.0, 0.5, 0.6],
                [-1.1, 0.6, 0.7],
                [0.3, 0.7, 0.8],
                [1.2, 0.8, 0.9],
                [-0.7, 0.9, 1.0],
                [0.9, 1.0, 1.1],
            ],
            dtype=np.float32,
        ),
        log_base_fees=np.array(
            [0.1, 0.2, 0.15, 0.3, 0.25, 0.05, 0.4, 0.12, 0.22, 0.18, 0.2],
            dtype=np.float32,
        ),
        timestamps=np.array([0, 5, 11, 19, 28, 40, 55, 71, 88, 106, 125], dtype=np.int64),
        anchor_rows=np.array([2, 4, 5, 7], dtype=np.int64),
        context_start_rows=np.array([0, 1, 0, 4], dtype=np.int64),
        candidate_start_rows=np.array([3, 5, 6, 8], dtype=np.int64),
        candidate_end_rows=np.array([5, 8, 7, 10], dtype=np.int64),
        max_candidate_slots=3,
    )


def _action_space(sample_indices: np.ndarray) -> PreparedActionSpace:
    mask = np.ones((sample_indices.shape[0], 3), dtype=np.bool_)
    mask[:, -1] = False
    return PreparedActionSpace(
        sample_indices=sample_indices,
        max_candidate_slots=3,
        action_mask=mask,
    )


def test_sequence_input_batches_preserve_positions_contexts_and_masks() -> None:
    store = _test_store()
    sample_indices = np.array([3, 0, 2, 1], dtype=np.int64)
    prepared = prepare_sequence_input(
        store,
        action_space=_action_space(sample_indices),
    )

    batch = prepared.build_batch(torch.as_tensor([0, 2], dtype=torch.int64))

    assert prepared.sample_count == 4
    assert prepared.batch_signatures.tolist() == [4, 3, 6, 4]
    assert batch.sample_positions.tolist() == [0, 2]
    assert batch.inputs.shape == (2, 6, 3)
    assert batch.input_mask.tolist() == [
        [True, True, True, True, False, False],
        [True, True, True, True, True, True],
    ]
    assert batch.action_mask.tolist() == [
        [True, True, False],
        [True, True, False],
    ]


def test_sequence_input_to_device_is_noop_when_already_on_device() -> None:
    prepared = prepare_sequence_input(
        _test_store(),
        action_space=_action_space(np.array([0, 1], dtype=np.int64)),
    )
    batch = prepared.build_batch(torch.as_tensor([0], dtype=torch.int64))

    assert batch.to_device(torch.device("cpu")) is batch
