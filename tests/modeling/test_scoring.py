from __future__ import annotations

from contextlib import nullcontext
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import torch

from spice.evaluation import EvaluationRun, EvaluationSummary
from spice.metrics import MetricSet
from spice.modeling.batch_plan import BatchRuntimeContext
from spice.modeling.runtime_planning import ModelingRuntimePlan
from spice.modeling.scoring import (
    EvaluationScoringRuntimePlan,
    PredictionMetricScoringRuntimePlan,
    score_evaluation,
    score_prediction_metrics,
)
from spice.temporal.execution_policy import PreparedActionSpace


def test_score_evaluation_validates_predicts_and_runs_evaluator(monkeypatch) -> None:
    decoded = SimpleNamespace(decoded_result_id="ranked_actions")
    summary = EvaluationSummary(
        metrics=MetricSet(values={"profit": 1.0}),
        window_metrics={},
        total_events=1,
        runs=[EvaluationRun(n_events=1, metrics={"profit": 1.0}, metadata={})],
    )
    calls: list[str] = []
    runtime_plan = ModelingRuntimePlan(
        resolved_device=torch.device("cpu"),
        precision="32-true",
        batch_runtime_context=BatchRuntimeContext(batch_size=8),
        deterministic=None,
        seed=0,
    )

    def fake_predict_decoded_result(*_args, **kwargs):
        calls.append(
            f"predict:{kwargs['runtime_plan'].batch_runtime_context.batch_size}:"
            f"{kwargs['execution_policy'].name}"
        )
        return decoded

    class FakeEvaluator:
        def validate_prediction_contract(self, prediction_contract) -> None:
            calls.append(f"validate:{prediction_contract.decoded_result_id}")

        def run(self, store, execution_policy, decoded_result, *, action_space):
            del store, execution_policy
            calls.append(
                "run:"
                f"{decoded_result.decoded_result_id}:"
                f"{action_space.sample_indices.tolist()}"
            )
            return summary

    monkeypatch.setattr(
        "spice.modeling.scoring.predict_decoded_result",
        fake_predict_decoded_result,
    )

    result = score_evaluation(
        scoring_plan=EvaluationScoringRuntimePlan(
            model=cast(Any, SimpleNamespace()),
            prediction_contract=cast(Any, SimpleNamespace(decoded_result_id="ranked_actions")),
            execution_policy=cast(Any, SimpleNamespace(name="policy")),
            store=cast(Any, SimpleNamespace()),
            action_space=PreparedActionSpace(
                sample_indices=np.array([2, 4], dtype=np.int64),
                max_candidate_slots=1,
                action_mask=np.ones((2, 1), dtype=np.bool_),
            ),
            runtime_plan=runtime_plan,
        ),
        evaluator_contract=cast(Any, FakeEvaluator()),
    )

    assert result is summary
    assert calls == [
        "validate:ranked_actions",
        "predict:8:policy",
        "run:ranked_actions:[2, 4]",
    ]


def test_score_prediction_metrics_uses_runtime_plan_and_prediction_training_state(
    monkeypatch,
) -> None:
    runtime_plan = ModelingRuntimePlan(
        resolved_device=torch.device("cpu"),
        precision="32-true",
        batch_runtime_context=BatchRuntimeContext(batch_size=1),
        deterministic=True,
        seed=1,
    )
    monkeypatch.setattr(
        "spice.modeling.scoring.modeling_backend_scope",
        lambda _plan: nullcontext(),
    )

    seen_training_states: list[object | None] = []

    class Accumulator:
        def __init__(self) -> None:
            self.values: list[float] = []

        def update(self, batch_state) -> None:
            self.values.append(batch_state["score"])

        def finalize(self) -> MetricSet:
            return MetricSet({"score": sum(self.values)})

    prediction_state = object()
    prediction_contract = SimpleNamespace(
        create_epoch_accumulator=Accumulator,
        compute_batch_loss_and_state=lambda outputs, targets, training_state: (
            seen_training_states.append(training_state) or torch.tensor(0.0),
            {"score": 2.5},
        ),
    )
    action_space = PreparedActionSpace(
        sample_indices=np.array([0], dtype=np.int64),
        max_candidate_slots=1,
        action_mask=np.ones((1, 1), dtype=np.bool_),
    )
    temporal_facts = cast(Any, SimpleNamespace(action_space=action_space))
    forward_calls = []

    def fake_run_planned_prediction_forward(_model, *, on_outputs, **kwargs):
        forward_calls.append(kwargs)
        on_outputs(SimpleNamespace(targets="metrics"), outputs=SimpleNamespace())

    monkeypatch.setattr(
        "spice.modeling.scoring.run_planned_prediction_forward",
        fake_run_planned_prediction_forward,
    )

    metrics = score_prediction_metrics(
        PredictionMetricScoringRuntimePlan(
            model=cast(Any, torch.nn.Linear(1, 1)),
            prediction_contract=cast(Any, prediction_contract),
            execution_policy=cast(Any, SimpleNamespace()),
            store=cast(Any, SimpleNamespace()),
            temporal_facts=temporal_facts,
            prediction_training_state=prediction_state,
            runtime_plan=runtime_plan,
        )
    )

    assert forward_calls[0]["runtime_plan"] is runtime_plan
    assert seen_training_states == [prediction_state]
    assert metrics.require("score") == 2.5
