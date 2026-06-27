from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pytest
import torch

from spice.modeling.batch_plan import (
    BatchRuntimeContext,
    build_model_input_batch_plan,
    build_prediction_batch_plan,
)
from spice.modeling.runtime_planning import ModelingRuntimePlan
from spice.temporal import (
    PreparedActionSpace,
    PreparedTemporalFacts,
    PreparedTemporalOutcomeFacts,
)
from spice.temporal.problem_store import CompiledProblemStore


def _store() -> CompiledProblemStore:
    return CompiledProblemStore(
        feature_matrix=np.arange(10, dtype=np.float32).reshape(5, 2),
        log_base_fees=np.zeros(5, dtype=np.float32),
        timestamps=np.arange(5, dtype=np.int64),
        anchor_rows=np.array([1, 1, 3, 3], dtype=np.int64),
        context_start_rows=np.array([0, 1, 2, 3], dtype=np.int64),
        candidate_start_rows=np.array([1, 1, 3, 3], dtype=np.int64),
        candidate_end_rows=np.array([2, 2, 4, 4], dtype=np.int64),
        max_candidate_slots=3,
    )


def _action_space(sample_indices: np.ndarray) -> PreparedActionSpace:
    return PreparedActionSpace(
        sample_indices=sample_indices,
        max_candidate_slots=3,
        action_mask=np.ones((sample_indices.shape[0], 3), dtype=np.bool_),
    )


def _temporal_facts(sample_indices: np.ndarray) -> PreparedTemporalFacts:
    action_space = _action_space(sample_indices)
    sample_count = int(sample_indices.shape[0])
    return PreparedTemporalFacts(
        action_space=action_space,
        outcome_facts=PreparedTemporalOutcomeFacts(
            action_outcome_rows=np.zeros((sample_count, 3), dtype=np.int64),
            action_outcome_log_fees=np.zeros((sample_count, 3), dtype=np.float32),
            reachable_action_mask=np.ones((sample_count, 3), dtype=np.bool_),
            baseline_rows=np.zeros(sample_count, dtype=np.int64),
            overflow_mask=np.zeros((sample_count, 3), dtype=np.bool_),
        ),
    )


@dataclass(slots=True)
class _TargetBatch:
    sample_positions: torch.Tensor

    def to_device(self, _device: torch.device) -> _TargetBatch:
        return self

    def pin_memory(self) -> _TargetBatch:
        return self


class _Targets:
    def __init__(self) -> None:
        self.positions: list[list[int]] = []

    def build_batch(self, sample_positions: torch.Tensor) -> _TargetBatch:
        self.positions.append(sample_positions.tolist())
        return _TargetBatch(sample_positions=sample_positions + 10)


class _PredictionContract:
    def __init__(self, targets: _Targets) -> None:
        self.targets = targets
        self.temporal_facts: PreparedTemporalFacts | None = None

    def prepare_targets(self, *_args, **kwargs) -> _Targets:
        self.temporal_facts = kwargs["temporal_facts"]
        return self.targets


def _runtime_plan(
    *,
    resolved_device: torch.device | None = None,
    host_loader_policy: Literal["automatic", "single_process_unpinned"] = "automatic",
    seed: int = 2026,
) -> ModelingRuntimePlan:
    return ModelingRuntimePlan(
        resolved_device=resolved_device or torch.device("cpu"),
        precision="32-true",
        batch_runtime_context=BatchRuntimeContext(
            batch_size=2,
            host_loader_policy=host_loader_policy,
        ),
        deterministic=None,
        seed=seed,
    )


def test_host_loader_worker_override_rejects_invalid_values(monkeypatch) -> None:
    monkeypatch.setenv("SPICE_DATALOADER_WORKERS", "-1")

    with pytest.raises(ValueError, match="must be non-negative"):
        build_model_input_batch_plan(
            _store(),
            action_space=_action_space(np.arange(4, dtype=np.int64)),
            runtime_plan=_runtime_plan(),
        )


def test_single_process_unpinned_loader_policy_disables_workers_and_pin_memory(
    monkeypatch,
) -> None:
    captured_kwargs = []

    class FakeDataLoader:
        @classmethod
        def __class_getitem__(cls, _item):
            return cls

        def __init__(self, _dataset, **kwargs) -> None:
            captured_kwargs.append(kwargs)
            self._batch_sampler = kwargs["batch_sampler"]
            self._collate_fn = kwargs["collate_fn"]

        def __iter__(self):
            for sample_positions in self._batch_sampler:
                yield self._collate_fn(sample_positions)

        def __len__(self) -> int:
            return len(self._batch_sampler)

    monkeypatch.setenv("SPICE_DATALOADER_WORKERS", "8")
    monkeypatch.setattr("spice.modeling.batch_plan.DataLoader", FakeDataLoader)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)

    plan = build_model_input_batch_plan(
        _store(),
        action_space=_action_space(np.arange(4, dtype=np.int64)),
        runtime_plan=_runtime_plan(
            resolved_device=torch.device("cuda"),
            host_loader_policy="single_process_unpinned",
        ),
    )

    assert next(iter(plan.source)).sample_positions.tolist() == [1, 3]
    assert captured_kwargs == [
        {
            "batch_sampler": captured_kwargs[0]["batch_sampler"],
            "collate_fn": captured_kwargs[0]["collate_fn"],
            "num_workers": 0,
            "persistent_workers": False,
            "prefetch_factor": None,
            "pin_memory": False,
        }
    ]


def test_batch_plan_orders_samples_deterministically_by_context_length() -> None:
    plan = build_model_input_batch_plan(
        _store(),
        action_space=_action_space(np.arange(4, dtype=np.int64)),
        runtime_plan=_runtime_plan(),
    )

    assert plan.sample_count == 4
    assert plan.batch_count == 2
    assert [batch.sample_positions.tolist() for batch in plan.source] == [[1, 3], [0, 2]]


def test_shuffled_batch_plan_changes_by_epoch_but_keeps_batch_shape() -> None:
    plan = build_prediction_batch_plan(
        _store(),
        temporal_facts=_temporal_facts(np.arange(4, dtype=np.int64)),
        prediction_contract=_PredictionContract(_Targets()),
        runtime_plan=_runtime_plan(),
        shuffle=True,
    )

    first_epoch = [batch.inputs.sample_positions.tolist() for batch in plan.source]
    second_epoch = [batch.inputs.sample_positions.tolist() for batch in plan.source]

    assert first_epoch != second_epoch
    assert [len(batch) for batch in first_epoch] == [2, 2]
    assert [len(batch) for batch in second_epoch] == [2, 2]
    assert sorted(position for batch in first_epoch for position in batch) == [0, 1, 2, 3]
    assert sorted(position for batch in second_epoch for position in batch) == [0, 1, 2, 3]


def test_prediction_batch_plan_binds_targets_to_input_sample_positions() -> None:
    targets = _Targets()
    prediction_contract = _PredictionContract(targets)
    plan = build_prediction_batch_plan(
        _store(),
        temporal_facts=_temporal_facts(np.arange(4, dtype=np.int64)),
        prediction_contract=prediction_contract,
        runtime_plan=_runtime_plan(),
    )

    first_batch = next(iter(plan.source))

    assert first_batch.inputs.sample_positions.tolist() == [1, 3]
    assert first_batch.targets.sample_positions.tolist() == [11, 13]
    assert targets.positions == [[1, 3]]
    assert prediction_contract.temporal_facts is not None
