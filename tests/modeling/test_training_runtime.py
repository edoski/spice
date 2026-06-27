from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import torch

from spice.config.models import TrainingConfig
from spice.modeling.batch_plan import BatchRuntimeContext
from spice.modeling.dataset_builders import PreparedTrainingSampleSelection
from spice.modeling.runtime_planning import ModelingRuntimePlan
from spice.modeling.training_runtime import plan_training_runtime, prepare_training_runtime
from spice.temporal.execution_policy import PreparedActionSpace


def _training_config() -> TrainingConfig:
    return TrainingConfig.model_validate(
        {
            "learning_rate": 0.02,
            "weight_decay": 0.03,
            "batch_size": 1,
            "max_epochs": 2,
            "early_stopping": {"patience": 2, "min_delta": 0.01},
            "gradient_clip_norm": 1.0,
            "seed": 7,
            "deterministic": True,
            "log_every_n_steps": 1,
            "sequence": {"min_length": 4, "max_length": 64},
        }
    )


def _runtime_plan() -> ModelingRuntimePlan:
    return ModelingRuntimePlan(
        resolved_device=torch.device("cpu"),
        precision="32-true",
        batch_runtime_context=BatchRuntimeContext(batch_size=1),
        deterministic=True,
        seed=7,
    )


def _sample_role(indices: list[int]) -> PreparedTrainingSampleSelection:
    sample_indices = np.array(indices, dtype=np.int64)
    action_space = PreparedActionSpace(
        sample_indices=sample_indices,
        max_candidate_slots=1,
        action_mask=np.ones((sample_indices.shape[0], 1), dtype=np.bool_),
    )
    return PreparedTrainingSampleSelection(
        temporal_facts=cast(Any, SimpleNamespace(action_space=action_space))
    )


def test_plan_training_runtime_builds_streaming_train_and_validation_plans(
    monkeypatch,
) -> None:
    calls = []
    prediction_state = object()
    train_samples = _sample_role([0, 1])
    validation_samples = _sample_role([2])

    def fake_build_prediction_batch_plan(
        *_args, temporal_facts, runtime_plan, shuffle, **_kwargs
    ):
        calls.append(
            {
                "runtime_plan": runtime_plan,
                "shuffle": shuffle,
                "temporal_facts": temporal_facts,
            }
        )
        return SimpleNamespace(source=[SimpleNamespace()])

    prediction_contract = SimpleNamespace(
        fit_training_state=lambda *args, **kwargs: (
            prediction_state if kwargs["temporal_facts"] is train_samples.temporal_facts else None
        )
    )
    monkeypatch.setattr(
        "spice.modeling.training_runtime.build_prediction_batch_plan",
        fake_build_prediction_batch_plan,
    )

    plan = plan_training_runtime(
        cast(Any, torch.nn.Linear(1, 1)),
        prediction_contract=cast(Any, prediction_contract),
        execution_policy=cast(Any, SimpleNamespace()),
        store=cast(Any, SimpleNamespace()),
        train_samples=train_samples,
        validation_samples=validation_samples,
        runtime_plan=_runtime_plan(),
    )

    assert plan.prediction_training_state is prediction_state
    assert plan.runtime_plan == _runtime_plan()
    assert calls == [
        {
            "runtime_plan": _runtime_plan(),
            "shuffle": True,
            "temporal_facts": train_samples.temporal_facts,
        },
        {
            "runtime_plan": _runtime_plan(),
            "shuffle": False,
            "temporal_facts": validation_samples.temporal_facts,
        },
    ]


def test_prepare_training_runtime_builds_cuda_runtime_and_moves_model(monkeypatch) -> None:
    model = torch.nn.Linear(1, 1)
    runtime_plan = _runtime_plan()
    moved_models: list[torch.nn.Module] = []

    monkeypatch.setattr(
        "spice.modeling.training_runtime.build_training_modeling_runtime_plan",
        lambda *, training_config: runtime_plan,
    )
    monkeypatch.setattr(
        "spice.modeling.training_runtime.prepare_model_for_runtime",
        lambda model, plan: moved_models.append(model) or model,
    )
    monkeypatch.setattr(
        "spice.modeling.training_runtime.modeling_backend_scope",
        lambda _plan: _NullContext(),
    )
    monkeypatch.setattr(
        "spice.modeling.training_runtime.plan_training_runtime",
        lambda model, **kwargs: SimpleNamespace(
            runtime_plan=kwargs["runtime_plan"],
            train_batch_plan=object(),
            validation_batch_plan=object(),
            prediction_training_state=None,
        ),
    )

    prepared = prepare_training_runtime(
        cast(Any, model),
        prediction_contract=cast(Any, SimpleNamespace()),
        execution_policy=cast(Any, SimpleNamespace()),
        store=cast(Any, SimpleNamespace()),
        train_samples=_sample_role([0]),
        validation_samples=_sample_role([1]),
        training_config=_training_config(),
    )

    assert prepared.fit_model is model
    assert prepared.batch_plan.runtime_plan is runtime_plan
    assert moved_models == [model]


class _NullContext:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *_args) -> None:
        return None
