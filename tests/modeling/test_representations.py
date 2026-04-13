from __future__ import annotations

import numpy as np
import torch

from spice.modeling.inference import predict_candidate_offsets
from spice.modeling.models import ModelOutputs, TemporalModel, take_last_valid
from spice.modeling.representations import (
    RepresentationRuntimeContext,
    build_sequence_event_batch,
    prepare_representation,
)
from spice.temporal.store import TemporalDatasetStore


def _test_store() -> TemporalDatasetStore:
    return TemporalDatasetStore(
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
            ],
            dtype=np.float32,
        ),
        log_base_fees=np.array(
            [0.1, 0.2, 0.15, 0.3, 0.25, 0.05, 0.4, 0.12, 0.22, 0.18],
            dtype=np.float32,
        ),
        timestamps=np.array([0, 5, 11, 19, 28, 40, 55, 71, 88, 106], dtype=np.int64),
        anchor_rows=np.array([2, 4, 5, 7], dtype=np.int64),
        context_start_rows=np.array([0, 1, 0, 4], dtype=np.int64),
        candidate_end_rows=np.array([5, 8, 7, 10], dtype=np.int64),
        max_candidate_slots=3,
    )


class _ToyTemporalModel(TemporalModel):
    def __init__(self, n_candidate_slots: int) -> None:
        super().__init__()
        self.n_candidate_slots = n_candidate_slots

    def forward(self, inputs: torch.Tensor, input_mask: torch.Tensor) -> ModelOutputs:
        last = take_last_valid(inputs, input_mask)
        base = last[:, 0]
        logits = torch.stack(
            (
                base,
                -base,
                torch.zeros_like(base),
            ),
            dim=1,
        )
        return ModelOutputs(logits=logits[:, : self.n_candidate_slots])


def test_sequence_event_storage_modes_yield_identical_batches() -> None:
    store = _test_store()
    sample_indices = np.array([3, 0, 2, 1], dtype=np.int64)
    streaming = prepare_representation(
        "sequence_event",
        store,
        sample_indices,
        runtime_context=RepresentationRuntimeContext(
            device_type="cpu",
            batch_size=2,
            available_memory_bytes=1,
        ),
    )
    materialized = prepare_representation(
        "sequence_event",
        store,
        sample_indices,
        runtime_context=RepresentationRuntimeContext(
            device_type="cpu",
            batch_size=2,
            available_memory_bytes=1 << 40,
        ),
    )

    assert streaming.storage_mode_id == "streaming"
    assert materialized.storage_mode_id == "materialized_dense"
    assert streaming.batch_planner_id == materialized.batch_planner_id == "signature_bucketed"

    streaming_batches = list(streaming.iter_batches(epoch=2, seed=2026, shuffle=True))
    materialized_batches = list(materialized.iter_batches(epoch=2, seed=2026, shuffle=True))

    assert len(streaming_batches) == len(materialized_batches)
    for streaming_batch, materialized_batch in zip(
        streaming_batches,
        materialized_batches,
        strict=True,
    ):
        assert torch.equal(streaming_batch.sample_positions, materialized_batch.sample_positions)
        assert torch.equal(streaming_batch.inputs, materialized_batch.inputs)
        assert torch.equal(streaming_batch.input_mask, materialized_batch.input_mask)
        assert torch.equal(
            streaming_batch.candidate_log_fees,
            materialized_batch.candidate_log_fees,
        )
        assert torch.equal(streaming_batch.candidate_mask, materialized_batch.candidate_mask)


def test_signature_bucketed_batches_cover_each_sample_once_per_epoch() -> None:
    store = _test_store()
    sample_indices = np.array([3, 0, 2, 1], dtype=np.int64)
    prepared = prepare_representation(
        "sequence_event",
        store,
        sample_indices,
        runtime_context=RepresentationRuntimeContext(
            device_type="cpu",
            batch_size=2,
            available_memory_bytes=1 << 40,
        ),
    )

    first_epoch = list(prepared.iter_batches(epoch=1, seed=2026, shuffle=True))
    second_epoch = list(prepared.iter_batches(epoch=1, seed=2026, shuffle=True))

    first_positions = torch.cat([batch.sample_positions for batch in first_epoch]).numpy()
    second_positions = torch.cat([batch.sample_positions for batch in second_epoch]).numpy()

    assert np.array_equal(first_positions, second_positions)
    assert np.array_equal(np.sort(first_positions), np.arange(sample_indices.shape[0]))
    assert len(np.unique(first_positions)) == sample_indices.shape[0]
    assert all(batch.inputs.shape[0] <= 2 for batch in first_epoch)


def test_predict_candidate_offsets_restores_original_sample_order() -> None:
    store = _test_store()
    sample_indices = np.array([3, 0, 2, 1], dtype=np.int64)
    prepared = prepare_representation(
        "sequence_event",
        store,
        sample_indices,
        runtime_context=RepresentationRuntimeContext(
            device_type="cpu",
            batch_size=2,
            available_memory_bytes=1 << 40,
        ),
    )
    ordered_positions = torch.cat(
        [batch.sample_positions for batch in prepared.iter_batches(epoch=0, seed=0, shuffle=False)]
    ).numpy()
    assert not np.array_equal(ordered_positions, np.arange(sample_indices.shape[0]))

    model = _ToyTemporalModel(store.max_candidate_slots)
    expected_batch = build_sequence_event_batch(store, sample_indices)
    expected_logits = model(expected_batch.inputs, expected_batch.input_mask).logits
    expected_logits = expected_logits.masked_fill(
        ~expected_batch.candidate_mask,
        torch.finfo(expected_logits.dtype).min,
    )
    expected = expected_logits.argmax(dim=-1).tolist()

    actual = predict_candidate_offsets(
        model,
        model_id="lstm",
        store=store,
        sample_indices=sample_indices,
        batch_size=2,
        device="cpu",
    )

    assert actual == expected
