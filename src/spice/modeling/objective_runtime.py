# pyright: strict

"""Model-bound objective runtime production."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..core.errors import ConfigResolutionError
from ..evaluation import EvaluatorConfig, compile_evaluator_contract
from ..metrics import MetricDescriptor, MetricSet
from ..objectives import CompiledObjectiveContract, ObjectiveConfig, compile_objective_contract
from .scoring import ModelScoringInput, score_evaluation

ScoringInputFactory = Callable[[], ModelScoringInput]
EvaluateObjectiveMetricsFn = Callable[
    [MetricSet, ScoringInputFactory | None],
    MetricSet,
]


@dataclass(frozen=True, slots=True)
class CompiledObjectiveRuntime:
    contract: CompiledObjectiveContract
    evaluate_metrics_fn: EvaluateObjectiveMetricsFn

    def evaluate_metrics(
        self,
        validation_metrics: MetricSet,
        *,
        scoring_input_factory: ScoringInputFactory | None = None,
    ) -> MetricSet:
        return self.evaluate_metrics_fn(validation_metrics, scoring_input_factory)


def compile_objective_runtime(
    objective: ObjectiveConfig,
    *,
    evaluation: EvaluatorConfig | None,
    prediction_metric_descriptors: tuple[MetricDescriptor, ...],
) -> CompiledObjectiveRuntime:
    contract = compile_objective_contract(objective, evaluation=evaluation)
    if contract.objective_id == "validation":
        _require_metric_descriptor(
            contract.metric_id,
            prediction_metric_descriptors,
            owner="prediction",
        )
        return CompiledObjectiveRuntime(
            contract=contract,
            evaluate_metrics_fn=_validation_metrics,
        )
    if evaluation is None:
        raise ConfigResolutionError("evaluation objective runtime requires evaluation config")
    evaluator_contract = compile_evaluator_contract(evaluation)
    _require_metric_descriptor(
        contract.metric_id,
        evaluator_contract.metric_descriptors,
        owner="evaluator",
    )

    def _evaluate(
        validation_metrics: MetricSet,
        scoring_input_factory: ScoringInputFactory | None,
    ) -> MetricSet:
        del validation_metrics
        if scoring_input_factory is None:
            raise ValueError("evaluation objective runtime requires scoring input")
        return score_evaluation(
            model_input=scoring_input_factory(),
            evaluator_contract=evaluator_contract,
        ).metrics

    return CompiledObjectiveRuntime(contract=contract, evaluate_metrics_fn=_evaluate)


def _validation_metrics(
    validation_metrics: MetricSet,
    scoring_input_factory: ScoringInputFactory | None,
) -> MetricSet:
    del scoring_input_factory
    return validation_metrics


def _require_metric_descriptor(
    metric_id: str,
    descriptors: tuple[MetricDescriptor, ...],
    *,
    owner: str,
) -> None:
    if metric_id in {descriptor.id for descriptor in descriptors}:
        return
    known = ", ".join(sorted(descriptor.id for descriptor in descriptors))
    raise ConfigResolutionError(
        f"objective metric {metric_id} is not declared by {owner} metrics. Known metrics: {known}"
    )
