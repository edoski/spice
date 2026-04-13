from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Literal, NamedTuple

import numpy as np
import torch

from spice.config import TrainingPrecision
from spice.config.models import CompileMode, EarlyStoppingConfig, TrainingConfig
from spice.modeling._runtime import build_model_loader, build_representation_runtime_context
from spice.modeling.families.base import ModelConfig, ModelTuningSpaceConfig, TunedModelParams
from spice.modeling.families.registry import ModelSpec, model_spec, register_model_spec
from spice.modeling.inference import predict_candidate_offsets
from spice.modeling.models import ModelOutputs, TemporalModel, take_last_valid
from spice.modeling.problem_batches import CandidateChoiceTargets, TemporalProblemBatch
from spice.modeling.representations import (
    InputRepresentationSpec,
    RepresentationRuntimeContext,
    SequenceEventBatch,
    build_sequence_event_batch,
    input_representation_spec,
    prepare_representation,
    register_input_representation,
)
from spice.modeling.training import evaluate_model
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


class _FlatProblemBatch(NamedTuple):
    sample_positions: torch.Tensor
    flat_inputs: torch.Tensor
    candidate_log_fees: torch.Tensor
    candidate_mask: torch.Tensor

    def to_device(self, device: torch.device) -> _FlatProblemBatch:
        return _FlatProblemBatch(
            sample_positions=self.sample_positions,
            flat_inputs=self.flat_inputs.to(device),
            candidate_log_fees=self.candidate_log_fees.to(device),
            candidate_mask=self.candidate_mask.to(device),
        )

    def model_kwargs(self) -> Mapping[str, torch.Tensor]:
        return {"flat_inputs": self.flat_inputs}

    def objective_targets(self) -> CandidateChoiceTargets:
        return CandidateChoiceTargets(
            candidate_log_fees=self.candidate_log_fees,
            candidate_mask=self.candidate_mask,
        )


class _FlatPreparedRepresentation:
    representation_id = "test_flat_problem"
    storage_mode_id = "flat_dense"
    batch_planner_id = "flat_sequential"

    def __init__(
        self,
        *,
        flat_inputs: torch.Tensor,
        candidate_log_fees: torch.Tensor,
        candidate_mask: torch.Tensor,
        batch_size: int,
    ) -> None:
        self._flat_inputs = flat_inputs
        self._candidate_log_fees = candidate_log_fees
        self._candidate_mask = candidate_mask
        self._batch_size = batch_size

    def __len__(self) -> int:
        sample_count = int(self._flat_inputs.shape[0])
        return (sample_count + self._batch_size - 1) // self._batch_size

    def iter_batches(
        self,
        *,
        epoch: int,
        seed: int,
        shuffle: bool,
    ) -> Iterator[TemporalProblemBatch]:
        del epoch, seed
        positions = np.arange(int(self._flat_inputs.shape[0]), dtype=np.int64)
        if shuffle:
            positions = positions[::-1]
        for offset in range(0, positions.shape[0], self._batch_size):
            batch_positions = positions[offset : offset + self._batch_size]
            index = torch.from_numpy(np.ascontiguousarray(batch_positions))
            yield _FlatProblemBatch(
                sample_positions=index,
                flat_inputs=self._flat_inputs.index_select(0, index),
                candidate_log_fees=self._candidate_log_fees.index_select(0, index),
                candidate_mask=self._candidate_mask.index_select(0, index),
            )


def _prepare_flat_problem(
    store: CompiledProblemStore,
    sample_indices: np.ndarray,
    *,
    runtime_context: RepresentationRuntimeContext,
) -> _FlatPreparedRepresentation:
    flat_inputs = torch.from_numpy(store.feature_matrix[store.anchor_rows[sample_indices]])
    candidate_counts = (
        store.candidate_end_rows[sample_indices] - (store.anchor_rows[sample_indices] + 1)
    )
    max_candidate_slots = int(candidate_counts.max())
    candidate_log_fees = np.zeros((sample_indices.shape[0], max_candidate_slots), dtype=np.float32)
    candidate_mask = np.zeros((sample_indices.shape[0], max_candidate_slots), dtype=np.bool_)
    for row, sample_index in enumerate(sample_indices.tolist()):
        anchor_row = int(store.anchor_rows[sample_index])
        candidate_end = int(store.candidate_end_rows[sample_index])
        candidate_values = store.log_base_fees[anchor_row + 1 : candidate_end]
        candidate_log_fees[row, : candidate_values.shape[0]] = candidate_values
        candidate_mask[row, : candidate_values.shape[0]] = True
    return _FlatPreparedRepresentation(
        flat_inputs=flat_inputs,
        candidate_log_fees=torch.from_numpy(candidate_log_fees),
        candidate_mask=torch.from_numpy(candidate_mask),
        batch_size=runtime_context.batch_size,
    )


class _FlatModelConfig(ModelConfig[Literal["test_flat"]]):
    id: Literal["test_flat"] = "test_flat"


class _FlatTuningSpaceModelConfig(ModelTuningSpaceConfig[Literal["test_flat"]]):
    id: Literal["test_flat"] = "test_flat"


class _FlatTunedModelParams(TunedModelParams[Literal["test_flat"]]):
    id: Literal["test_flat"] = "test_flat"


class _FlatTemporalModel(TemporalModel):
    def __init__(self, n_candidate_slots: int) -> None:
        super().__init__()
        self.n_candidate_slots = n_candidate_slots

    def forward(self, flat_inputs: torch.Tensor) -> ModelOutputs:
        base = flat_inputs[:, 0]
        logits = torch.stack(
            (
                base,
                -base,
                torch.zeros_like(base),
            ),
            dim=1,
        )
        return ModelOutputs(logits=logits[:, : self.n_candidate_slots])


def _register_flat_test_family() -> None:
    try:
        input_representation_spec("test_flat_problem")
    except ValueError:
        register_input_representation(
            InputRepresentationSpec(
                id="test_flat_problem",
                prepare=_prepare_flat_problem,
            )
        )

    try:
        model_spec("test_flat")
    except ValueError:
        register_model_spec(
            ModelSpec(
                id="test_flat",
                input_representation="test_flat_problem",
                family_execution_id="flat_projection",
                model_config_type=_FlatModelConfig,
                tuning_space_type=_FlatTuningSpaceModelConfig,
                tuned_params_type=_FlatTunedModelParams,
                build_model=lambda n_features, n_candidate_slots, config: _FlatTemporalModel(
                    n_candidate_slots
                ),
                default_precision=lambda device: TrainingPrecision.FP32,
                auto_compile=lambda device, precision: False,
                validate_tuning_space=lambda model_config, tuning_space: None,
                sample_model_params=lambda trial, tuning_space: None,
                apply_model_params=lambda model_config, params: model_config,
            )
        )


def _test_training_config(batch_size: int) -> TrainingConfig:
    return TrainingConfig(
        learning_rate=1e-3,
        weight_decay=0.0,
        batch_size=batch_size,
        max_epochs=1,
        early_stopping=EarlyStoppingConfig(patience=1, min_delta=0.0),
        gradient_clip_norm=1.0,
        device="cpu",
        seed=2026,
        deterministic=True,
        log_every_n_steps=1,
        precision=TrainingPrecision.FP32,
        compile=CompileMode.OFF,
    )


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


def test_generic_evaluation_pipeline_accepts_non_sequence_event_batches() -> None:
    _register_flat_test_family()
    store = _test_store()
    sample_indices = np.array([3, 0, 2, 1], dtype=np.int64)
    training_config = _test_training_config(batch_size=2)
    model = _FlatTemporalModel(store.max_candidate_slots)
    runtime_context = build_representation_runtime_context(
        device=torch.device("cpu"),
        batch_size=training_config.batch_size,
    )
    loader = build_model_loader(
        store,
        sample_indices,
        model_id="test_flat",
        runtime_context=runtime_context,
        seed=training_config.seed,
    )

    first_batch = next(iter(loader))
    assert not isinstance(first_batch, SequenceEventBatch)

    actual = evaluate_model(
        model,
        model_id="test_flat",
        store=store,
        sample_indices=sample_indices,
        training_config=training_config,
    )

    assert actual.objective_loss > 0.0
    assert 0.0 <= actual.exact_optimum_hit_rate <= 1.0
    assert np.isfinite(actual.cost_over_optimum)
    assert np.isfinite(actual.profit_over_baseline)
