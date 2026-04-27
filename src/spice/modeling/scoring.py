"""Model-to-evaluator scoring bridge."""

from __future__ import annotations

from dataclasses import dataclass

from ..evaluation import CompiledEvaluatorContract, EvaluationSummary
from ..prediction import CompiledPredictionContract
from ..temporal.execution_policy import CompiledExecutionPolicyContract
from ..temporal.problem_store import CompiledProblemStore, IntVector
from .families.base import ModelConfig
from .inference import predict_with_model
from .models import TemporalModel
from .representations import CompiledRepresentationContract


@dataclass(frozen=True, slots=True)
class EvaluationScoringContext:
    model: TemporalModel
    model_config: ModelConfig
    prediction_contract: CompiledPredictionContract
    representation_contract: CompiledRepresentationContract
    evaluator_contract: CompiledEvaluatorContract
    execution_policy: CompiledExecutionPolicyContract
    store: CompiledProblemStore
    sample_indices: IntVector
    batch_size: int


def score_evaluation(context: EvaluationScoringContext) -> EvaluationSummary:
    context.evaluator_contract.validate_prediction_contract(context.prediction_contract)
    decoded_offsets = predict_with_model(
        context.model,
        model_config=context.model_config,
        prediction_contract=context.prediction_contract,
        representation_contract=context.representation_contract,
        store=context.store,
        sample_indices=context.sample_indices,
        batch_size=context.batch_size,
    )
    return context.evaluator_contract.run(
        context.store,
        context.execution_policy,
        decoded_offsets,
        sample_indices=context.sample_indices,
    )
