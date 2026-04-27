from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from spice.evaluation import EvaluationRun, EvaluationSummary
from spice.modeling.scoring import EvaluationScoringContext, score_evaluation
from spice.prediction import MetricSet


def test_score_evaluation_validates_predicts_and_runs_evaluator(monkeypatch) -> None:
    decoded = SimpleNamespace(decoded_result_id="offsets")
    summary = EvaluationSummary(
        metrics=MetricSet(values={"profit": 1.0}),
        window_metrics={},
        total_events=1,
        runs=[EvaluationRun(n_events=1, metrics={"profit": 1.0}, metadata={})],
    )
    calls: list[str] = []

    def fake_predict_with_model(*_args, **kwargs):
        calls.append(f"predict:{kwargs['batch_size']}")
        return decoded

    class FakeEvaluator:
        def validate_prediction_contract(self, prediction_contract) -> None:
            calls.append(f"validate:{prediction_contract.decoded_result_id}")

        def run(self, store, execution_policy, decoded_result, *, sample_indices):
            del store, execution_policy
            calls.append(f"run:{decoded_result.decoded_result_id}:{sample_indices.tolist()}")
            return summary

    monkeypatch.setattr("spice.modeling.scoring.predict_with_model", fake_predict_with_model)

    result = score_evaluation(
        EvaluationScoringContext(
            model=SimpleNamespace(),
            model_config=SimpleNamespace(),
            prediction_contract=SimpleNamespace(decoded_result_id="offsets"),
            representation_contract=SimpleNamespace(),
            evaluator_contract=FakeEvaluator(),
            execution_policy=SimpleNamespace(),
            store=SimpleNamespace(),
            sample_indices=np.array([2, 4], dtype=np.int64),
            batch_size=8,
        )
    )

    assert result is summary
    assert calls == ["validate:offsets", "predict:8", "run:offsets:[2, 4]"]
