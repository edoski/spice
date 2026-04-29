from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from spice.evaluation import EvaluationSummary
from spice.modeling.objective_metrics import (
    ObjectiveMetricEvaluationContext,
    compile_objective_metric_source,
)
from spice.objectives import CompiledObjectiveContract
from spice.prediction import MetricSet


def _objective_contract(
    *,
    objective_id: str,
    benchmark_id: str | None,
) -> CompiledObjectiveContract:
    return CompiledObjectiveContract(
        objective_id=objective_id,
        metric_id="score",
        direction="maximize",
        benchmark_id=benchmark_id,
        config_payload={},
    )


def test_validation_objective_metric_source_returns_validation_metrics_unchanged() -> None:
    metrics = MetricSet({"score": 1.0})
    source = compile_objective_metric_source(
        _objective_contract(objective_id="validation", benchmark_id=None),
        evaluation=None,
    )

    result = source.evaluate_metrics(
        metrics,
        context=SimpleNamespace(),
    )

    assert result is metrics


def test_evaluation_objective_metric_source_scores_with_same_runtime_facts(
    monkeypatch,
) -> None:
    evaluator_contract = SimpleNamespace(evaluation_id="poisson_replay_2h")
    evaluation = SimpleNamespace(id="poisson_replay_2h")
    summary = EvaluationSummary(
        metrics=MetricSet({"score": 2.0}),
        window_metrics={},
        total_events=1,
        runs=[],
    )
    seen_contexts = []
    monkeypatch.setattr(
        "spice.modeling.objective_metrics.compile_evaluator_contract",
        lambda config: evaluator_contract,
    )

    def fake_score_evaluation(context):
        seen_contexts.append(context)
        return summary

    monkeypatch.setattr(
        "spice.modeling.objective_metrics.score_evaluation",
        fake_score_evaluation,
    )
    source = compile_objective_metric_source(
        _objective_contract(
            objective_id="evaluation",
            benchmark_id="poisson_replay_2h",
        ),
        evaluation=evaluation,
    )
    runtime_context = ObjectiveMetricEvaluationContext(
        model=SimpleNamespace(name="model"),
        model_config=SimpleNamespace(name="model_config"),
        prediction_contract=SimpleNamespace(name="prediction"),
        representation_contract=SimpleNamespace(name="representation"),
        execution_policy=SimpleNamespace(name="execution"),
        store=SimpleNamespace(name="store"),
        sample_indices=np.array([2, 4], dtype=np.int64),
        batch_size=8,
    )

    result = source.evaluate_metrics(
        MetricSet({"score": 1.0}),
        context=runtime_context,
    )

    assert result == summary.metrics
    assert len(seen_contexts) == 1
    scoring_context = seen_contexts[0]
    assert scoring_context.model is runtime_context.model
    assert scoring_context.model_config is runtime_context.model_config
    assert scoring_context.prediction_contract is runtime_context.prediction_contract
    assert scoring_context.representation_contract is runtime_context.representation_contract
    assert scoring_context.evaluator_contract is evaluator_contract
    assert scoring_context.execution_policy is runtime_context.execution_policy
    assert scoring_context.store is runtime_context.store
    assert scoring_context.sample_indices is runtime_context.sample_indices
    assert scoring_context.batch_size == 8
