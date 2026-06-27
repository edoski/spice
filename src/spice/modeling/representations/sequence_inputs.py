"""Fixed sequence model-input tensorization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
import torch
from numpy.typing import NDArray

from ...prediction import ModelInputBatch
from ...temporal.execution_policy import PreparedActionSpace
from ...temporal.problem_store import CompiledProblemStore

IntVector = NDArray[np.int64]


class SequenceInputBatch(NamedTuple):
    sample_positions: torch.Tensor
    inputs: torch.Tensor
    input_mask: torch.Tensor
    action_mask: torch.Tensor

    def to_device(self, device: torch.device) -> SequenceInputBatch:
        if (
            self.inputs.device == device
            and self.input_mask.device == device
            and self.action_mask.device == device
        ):
            return self
        non_blocking = device.type == "cuda"
        return SequenceInputBatch(
            sample_positions=self.sample_positions,
            inputs=self.inputs.to(device, non_blocking=non_blocking),
            input_mask=self.input_mask.to(device, non_blocking=non_blocking),
            action_mask=self.action_mask.to(device, non_blocking=non_blocking),
        )

    def model_kwargs(self) -> dict[str, torch.Tensor]:
        return {
            "inputs": self.inputs,
            "input_mask": self.input_mask,
        }

    def pin_memory(self) -> SequenceInputBatch:
        if self.inputs.device.type != "cpu":
            return self
        return SequenceInputBatch(
            sample_positions=self.sample_positions.pin_memory(),
            inputs=self.inputs.pin_memory(),
            input_mask=self.input_mask.pin_memory(),
            action_mask=self.action_mask.pin_memory(),
        )


def build_sequence_input_batch(
    store: CompiledProblemStore,
    sample_indices: IntVector,
    *,
    action_mask: NDArray[np.bool_],
    sample_positions: IntVector | torch.Tensor | None = None,
    max_context_length: int | None = None,
) -> SequenceInputBatch:
    layout = _sequence_input_layout_for_samples(
        store,
        sample_indices,
        empty_error="Sequence batches require at least one sample",
        max_context_length=max_context_length,
    )
    batch_size = int(layout.sample_indices.shape[0])
    if sample_positions is None:
        resolved_positions = np.arange(batch_size, dtype=np.int64)
    elif isinstance(sample_positions, torch.Tensor):
        resolved_positions = sample_positions.detach().cpu().numpy().astype(np.int64, copy=False)
    else:
        resolved_positions = sample_positions.astype(np.int64, copy=False)
    if resolved_positions.shape[0] != batch_size:
        raise ValueError("sample_positions must match sample_indices length")
    resolved_action_mask = _validated_action_mask(
        action_mask,
        sample_count=batch_size,
        max_candidate_slots=store.max_candidate_slots,
    )

    inputs = np.zeros((batch_size, layout.max_context_length, store.n_features), dtype=np.float32)
    input_mask = np.zeros((batch_size, layout.max_context_length), dtype=np.bool_)
    batch_action_mask = np.zeros((batch_size, store.max_candidate_slots), dtype=np.bool_)
    _fill_dense_sequence_input_rows(
        store,
        source_action_mask=resolved_action_mask,
        layout=layout,
        row_start=0,
        row_stop=batch_size,
        inputs=inputs,
        input_mask=input_mask,
        output_action_mask=batch_action_mask,
    )

    return SequenceInputBatch(
        sample_positions=torch.from_numpy(np.ascontiguousarray(resolved_positions)),
        inputs=torch.from_numpy(inputs),
        input_mask=torch.from_numpy(input_mask),
        action_mask=torch.from_numpy(batch_action_mask),
    )


@dataclass(frozen=True, slots=True)
class _SequenceInputLayout:
    sample_indices: IntVector
    context_lengths: IntVector
    max_context_length: int


@dataclass(slots=True)
class PreparedSequenceInputBatches:
    store: CompiledProblemStore
    action_space: PreparedActionSpace
    layout: _SequenceInputLayout

    @property
    def sample_count(self) -> int:
        return int(self.layout.sample_indices.shape[0])

    @property
    def batch_signatures(self) -> IntVector:
        return self.layout.context_lengths

    def build_batch(self, sample_positions: torch.Tensor) -> ModelInputBatch:
        positions = sample_positions.detach().cpu().numpy().astype(np.int64, copy=False)
        batch_sample_indices = self.layout.sample_indices[positions]
        return build_sequence_input_batch(
            self.store,
            batch_sample_indices,
            action_mask=self.action_space.action_mask[positions],
            sample_positions=sample_positions,
            max_context_length=self.layout.max_context_length,
        )

def prepare_sequence_input(
    store: CompiledProblemStore,
    *,
    action_space: PreparedActionSpace,
) -> PreparedSequenceInputBatches:
    layout = _sequence_input_layout(store, action_space)
    return PreparedSequenceInputBatches(
        store=store,
        action_space=action_space,
        layout=layout,
    )

def _sequence_input_layout(
    store: CompiledProblemStore,
    action_space: PreparedActionSpace,
) -> _SequenceInputLayout:
    return _sequence_input_layout_for_samples(
        store,
        action_space.sample_indices,
        empty_error="prepared sequence inputs require at least one sample",
    )


def _sequence_input_layout_for_samples(
    store: CompiledProblemStore,
    sample_indices: IntVector,
    *,
    empty_error: str,
    max_context_length: int | None = None,
) -> _SequenceInputLayout:
    if sample_indices.size == 0:
        raise ValueError(empty_error)
    resolved_sample_indices = sample_indices.astype(np.int64, copy=False)
    context = store.context_windows(resolved_sample_indices)
    resolved_max_context = (
        int(context.context_lengths.max())
        if max_context_length is None
        else int(max_context_length)
    )
    if np.any(context.context_lengths > resolved_max_context):
        raise ValueError("max_context_length is too small for the requested batch")
    return _SequenceInputLayout(
        sample_indices=resolved_sample_indices,
        context_lengths=context.context_lengths,
        max_context_length=resolved_max_context,
    )


def _validated_action_mask(
    action_mask: NDArray[np.bool_],
    *,
    sample_count: int,
    max_candidate_slots: int,
) -> NDArray[np.bool_]:
    resolved = action_mask.astype(np.bool_, copy=False)
    if resolved.shape != (sample_count, max_candidate_slots):
        raise ValueError("action_mask must match sample count and action width")
    return resolved


def _fill_dense_sequence_input_rows(
    store: CompiledProblemStore,
    source_action_mask: NDArray[np.bool_],
    layout: _SequenceInputLayout,
    *,
    row_start: int,
    row_stop: int,
    inputs: np.ndarray,
    input_mask: np.ndarray,
    output_action_mask: np.ndarray,
) -> None:
    sample_indices = layout.sample_indices[row_start:row_stop]
    context = store.context_windows(sample_indices)
    output_action_mask[:, :] = source_action_mask[row_start:row_stop]
    for output_row, (anchor_row, context_start) in enumerate(
        zip(context.anchor_rows, context.context_start_rows, strict=True)
    ):
        anchor_row = int(anchor_row)
        context_start = int(context_start)
        sequence = store.feature_matrix[context_start : anchor_row + 1]
        inputs[output_row, : sequence.shape[0], :] = sequence
        input_mask[output_row, : sequence.shape[0]] = True
