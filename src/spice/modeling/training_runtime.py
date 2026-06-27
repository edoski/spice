"""Training runtime planning."""

from __future__ import annotations

from dataclasses import dataclass

from ..config.models import TrainingConfig
from ..prediction import CompiledPredictionContract
from ..prediction.contracts import PredictionBatch
from ..temporal.execution_policy import CompiledExecutionPolicyContract
from ..temporal.problem_store import CompiledProblemStore
from .batch_plan import BatchPlan, build_prediction_batch_plan
from .dataset_builders import PreparedTrainingSampleSelection
from .models import TemporalModel
from .runtime_planning import (
    ModelingRuntimePlan,
    build_training_modeling_runtime_plan,
    modeling_backend_scope,
    prepare_model_for_runtime,
)


@dataclass(frozen=True, slots=True)
class TrainingRuntimePlan:
    runtime_plan: ModelingRuntimePlan
    train_batch_plan: BatchPlan[PredictionBatch]
    validation_batch_plan: BatchPlan[PredictionBatch]
    prediction_training_state: object | None


@dataclass(frozen=True, slots=True)
class PreparedTrainingRuntime:
    fit_model: TemporalModel
    batch_plan: TrainingRuntimePlan

def plan_training_runtime(
    model: TemporalModel,
    *,
    prediction_contract: CompiledPredictionContract,
    execution_policy: CompiledExecutionPolicyContract,
    store: CompiledProblemStore,
    train_samples: PreparedTrainingSampleSelection,
    validation_samples: PreparedTrainingSampleSelection,
    runtime_plan: ModelingRuntimePlan,
) -> TrainingRuntimePlan:
    del model, execution_policy
    prediction_training_state = prediction_contract.fit_training_state(
        temporal_facts=train_samples.temporal_facts,
    )
    train_batch_plan = build_prediction_batch_plan(
        store,
        temporal_facts=train_samples.temporal_facts,
        prediction_contract=prediction_contract,
        runtime_plan=runtime_plan,
        shuffle=True,
    )
    validation_batch_plan = build_prediction_batch_plan(
        store,
        temporal_facts=validation_samples.temporal_facts,
        prediction_contract=prediction_contract,
        runtime_plan=runtime_plan,
        shuffle=False,
    )
    return TrainingRuntimePlan(
        runtime_plan=runtime_plan,
        train_batch_plan=train_batch_plan,
        validation_batch_plan=validation_batch_plan,
        prediction_training_state=prediction_training_state,
    )


def prepare_training_runtime(
    model: TemporalModel,
    *,
    prediction_contract: CompiledPredictionContract,
    execution_policy: CompiledExecutionPolicyContract,
    store: CompiledProblemStore,
    train_samples: PreparedTrainingSampleSelection,
    validation_samples: PreparedTrainingSampleSelection,
    training_config: TrainingConfig,
) -> PreparedTrainingRuntime:
    runtime_plan = build_training_modeling_runtime_plan(
        training_config=training_config,
    )
    fit_model = prepare_model_for_runtime(model, runtime_plan)
    with modeling_backend_scope(runtime_plan):
        batch_plan = plan_training_runtime(
            fit_model,
            prediction_contract=prediction_contract,
            execution_policy=execution_policy,
            store=store,
            train_samples=train_samples,
            validation_samples=validation_samples,
            runtime_plan=runtime_plan,
        )
    return PreparedTrainingRuntime(
        fit_model=fit_model,
        batch_plan=batch_plan,
    )
