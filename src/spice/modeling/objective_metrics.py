# pyright: strict

"""Model-bound objective metric production."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..core.errors import ConfigResolutionError
from ..evaluation import EvaluatorConfig, compile_evaluator_contract
from ..objectives import CompiledObjectiveContract
from ..prediction import CompiledPredictionContract, MetricSet
from ..temporal.execution_policy import CompiledExecutionPolicyContract
from ..temporal.problem_store import CompiledProblemStore, IntVector
from .families.base import ModelConfig
from .models import TemporalModel
from .representations import CompiledRepresentationContract
from .scoring import EvaluationScoringContext, score_evaluation


@dataclass(frozen=True, slots=True)
class ObjectiveMetricEvaluationContext:
    model: TemporalModel
    model_config: ModelConfig[Any]
    prediction_contract: CompiledPredictionContract
    representation_contract: CompiledRepresentationContract
    execution_policy: CompiledExecutionPolicyContract
    store: CompiledProblemStore
    sample_indices: IntVector
    batch_size: int


EvaluateObjectiveMetricsFn = Callable[
    [MetricSet, ObjectiveMetricEvaluationContext],
    MetricSet,
]


@dataclass(frozen=True, slots=True)
class CompiledObjectiveMetricSource:
    evaluate_metrics_fn: EvaluateObjectiveMetricsFn

    def evaluate_metrics(
        self,
        validation_metrics: MetricSet,
        *,
        context: ObjectiveMetricEvaluationContext,
    ) -> MetricSet:
        return self.evaluate_metrics_fn(validation_metrics, context)


def compile_objective_metric_source(
    objective_contract: CompiledObjectiveContract,
    *,
    evaluation: EvaluatorConfig | None,
) -> CompiledObjectiveMetricSource:
    if objective_contract.objective_id == "validation":
        return CompiledObjectiveMetricSource(
            evaluate_metrics_fn=lambda validation_metrics, context: validation_metrics,
        )
    if evaluation is None:
        raise ConfigResolutionError(
            f"objective benchmark {objective_contract.benchmark_id} requires evaluation"
        )
    if objective_contract.benchmark_id != evaluation.id:
        raise ConfigResolutionError(
            "objective benchmark "
            f"{objective_contract.benchmark_id} does not match evaluation {evaluation.id}"
        )
    evaluator_contract = compile_evaluator_contract(evaluation)

    def _evaluate(
        validation_metrics: MetricSet,
        context: ObjectiveMetricEvaluationContext,
    ) -> MetricSet:
        del validation_metrics
        return score_evaluation(
            EvaluationScoringContext(
                model=context.model,
                model_config=context.model_config,
                prediction_contract=context.prediction_contract,
                representation_contract=context.representation_contract,
                evaluator_contract=evaluator_contract,
                execution_policy=context.execution_policy,
                store=context.store,
                sample_indices=context.sample_indices,
                batch_size=context.batch_size,
            )
        ).metrics

    return CompiledObjectiveMetricSource(evaluate_metrics_fn=_evaluate)
