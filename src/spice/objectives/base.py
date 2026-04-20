"""Workflow-owned optimization objective seam."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import SerializeAsAny, field_validator

from ..core.closed_dispatch import (
    config_payload_and_id,
    unknown_id_error,
    validate_path_segment,
)
from ..core.reporting import Reporter
from ..evaluation import (
    EvaluatorConfig,
    coerce_evaluator_config,
    compile_evaluator_contract,
)
from ..modeling.families.base import ConfigModel
from ..prediction import MetricSet
from ..semantics import ObjectiveSemantics

if TYPE_CHECKING:
    from ..modeling._runtime import CompiledRepresentationContract
    from ..modeling.models import TemporalModel
    from ..prediction import CompiledPredictionContract
    from ..temporal.problem_store import CompiledProblemStore
    from ..temporal.realization import CompiledRealizationPolicyContract


class ObjectiveDirection(StrEnum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


class ObjectiveConfig(ConfigModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return validate_path_segment(value, label="objective.id")


class ValidationTrainingMetricObjectiveConfig(ObjectiveConfig):
    id: str = "validation_training_metric"
    metric_id: str
    direction: ObjectiveDirection

    @field_validator("metric_id")
    @classmethod
    def validate_metric_id(cls, value: str) -> str:
        return validate_path_segment(value, label="objective.metric_id")


class ValidationEvaluatorMetricObjectiveConfig(ObjectiveConfig):
    id: str = "validation_evaluator_metric"
    metric_id: str
    direction: ObjectiveDirection
    evaluator: SerializeAsAny[EvaluatorConfig]

    @field_validator("metric_id")
    @classmethod
    def validate_metric_id(cls, value: str) -> str:
        return validate_path_segment(value, label="objective.metric_id")

    @field_validator("evaluator", mode="before")
    @classmethod
    def validate_evaluator(cls, value: object) -> EvaluatorConfig:
        if isinstance(value, str):
            from ..config.registry import load_named_group

            payload = load_named_group(value, "evaluation")
            raw_evaluator = payload.get("evaluator")
            if raw_evaluator is None:
                raise TypeError("named evaluation specs must declare an evaluator mapping")
            if not isinstance(raw_evaluator, Mapping):
                raise TypeError("named evaluation evaluator payload must be a mapping")
            return coerce_evaluator_config(raw_evaluator)
        if isinstance(value, Mapping):
            return coerce_evaluator_config(value)
        if isinstance(value, EvaluatorConfig):
            return coerce_evaluator_config(value)
        raise TypeError("objective.evaluator must be a spec name, mapping, or config model")


@dataclass(frozen=True, slots=True)
class ObjectiveEvaluationContext:
    model: TemporalModel
    prediction_contract: CompiledPredictionContract
    representation_contract: CompiledRepresentationContract
    realization_policy: CompiledRealizationPolicyContract
    store: CompiledProblemStore
    sample_indices: NDArray[np.int64]
    batch_size: int
    device: str
    reporter: Reporter | None


EvaluateObjectiveMetricsFn = Callable[[MetricSet, ObjectiveEvaluationContext], MetricSet]


@dataclass(frozen=True, slots=True)
class CompiledObjectiveContract:
    objective_id: str
    metric_id: str
    direction: Literal["maximize", "minimize"]
    evaluator_id: str | None
    config_payload: dict[str, object]
    evaluate_metrics_fn: EvaluateObjectiveMetricsFn

    @property
    def semantics(self) -> ObjectiveSemantics:
        return ObjectiveSemantics(
            objective_id=self.objective_id,
            metric_id=self.metric_id,
            direction=self.direction,
            evaluator_id=self.evaluator_id,
        )

    @property
    def checkpoint_monitor(self) -> str:
        if self.evaluator_id is None:
            return f"validation_{self.metric_id}"
        return f"validation_{self.evaluator_id}_{self.metric_id}"

    def evaluate_metrics(
        self,
        validation_metrics: MetricSet,
        *,
        context: ObjectiveEvaluationContext,
    ) -> MetricSet:
        return self.evaluate_metrics_fn(validation_metrics, context)

    def value(self, metrics: MetricSet) -> float:
        return metrics.require(self.metric_id)


@dataclass(frozen=True, slots=True)
class ObjectiveSpec:
    id: str
    config_type: type[ObjectiveConfig]
    compile: Callable[[ObjectiveConfig], CompiledObjectiveContract]


def _compile_validation_training_metric(
    config: ObjectiveConfig,
) -> CompiledObjectiveContract:
    parsed = ValidationTrainingMetricObjectiveConfig.model_validate(config)
    payload = parsed.model_dump(mode="json", exclude_none=True)
    return CompiledObjectiveContract(
        objective_id=parsed.id,
        metric_id=parsed.metric_id,
        direction=parsed.direction.value,
        evaluator_id=None,
        config_payload=payload,
        evaluate_metrics_fn=lambda validation_metrics, context: validation_metrics,
    )


def _compile_validation_evaluator_metric(
    config: ObjectiveConfig,
) -> CompiledObjectiveContract:
    parsed = ValidationEvaluatorMetricObjectiveConfig.model_validate(config)
    evaluator_contract = compile_evaluator_contract(parsed.evaluator)
    payload = parsed.model_dump(mode="json", exclude_none=True)

    def _evaluate(validation_metrics: MetricSet, context: ObjectiveEvaluationContext) -> MetricSet:
        del validation_metrics
        from ..modeling.inference import predict_with_model

        decoded_offsets = predict_with_model(
            context.model,
            prediction_contract=context.prediction_contract,
            representation_contract=context.representation_contract,
            store=context.store,
            sample_indices=context.sample_indices,
            batch_size=context.batch_size,
            device=context.device,
            reporter=context.reporter,
        )
        return evaluator_contract.run(
            context.store,
            context.realization_policy,
            decoded_offsets,
            context.sample_indices,
            context.reporter,
        ).metrics

    return CompiledObjectiveContract(
        objective_id=parsed.id,
        metric_id=parsed.metric_id,
        direction=parsed.direction.value,
        evaluator_id=evaluator_contract.evaluator_id,
        config_payload=payload,
        evaluate_metrics_fn=_evaluate,
    )


def objective_spec(objective_id: str) -> ObjectiveSpec:
    if objective_id == "validation_training_metric":
        return ObjectiveSpec(
            id="validation_training_metric",
            config_type=ValidationTrainingMetricObjectiveConfig,
            compile=_compile_validation_training_metric,
        )
    if objective_id == "validation_evaluator_metric":
        return ObjectiveSpec(
            id="validation_evaluator_metric",
            config_type=ValidationEvaluatorMetricObjectiveConfig,
            compile=_compile_validation_evaluator_metric,
        )
    raise unknown_id_error(
        field_name="objective.id",
        component_id=objective_id,
        known_ids=("validation_training_metric", "validation_evaluator_metric"),
    )


def coerce_objective_config(
    payload: Mapping[str, object] | ObjectiveConfig,
) -> ObjectiveConfig:
    raw_payload, objective_id = config_payload_and_id(
        payload,
        config_type=ObjectiveConfig,
        field_name="objective.id",
        mapping_label="objective",
    )
    spec = objective_spec(objective_id)
    return spec.config_type.model_validate(raw_payload)


def compile_objective_contract(config: ObjectiveConfig) -> CompiledObjectiveContract:
    return objective_spec(config.id).compile(config)
