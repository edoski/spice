"""PyTorch batch adapters for the shared sequence-event representation."""

from __future__ import annotations

import math
from collections.abc import Iterator
from typing import NamedTuple

import numpy as np
import torch
from numpy.typing import NDArray

from ..data.datasets import TemporalDatasetStore
from .representations import InputRepresentationSpec, register_input_representation

IntVector = NDArray[np.int64]


class SequenceEventBatch(NamedTuple):
    inputs: torch.Tensor
    input_mask: torch.Tensor
    candidate_log_fees: torch.Tensor
    candidate_mask: torch.Tensor


def build_sequence_event_batch(
    store: TemporalDatasetStore,
    sample_indices: IntVector,
) -> SequenceEventBatch:
    if sample_indices.size == 0:
        raise ValueError("Sequence batches require at least one sample")
    sample_indices = sample_indices.astype(np.int64, copy=False)
    anchor_rows = store.anchor_rows[sample_indices]
    context_starts = store.context_start_rows[sample_indices]
    input_lengths = anchor_rows - context_starts + 1
    max_input_length = int(input_lengths.max())
    batch_size = int(sample_indices.shape[0])

    inputs = np.zeros((batch_size, max_input_length, store.n_features), dtype=np.float32)
    input_mask = np.zeros((batch_size, max_input_length), dtype=np.bool_)
    candidate_log_fees = np.zeros((batch_size, store.max_candidate_slots), dtype=np.float32)
    candidate_mask = np.zeros((batch_size, store.max_candidate_slots), dtype=np.bool_)

    for row, sample_index in enumerate(sample_indices):
        anchor_row = int(store.anchor_rows[sample_index])
        context_start = int(store.context_start_rows[sample_index])
        candidate_end = int(store.candidate_end_rows[sample_index])
        sequence = store.feature_matrix[context_start : anchor_row + 1]
        candidate_values = store.log_base_fees[anchor_row + 1 : candidate_end]
        inputs[row, : sequence.shape[0], :] = sequence
        input_mask[row, : sequence.shape[0]] = True
        candidate_log_fees[row, : candidate_values.shape[0]] = candidate_values
        candidate_mask[row, : candidate_values.shape[0]] = True

    return SequenceEventBatch(
        inputs=torch.from_numpy(inputs),
        input_mask=torch.from_numpy(input_mask),
        candidate_log_fees=torch.from_numpy(candidate_log_fees),
        candidate_mask=torch.from_numpy(candidate_mask),
    )


class SequenceEventBatchLoader:
    """Batch-native loader over a ragged timestamp-native temporal dataset store."""

    def __init__(
        self,
        store: TemporalDatasetStore,
        sample_indices: IntVector,
        *,
        batch_size: int,
        shuffle: bool = False,
    ) -> None:
        if sample_indices.size == 0:
            raise ValueError("SequenceEventBatchLoader requires at least one sample")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self.store = store
        self.sample_indices = sample_indices.astype(np.int64, copy=False)
        self.batch_size = batch_size
        self.shuffle = shuffle

    def __len__(self) -> int:
        return math.ceil(int(self.sample_indices.shape[0]) / self.batch_size)

    def __iter__(self) -> Iterator[SequenceEventBatch]:
        order = self.sample_indices
        if self.shuffle:
            order = np.random.permutation(order)
        for offset in range(0, int(order.shape[0]), self.batch_size):
            batch_indices = order[offset : offset + self.batch_size]
            yield build_sequence_event_batch(self.store, batch_indices)


def move_batch_to_device(
    batch: SequenceEventBatch,
    device: torch.device,
) -> SequenceEventBatch:
    return SequenceEventBatch(*(tensor.to(device) for tensor in batch))


def _build_sequence_event_loader(
    store: TemporalDatasetStore,
    sample_indices: IntVector,
    *,
    batch_size: int,
    shuffle: bool = False,
) -> SequenceEventBatchLoader:
    return SequenceEventBatchLoader(
        store,
        sample_indices,
        batch_size=batch_size,
        shuffle=shuffle,
    )


register_input_representation(
    InputRepresentationSpec(
        id="sequence_event",
        build_loader=_build_sequence_event_loader,
    )
)
