"""Model-to-evaluator scoring bridge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import torch

from ..core.errors import SpiceOperatorError
from ..evaluation import CompiledEvaluatorContract, EvaluationSummary
from ..metrics import MetricSet
from ..prediction import CompiledPredictionContract
from ..prediction.contracts import PredictionBatch
from ..prediction.decoding import DecodedPredictionResult, decode_context_from_batch
from ..temporal.execution_policy import (
    CompiledExecutionPolicyContract,
    PreparedActionSpace,
    PreparedTemporalFacts,
)
from ..temporal.problem_store import CompiledProblemStore
from .forward_runtime import (
    run_planned_model_input_forward,
    run_planned_prediction_forward,
)
from .models import TemporalModel
from .representations import CompiledRepresentationContract
from .runtime_planning import (
    ModelingRuntimePlan,
    modeling_backend_scope,
    prepare_model_for_runtime,
)


@dataclass(frozen=True, slots=True)
class EvaluationScoringRuntimePlan:
    model: TemporalModel
    prediction_contract: CompiledPredictionContract
    representation_contract: CompiledRepresentationContract
    execution_policy: CompiledExecutionPolicyContract
    store: CompiledProblemStore
    action_space: PreparedActionSpace
    runtime_plan: ModelingRuntimePlan


@dataclass(frozen=True, slots=True)
class PredictionMetricScoringRuntimePlan:
    model: TemporalModel
    prediction_contract: CompiledPredictionContract
    representation_contract: CompiledRepresentationContract
    execution_policy: CompiledExecutionPolicyContract
    store: CompiledProblemStore
    temporal_facts: PreparedTemporalFacts
    prediction_training_state: object | None
    runtime_plan: ModelingRuntimePlan


def score_evaluation(
    *,
    scoring_plan: EvaluationScoringRuntimePlan,
    evaluator_contract: CompiledEvaluatorContract,
) -> EvaluationSummary:
    evaluator_contract.validate_prediction_contract(scoring_plan.prediction_contract)
    decoded_result = _predict_decoded_result(
        scoring_plan.model,
        prediction_contract=scoring_plan.prediction_contract,
        representation_contract=scoring_plan.representation_contract,
        execution_policy=scoring_plan.execution_policy,
        store=scoring_plan.store,
        action_space=scoring_plan.action_space,
        runtime_plan=scoring_plan.runtime_plan,
    )
    return evaluator_contract.run(
        scoring_plan.store,
        scoring_plan.execution_policy,
        decoded_result,
        action_space=scoring_plan.action_space,
    )


def score_evaluation_metrics(
    *,
    scoring_plan: EvaluationScoringRuntimePlan,
    evaluator_contract: CompiledEvaluatorContract,
) -> MetricSet:
    return score_evaluation(
        scoring_plan=scoring_plan,
        evaluator_contract=evaluator_contract,
    ).metrics


def score_prediction_metrics(
    scoring_plan: PredictionMetricScoringRuntimePlan,
) -> MetricSet:
    if scoring_plan.temporal_facts.action_space.sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")
    runtime_model = prepare_model_for_runtime(
        cast(TemporalModel, scoring_plan.model),
        scoring_plan.runtime_plan,
    )
    accumulator = scoring_plan.prediction_contract.create_epoch_accumulator()

    def _accumulate(batch: PredictionBatch, outputs) -> None:
        _, batch_state = scoring_plan.prediction_contract.compute_batch_loss_and_state(
            outputs,
            batch.targets,
            training_state=scoring_plan.prediction_training_state,
        )
        accumulator.update(batch_state)

    with modeling_backend_scope(scoring_plan.runtime_plan):
        run_planned_prediction_forward(
            runtime_model,
            store=scoring_plan.store,
            temporal_facts=scoring_plan.temporal_facts,
            representation_contract=scoring_plan.representation_contract,
            prediction_contract=scoring_plan.prediction_contract,
            execution_policy=scoring_plan.execution_policy,
            runtime_plan=scoring_plan.runtime_plan,
            on_outputs=_accumulate,
        )
    return accumulator.finalize()


def _predict_decoded_result(
    model: TemporalModel,
    *,
    prediction_contract: CompiledPredictionContract,
    representation_contract: CompiledRepresentationContract,
    execution_policy: CompiledExecutionPolicyContract,
    store: CompiledProblemStore,
    action_space: PreparedActionSpace,
    runtime_plan: ModelingRuntimePlan,
) -> DecodedPredictionResult:
    if action_space.sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")

    runtime_model = prepare_model_for_runtime(model, runtime_plan)
    predictions = prediction_contract.allocate_decoded_result(
        int(action_space.sample_indices.shape[0])
    )

    def _decode_batch(batch, outputs) -> None:
        _validate_finite_outputs(outputs)
        prediction_contract.decode_batch_result_into(
            predictions,
            outputs,
            decode_context_from_batch(batch),
        )

    with modeling_backend_scope(runtime_plan):
        run_planned_model_input_forward(
            runtime_model,
            store=store,
            action_space=action_space,
            representation_contract=representation_contract,
            execution_policy=execution_policy,
            runtime_plan=runtime_plan,
            on_outputs=_decode_batch,
        )
    return predictions


def _validate_finite_outputs(outputs) -> None:
    for head_id, tensor in outputs.heads.items():
        if tensor.is_floating_point() and not bool(torch.isfinite(tensor).all()):
            raise SpiceOperatorError(f"Non-finite model output head during inference: {head_id}")
