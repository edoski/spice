from __future__ import annotations

from contextlib import nullcontext
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest
import torch

from spice.config.models import TrainingConfig
from spice.metrics import MetricSet
from spice.modeling.batch_plan import BatchRuntimeContext, DeviceStorageBudget
from spice.modeling.objective_runtime import CompiledObjectiveRuntime
from spice.modeling.runtime_planning import ModelingRuntimePlan
from spice.modeling.scoring import EvaluationScoringRuntimePlan
from spice.modeling.training_runner import (
    TrainingCallbacks,
    TrainingCheckpoint,
    TrainingFitSpec,
    run_training_fit,
)
from spice.modeling.training_runtime import PreparedTrainingRuntime, TrainingRuntimePlan
from spice.objectives import CompiledObjectiveContract
from spice.temporal.execution_policy import PreparedActionSpace


class _TinyModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.weight = torch.nn.Parameter(torch.tensor(0.0))


class _FakeOptimizer:
    def __init__(self) -> None:
        self.loaded_state: dict[str, object] | None = None

    def state_dict(self) -> dict[str, object]:
        return {"loaded": self.loaded_state is not None}

    def load_state_dict(self, state: dict[str, object]) -> None:
        self.loaded_state = state


def _training_config(*, max_epochs: int = 2, patience: int = 2) -> TrainingConfig:
    return TrainingConfig.model_validate(
        {
            "learning_rate": 0.01,
            "weight_decay": 0.0,
            "batch_size": 1,
            "max_epochs": max_epochs,
            "early_stopping": {"patience": patience, "min_delta": 0.01},
            "gradient_clip_norm": 1.0,
            "seed": 1,
            "deterministic": True,
            "log_every_n_steps": 1,
        }
    )


def _objective_contract() -> CompiledObjectiveContract:
    return CompiledObjectiveContract(
        objective_id="validation",
        metric_id="score",
        direction="maximize",
        evaluator_id=None,
    )


def _objective_runtime(evaluate_metrics_fn=None) -> CompiledObjectiveRuntime:
    return CompiledObjectiveRuntime(
        contract=_objective_contract(),
        evaluate_metrics_fn=evaluate_metrics_fn
        or (lambda validation_metrics, context: validation_metrics),
    )


def _patch_training_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_context = BatchRuntimeContext(
        batch_size=1,
        available_host_memory_bytes=1024,
        device_storage_budget=DeviceStorageBudget.disabled(),
    )
    runtime_plan = ModelingRuntimePlan(
        resolved_device=torch.device("cpu"),
        precision="32-true",
        batch_runtime_context=runtime_context,
        deterministic=None,
        seed=0,
    )

    def fake_prepare_training_runtime(model, **_kwargs):
        return PreparedTrainingRuntime(
            fit_model=model,
            optimizer=cast(torch.optim.Optimizer, _FakeOptimizer()),
            batch_plan=TrainingRuntimePlan(
                runtime_plan=runtime_plan,
                train_batch_plan=cast(Any, SimpleNamespace(source=[0])),
                validation_batch_plan=cast(Any, SimpleNamespace(source=[0])),
                prediction_training_state=None,
            ),
        )

    monkeypatch.setattr(
        "spice.modeling.training_runner.prepare_training_runtime",
        fake_prepare_training_runtime,
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.modeling_backend_scope",
        lambda _plan: nullcontext(),
    )


def _sample_role(indices: list[int]):
    sample_indices = np.array(indices, dtype=np.int64)
    action_space = PreparedActionSpace(
        sample_indices=sample_indices,
        max_candidate_slots=1,
        action_mask=np.ones((sample_indices.shape[0], 1), dtype=np.bool_),
    )
    return SimpleNamespace(
        sample_indices=sample_indices,
        action_space=action_space,
        temporal_facts=SimpleNamespace(action_space=action_space),
    )


def _prepared(*, train: list[int] | None = None, validation: list[int] | None = None):
    return SimpleNamespace(
        execution_policy=SimpleNamespace(),
        store=SimpleNamespace(),
        samples=SimpleNamespace(
            train=_sample_role([0] if train is None else train),
            validation=_sample_role([1] if validation is None else validation),
            test=_sample_role([2]),
        ),
    )


def _fit_spec(
    tmp_path,
    *,
    model,
    training_config,
    objective_runtime=None,
) -> TrainingFitSpec:
    return TrainingFitSpec(
        model=model,
        prediction_contract=cast(Any, SimpleNamespace(fit_training_state=lambda *_, **__: None)),
        representation_contract=cast(Any, SimpleNamespace()),
        objective_runtime=objective_runtime or _objective_runtime(),
        prepared=cast(Any, _prepared(train=[0], validation=[0])),
        training_config=training_config,
    )


def test_training_fit_restores_best_state_and_calls_early_stop_callback(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    epoch_state = {"epoch": 0}
    early_stop_calls: list[tuple[int, int]] = []
    objective_values = [1.0, 1.005]

    def fake_run_epoch(model, *, training, **_kwargs):
        if training:
            epoch_state["epoch"] += 1
            model.weight.data.fill_(float(epoch_state["epoch"]))
        return MetricSet({"score": objective_values[epoch_state["epoch"] - 1]})

    _patch_training_runtime(monkeypatch)
    monkeypatch.setattr("spice.modeling.training_runner.run_epoch", fake_run_epoch)

    model = _TinyModel()
    result = run_training_fit(
        _fit_spec(
            tmp_path,
            model=cast(Any, model),
            training_config=_training_config(max_epochs=2, patience=1),
        ),
        callbacks=TrainingCallbacks(
            on_early_stop=lambda epoch, best_epoch: early_stop_calls.append((epoch, best_epoch)),
        ),
    )

    assert result.best_epoch == 1
    assert result.best_objective_value == 1.0
    assert len(result.train_history) == 2
    assert len(result.validation_history) == 2
    assert len(result.objective_history) == 2
    assert model.weight.item() == 1.0
    assert result.runtime_plan.seed == 0
    assert early_stop_calls == [(2, 1)]


def test_training_fit_resumes_from_checkpoint(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    epoch_state = {"epoch": 1}
    checkpoints: list[TrainingCheckpoint] = []

    def fake_run_epoch(model, *, training, **_kwargs):
        if training:
            epoch_state["epoch"] += 1
            model.weight.data.fill_(float(epoch_state["epoch"]))
        return MetricSet({"score": float(epoch_state["epoch"])})

    _patch_training_runtime(monkeypatch)
    monkeypatch.setattr("spice.modeling.training_runner.run_epoch", fake_run_epoch)

    model = _TinyModel()
    checkpoint = TrainingCheckpoint(
        completed_epoch=1,
        model_state={"weight": torch.tensor(1.0)},
        optimizer_state={"epoch": 1},
        policy_state={
            "train_history": [{"score": 1.0}],
            "validation_history": [{"score": 1.0}],
            "objective_history": [{"score": 1.0}],
            "best_state": {"weight": torch.tensor(1.0)},
            "best_epoch": 1,
            "epochs_without_improvement": 0,
        },
    )

    spec = _fit_spec(
        tmp_path,
        model=model,
        training_config=_training_config(max_epochs=2, patience=2),
    )
    spec.checkpoint = checkpoint
    result = run_training_fit(
        spec,
        callbacks=TrainingCallbacks(on_checkpoint=checkpoints.append),
    )

    assert result.best_epoch == 2
    assert len(result.train_history) == 2
    assert model.weight.item() == 2.0
    assert [saved.completed_epoch for saved in checkpoints] == [2]


def test_training_fit_delegates_scoring_plan_to_objective_runtime(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen_scoring_plans: list[EvaluationScoringRuntimePlan | None] = []

    def fake_run_epoch(_model, *, training, **_kwargs):
        return MetricSet({"score": 1.0 if training else 2.0})

    def evaluate_metrics(validation_metrics, scoring_plan):
        assert validation_metrics == MetricSet({"score": 2.0})
        seen_scoring_plans.append(scoring_plan)
        return MetricSet({"score": 3.0})

    _patch_training_runtime(monkeypatch)
    monkeypatch.setattr("spice.modeling.training_runner.run_epoch", fake_run_epoch)
    model = _TinyModel()
    prediction_contract = cast(Any, SimpleNamespace(fit_training_state=lambda *_, **__: None))
    representation_contract = cast(Any, SimpleNamespace())
    prepared = _prepared(train=[0], validation=[1])

    result = run_training_fit(
        TrainingFitSpec(
            model=cast(Any, model),
            prediction_contract=prediction_contract,
            representation_contract=representation_contract,
            objective_runtime=_objective_runtime(evaluate_metrics),
            prepared=cast(Any, prepared),
            training_config=_training_config(max_epochs=1),
        )
    )

    assert result.best_objective_value == 3.0
    assert len(seen_scoring_plans) == 1
    scoring_plan = seen_scoring_plans[0]
    assert scoring_plan is not None
    assert scoring_plan.model is model
    assert scoring_plan.prediction_contract is prediction_contract
    assert scoring_plan.representation_contract is representation_contract
    assert scoring_plan.execution_policy is prepared.execution_policy
    assert scoring_plan.store is prepared.store
    assert scoring_plan.runtime_plan is not None
    np.testing.assert_array_equal(
        scoring_plan.action_space.sample_indices,
        np.array([1], dtype=np.int64),
    )
