"""Internal model-input representation registry and realization helpers."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import NamedTuple, Protocol

import numpy as np
import torch
from numpy.typing import NDArray

from ..temporal.problem_store import CompiledProblemStore
from .problem_batches import CandidateChoiceTargets, TemporalProblemBatch

IntVector = NDArray[np.int64]
_MAX_AUTOMATIC_MATERIALIZATION_BYTES = 8 * 1024**3


class SequenceEventBatch(NamedTuple):
    sample_positions: torch.Tensor
    inputs: torch.Tensor
    input_mask: torch.Tensor
    candidate_log_fees: torch.Tensor
    candidate_mask: torch.Tensor

    def to_device(self, device: torch.device) -> SequenceEventBatch:
        return SequenceEventBatch(
            sample_positions=self.sample_positions,
            inputs=self.inputs.to(device),
            input_mask=self.input_mask.to(device),
            candidate_log_fees=self.candidate_log_fees.to(device),
            candidate_mask=self.candidate_mask.to(device),
        )

    def model_kwargs(self) -> dict[str, torch.Tensor]:
        return {
            "inputs": self.inputs,
            "input_mask": self.input_mask,
        }

    def objective_targets(self) -> CandidateChoiceTargets:
        return CandidateChoiceTargets(
            candidate_log_fees=self.candidate_log_fees,
            candidate_mask=self.candidate_mask,
        )


@dataclass(frozen=True, slots=True)
class RepresentationRuntimeContext:
    device_type: str
    batch_size: int
    available_memory_bytes: int


class PreparedRepresentation(Protocol):
    representation_id: str
    storage_mode_id: str
    batch_planner_id: str

    def __len__(self) -> int: ...

    def iter_batches(
        self,
        *,
        epoch: int,
        seed: int,
        shuffle: bool,
    ) -> Iterator[TemporalProblemBatch]: ...


class RepresentationLoader(Protocol):
    representation_id: str
    storage_mode_id: str
    batch_planner_id: str

    def __iter__(self) -> Iterator[TemporalProblemBatch]: ...

    def __len__(self) -> int: ...


@dataclass(frozen=True, slots=True)
class InputRepresentationSpec:
    id: str
    prepare: Callable[..., PreparedRepresentation]


class PreparedRepresentationLoader:
    def __init__(
        self,
        prepared: PreparedRepresentation,
        *,
        seed: int,
        shuffle: bool,
    ) -> None:
        self.prepared = prepared
        self.seed = seed
        self.shuffle = shuffle
        self._epoch = 0

    @property
    def representation_id(self) -> str:
        return self.prepared.representation_id

    @property
    def storage_mode_id(self) -> str:
        return self.prepared.storage_mode_id

    @property
    def batch_planner_id(self) -> str:
        return self.prepared.batch_planner_id

    def __len__(self) -> int:
        return len(self.prepared)

    def __iter__(self) -> Iterator[TemporalProblemBatch]:
        epoch = self._epoch if self.shuffle else 0
        iterator = self.prepared.iter_batches(
            epoch=epoch,
            seed=self.seed,
            shuffle=self.shuffle,
        )
        if self.shuffle:
            self._epoch += 1
        return iterator


_REPRESENTATIONS: dict[str, InputRepresentationSpec] = {}


def register_input_representation(spec: InputRepresentationSpec) -> None:
    existing = _REPRESENTATIONS.get(spec.id)
    if existing is not None:
        raise ValueError(f"Duplicate input representation id: {spec.id}")
    _REPRESENTATIONS[spec.id] = spec


def input_representation_spec(representation_id: str) -> InputRepresentationSpec:
    try:
        return _REPRESENTATIONS[representation_id]
    except KeyError as exc:
        known = ", ".join(sorted(_REPRESENTATIONS))
        raise ValueError(
            f"Unknown input representation: {representation_id}. Known representations: {known}"
        ) from exc


def prepare_representation(
    representation_id: str,
    store: CompiledProblemStore,
    sample_indices: IntVector,
    *,
    runtime_context: RepresentationRuntimeContext,
) -> PreparedRepresentation:
    spec = input_representation_spec(representation_id)
    return spec.prepare(
        store,
        sample_indices,
        runtime_context=runtime_context,
    )


def build_representation_loader(
    representation_id: str,
    store: CompiledProblemStore,
    sample_indices: IntVector,
    *,
    runtime_context: RepresentationRuntimeContext,
    seed: int,
    shuffle: bool = False,
) -> PreparedRepresentationLoader:
    prepared = prepare_representation(
        representation_id,
        store,
        sample_indices,
        runtime_context=runtime_context,
    )
    return PreparedRepresentationLoader(
        prepared,
        seed=seed,
        shuffle=shuffle,
    )


def build_sequence_event_batch(
    store: CompiledProblemStore,
    sample_indices: IntVector,
    *,
    sample_positions: IntVector | None = None,
    max_context_length: int | None = None,
    max_candidate_slots: int | None = None,
) -> SequenceEventBatch:
    if sample_indices.size == 0:
        raise ValueError("Sequence batches require at least one sample")
    sample_indices = sample_indices.astype(np.int64, copy=False)
    anchor_rows = store.anchor_rows[sample_indices]
    context_starts = store.context_start_rows[sample_indices]
    candidate_ends = store.candidate_end_rows[sample_indices]
    input_lengths = anchor_rows - context_starts + 1
    candidate_counts = candidate_ends - (anchor_rows + 1)
    batch_size = int(sample_indices.shape[0])
    resolved_positions = (
        np.arange(batch_size, dtype=np.int64)
        if sample_positions is None
        else sample_positions.astype(np.int64, copy=False)
    )
    if resolved_positions.shape[0] != batch_size:
        raise ValueError("sample_positions must match sample_indices length")
    resolved_max_context = (
        int(input_lengths.max()) if max_context_length is None else int(max_context_length)
    )
    resolved_max_candidate_slots = (
        int(candidate_counts.max()) if max_candidate_slots is None else int(max_candidate_slots)
    )
    if np.any(input_lengths > resolved_max_context):
        raise ValueError("max_context_length is too small for the requested batch")
    if np.any(candidate_counts > resolved_max_candidate_slots):
        raise ValueError("max_candidate_slots is too small for the requested batch")

    inputs = np.zeros((batch_size, resolved_max_context, store.n_features), dtype=np.float32)
    input_mask = np.zeros((batch_size, resolved_max_context), dtype=np.bool_)
    candidate_log_fees = np.zeros(
        (batch_size, resolved_max_candidate_slots),
        dtype=np.float32,
    )
    candidate_mask = np.zeros((batch_size, resolved_max_candidate_slots), dtype=np.bool_)

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
        sample_positions=torch.from_numpy(np.ascontiguousarray(resolved_positions)),
        inputs=torch.from_numpy(inputs),
        input_mask=torch.from_numpy(input_mask),
        candidate_log_fees=torch.from_numpy(candidate_log_fees),
        candidate_mask=torch.from_numpy(candidate_mask),
    )

@dataclass(frozen=True, slots=True)
class _SequenceEventLayout:
    sample_indices: IntVector
    context_lengths: IntVector
    candidate_counts: IntVector
    max_context_length: int
    max_candidate_slots: int


@dataclass(slots=True)
class _StreamingSequenceEventRepresentation:
    store: CompiledProblemStore
    layout: _SequenceEventLayout
    batch_size: int
    representation_id: str = "sequence_event"
    storage_mode_id: str = "streaming"
    batch_planner_id: str = "signature_bucketed"

    def __len__(self) -> int:
        return math.ceil(int(self.layout.sample_indices.shape[0]) / self.batch_size)

    def iter_batches(
        self,
        *,
        epoch: int,
        seed: int,
        shuffle: bool,
    ) -> Iterator[TemporalProblemBatch]:
        order = _sequence_event_order(
            self.layout,
            epoch=epoch,
            seed=seed,
            shuffle=shuffle,
        )
        for offset in range(0, int(order.shape[0]), self.batch_size):
            batch_positions = order[offset : offset + self.batch_size]
            batch_sample_indices = self.layout.sample_indices[batch_positions]
            yield build_sequence_event_batch(
                self.store,
                batch_sample_indices,
                sample_positions=batch_positions,
                max_context_length=self.layout.max_context_length,
                max_candidate_slots=self.layout.max_candidate_slots,
            )


@dataclass(slots=True)
class _MaterializedSequenceEventRepresentation:
    inputs: torch.Tensor
    input_mask: torch.Tensor
    candidate_log_fees: torch.Tensor
    candidate_mask: torch.Tensor
    layout: _SequenceEventLayout
    batch_size: int
    representation_id: str = "sequence_event"
    storage_mode_id: str = "materialized_dense"
    batch_planner_id: str = "signature_bucketed"

    def __len__(self) -> int:
        return math.ceil(int(self.layout.sample_indices.shape[0]) / self.batch_size)

    def iter_batches(
        self,
        *,
        epoch: int,
        seed: int,
        shuffle: bool,
    ) -> Iterator[TemporalProblemBatch]:
        order = _sequence_event_order(
            self.layout,
            epoch=epoch,
            seed=seed,
            shuffle=shuffle,
        )
        for offset in range(0, int(order.shape[0]), self.batch_size):
            batch_positions = order[offset : offset + self.batch_size]
            index = torch.from_numpy(np.ascontiguousarray(batch_positions))
            yield SequenceEventBatch(
                sample_positions=index,
                inputs=self.inputs.index_select(0, index),
                input_mask=self.input_mask.index_select(0, index),
                candidate_log_fees=self.candidate_log_fees.index_select(0, index),
                candidate_mask=self.candidate_mask.index_select(0, index),
            )


def _prepare_sequence_event(
    store: CompiledProblemStore,
    sample_indices: IntVector,
    *,
    runtime_context: RepresentationRuntimeContext,
) -> PreparedRepresentation:
    if runtime_context.batch_size <= 0:
        raise ValueError("runtime_context.batch_size must be positive")
    layout = _sequence_event_layout(store, sample_indices)
    dense_storage_bytes = _dense_sequence_event_storage_bytes(layout, store.n_features)
    materialization_budget = min(
        _MAX_AUTOMATIC_MATERIALIZATION_BYTES,
        max(0, runtime_context.available_memory_bytes // 5),
    )
    if dense_storage_bytes <= materialization_budget:
        return _materialize_sequence_event(store, layout, batch_size=runtime_context.batch_size)
    return _StreamingSequenceEventRepresentation(
        store=store,
        layout=layout,
        batch_size=runtime_context.batch_size,
    )


def _sequence_event_layout(
    store: CompiledProblemStore,
    sample_indices: IntVector,
) -> _SequenceEventLayout:
    if sample_indices.size == 0:
        raise ValueError("Prepared representations require at least one sample")
    resolved_sample_indices = sample_indices.astype(np.int64, copy=False)
    anchor_rows = store.anchor_rows[resolved_sample_indices]
    context_starts = store.context_start_rows[resolved_sample_indices]
    candidate_ends = store.candidate_end_rows[resolved_sample_indices]
    context_lengths = (anchor_rows - context_starts + 1).astype(np.int64, copy=False)
    candidate_counts = (candidate_ends - (anchor_rows + 1)).astype(np.int64, copy=False)
    return _SequenceEventLayout(
        sample_indices=resolved_sample_indices,
        context_lengths=context_lengths,
        candidate_counts=candidate_counts,
        max_context_length=int(context_lengths.max()),
        max_candidate_slots=int(candidate_counts.max()),
    )


def _dense_sequence_event_storage_bytes(
    layout: _SequenceEventLayout,
    n_features: int,
) -> int:
    sample_count = int(layout.sample_indices.shape[0])
    inputs_bytes = (
        sample_count
        * layout.max_context_length
        * n_features
        * np.dtype(np.float32).itemsize
    )
    input_mask_bytes = sample_count * layout.max_context_length * np.dtype(np.bool_).itemsize
    candidate_bytes = (
        sample_count * layout.max_candidate_slots * np.dtype(np.float32).itemsize
    )
    candidate_mask_bytes = (
        sample_count * layout.max_candidate_slots * np.dtype(np.bool_).itemsize
    )
    return inputs_bytes + input_mask_bytes + candidate_bytes + candidate_mask_bytes


def _sequence_event_order(
    layout: _SequenceEventLayout,
    *,
    epoch: int,
    seed: int,
    shuffle: bool,
) -> IntVector:
    order = np.arange(layout.sample_indices.shape[0], dtype=np.int64)
    if shuffle:
        rng = np.random.default_rng(np.random.SeedSequence([seed, epoch]))
        order = rng.permutation(order)
    signatures = (
        layout.candidate_counts[order].astype(np.int64) << 32
    ) | layout.context_lengths[order].astype(np.int64)
    return order[np.argsort(signatures, kind="stable")]


def _materialize_sequence_event(
    store: CompiledProblemStore,
    layout: _SequenceEventLayout,
    *,
    batch_size: int,
) -> _MaterializedSequenceEventRepresentation:
    sample_count = int(layout.sample_indices.shape[0])
    inputs = np.zeros(
        (sample_count, layout.max_context_length, store.n_features),
        dtype=np.float32,
    )
    input_mask = np.zeros((sample_count, layout.max_context_length), dtype=np.bool_)
    candidate_log_fees = np.zeros(
        (sample_count, layout.max_candidate_slots),
        dtype=np.float32,
    )
    candidate_mask = np.zeros((sample_count, layout.max_candidate_slots), dtype=np.bool_)

    for row, sample_index in enumerate(layout.sample_indices):
        anchor_row = int(store.anchor_rows[sample_index])
        context_start = int(store.context_start_rows[sample_index])
        candidate_end = int(store.candidate_end_rows[sample_index])
        sequence = store.feature_matrix[context_start : anchor_row + 1]
        candidate_values = store.log_base_fees[anchor_row + 1 : candidate_end]
        inputs[row, : sequence.shape[0], :] = sequence
        input_mask[row, : sequence.shape[0]] = True
        candidate_log_fees[row, : candidate_values.shape[0]] = candidate_values
        candidate_mask[row, : candidate_values.shape[0]] = True

    return _MaterializedSequenceEventRepresentation(
        inputs=torch.from_numpy(inputs),
        input_mask=torch.from_numpy(input_mask),
        candidate_log_fees=torch.from_numpy(candidate_log_fees),
        candidate_mask=torch.from_numpy(candidate_mask),
        layout=layout,
        batch_size=batch_size,
    )


register_input_representation(
    InputRepresentationSpec(
        id="sequence_event",
        prepare=_prepare_sequence_event,
    )
)
