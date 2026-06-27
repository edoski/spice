from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest
import torch

from spice.modeling.batch_plan import BatchRuntimeContext
from spice.modeling.forward_runtime import (
    run_planned_model_input_forward,
    run_planned_prediction_forward,
)
from spice.modeling.runtime_planning import ModelingRuntimePlan
from spice.temporal.execution_policy import PreparedActionSpace


def _runtime_plan() -> ModelingRuntimePlan:
    return ModelingRuntimePlan(
        resolved_device=torch.device("cpu"),
        precision="32-true",
        batch_runtime_context=BatchRuntimeContext(batch_size=2),
        deterministic=None,
        seed=3,
    )


def test_planned_forward_rejects_empty_sample_indices() -> None:
    empty_action_space = PreparedActionSpace(
        sample_indices=np.array([], dtype=np.int64),
        max_candidate_slots=1,
        action_mask=np.zeros((0, 1), dtype=np.bool_),
    )
    with pytest.raises(ValueError, match="sample_indices must be non-empty"):
        run_planned_model_input_forward(
            object(),
            store=object(),
            action_space=empty_action_space,
            runtime_plan=_runtime_plan(),
            on_outputs=lambda _batch, _outputs: None,
        )

    with pytest.raises(ValueError, match="sample_indices must be non-empty"):
        run_planned_prediction_forward(
            object(),
            store=object(),
            temporal_facts=SimpleNamespace(action_space=empty_action_space),
            prediction_contract=object(),
            runtime_plan=_runtime_plan(),
            on_outputs=lambda _batch, _outputs: None,
        )


class _ProbeBatch:
    def __init__(self, label: str) -> None:
        self.label = label

    def to_device(self, _device: torch.device):
        return self

    def model_kwargs(self) -> dict[str, torch.Tensor]:
        return {"x": torch.tensor([1.0])}


class _ProbeModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.grad_enabled: list[bool] = []

    def forward(self, **_kwargs):
        self.grad_enabled.append(torch.is_grad_enabled())
        return SimpleNamespace()


def test_model_input_forward_builds_one_streaming_plan(
    monkeypatch,
) -> None:
    model = _ProbeModel()
    action_space = PreparedActionSpace(
        sample_indices=np.array([0], dtype=np.int64),
        max_candidate_slots=1,
        action_mask=np.ones((1, 1), dtype=np.bool_),
    )
    plan_calls: list[dict[str, object]] = []
    final_calls: list[dict[str, object]] = []

    def fake_build_model_input_batch_plan(
        _store,
        *,
        action_space: object,
        runtime_plan: ModelingRuntimePlan,
        **_kwargs,
    ):
        plan_calls.append(
            {
                "action_space": action_space,
                "host_loader_policy": runtime_plan.batch_runtime_context.host_loader_policy,
                "resolved_device": runtime_plan.resolved_device,
                "seed": runtime_plan.seed,
            }
        )
        return SimpleNamespace(source=[_ProbeBatch(f"batch-{len(plan_calls)}")])

    def fake_run_model_forward_pass(_model, *, loader, runtime_plan, on_outputs):
        final_calls.append(
            {
                "loader": [batch.label for batch in loader],
                "resolved_device": runtime_plan.resolved_device,
                "precision": runtime_plan.precision,
            }
        )
        on_outputs(_ProbeBatch("final"), SimpleNamespace())

    monkeypatch.setattr(
        "spice.modeling.forward_runtime.build_model_input_batch_plan",
        fake_build_model_input_batch_plan,
    )
    monkeypatch.setattr(
        "spice.modeling.forward_runtime.run_model_forward_pass",
        fake_run_model_forward_pass,
    )
    outputs: list[str] = []

    run_planned_model_input_forward(
        cast(Any, model),
        store=object(),
        action_space=action_space,
        runtime_plan=_runtime_plan(),
        on_outputs=lambda batch, _outputs: outputs.append(batch.label),
    )

    assert plan_calls[0]["action_space"] is action_space
    assert plan_calls[0]["host_loader_policy"] == "automatic"
    assert final_calls == [
        {
            "loader": ["batch-1"],
            "resolved_device": torch.device("cpu"),
            "precision": "32-true",
        },
    ]
    assert outputs == ["final"]


def test_prediction_forward_reuses_temporal_facts_and_keeps_unshuffled_plans(
    monkeypatch,
) -> None:
    temporal_facts = SimpleNamespace(
        action_space=PreparedActionSpace(
            sample_indices=np.array([2, 3], dtype=np.int64),
            max_candidate_slots=1,
            action_mask=np.ones((2, 1), dtype=np.bool_),
        )
    )
    plan_calls: list[dict[str, object]] = []

    def fake_build_prediction_batch_plan(
        _store,
        *,
        temporal_facts: object,
        runtime_plan: ModelingRuntimePlan,
        shuffle: bool,
        **_kwargs,
    ):
        plan_calls.append(
            {
                "temporal_facts": temporal_facts,
                "seed": runtime_plan.seed,
                "shuffle": shuffle,
            }
        )
        return SimpleNamespace(source=[_ProbeBatch(f"prediction-{len(plan_calls)}")])

    monkeypatch.setattr(
        "spice.modeling.forward_runtime.build_prediction_batch_plan",
        fake_build_prediction_batch_plan,
    )
    monkeypatch.setattr(
        "spice.modeling.forward_runtime.run_model_forward_pass",
        lambda *_args, **_kwargs: None,
    )

    run_planned_prediction_forward(
        cast(Any, _ProbeModel()),
        store=object(),
        temporal_facts=temporal_facts,
        prediction_contract=object(),
        runtime_plan=_runtime_plan(),
        on_outputs=lambda _batch, _outputs: None,
    )

    assert plan_calls == [
        {
            "temporal_facts": temporal_facts,
            "seed": 3,
            "shuffle": False,
        }
    ]
