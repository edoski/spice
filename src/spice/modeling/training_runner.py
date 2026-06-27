"""Training-runner fit and metric evaluation."""

from __future__ import annotations

from dataclasses import dataclass

import lightning.pytorch as pl

from ..config.models import TrainingConfig
from ..metrics import MetricSet
from ..prediction import CompiledPredictionContract
from ._fit_policy import TrainingFitPolicy
from .dataset_builders import PreparedTrainingDataset
from .lightning_module import SpiceLightningModule
from .models import TemporalModel
from .objective_runtime import CompiledObjectiveRuntime
from .runtime_planning import ModelingRuntimePlan, modeling_backend_scope
from .scoring import EvaluationScoringRuntimePlan
from .training_runner_types import (
    TrainingCallbacks,
    TrainingCheckpoint,
)
from .training_runtime import prepare_training_runtime


@dataclass(slots=True)
class TrainingResult:
    best_epoch: int
    objective_metric_id: str
    best_objective_value: float
    train_history: list[MetricSet]
    validation_history: list[MetricSet]
    objective_history: list[MetricSet]
    prediction_training_state: object | None
    runtime_plan: ModelingRuntimePlan


@dataclass(slots=True)
class TrainingFitSpec:
    model: TemporalModel
    prediction_contract: CompiledPredictionContract
    objective_runtime: CompiledObjectiveRuntime
    prepared: PreparedTrainingDataset
    training_config: TrainingConfig
    checkpoint: TrainingCheckpoint | None = None


def run_training_fit(
    spec: TrainingFitSpec,
    *,
    callbacks: TrainingCallbacks | None = None,
) -> TrainingResult:
    active_callbacks = callbacks or TrainingCallbacks()
    if (
        spec.prepared.samples.train.sample_indices.size == 0
        or spec.prepared.samples.validation.sample_indices.size == 0
    ):
        raise ValueError("Train and validation sample selections must both be non-empty")

    policy = TrainingFitPolicy.create(
        objective_contract=spec.objective_runtime.contract,
        max_epochs=spec.training_config.max_epochs,
        patience=spec.training_config.early_stopping.patience,
        min_delta=spec.training_config.early_stopping.min_delta,
    )

    prepared_runtime = prepare_training_runtime(
        spec.model,
        prediction_contract=spec.prediction_contract,
        execution_policy=spec.prepared.execution_policy,
        store=spec.prepared.store,
        train_samples=spec.prepared.samples.train,
        validation_samples=spec.prepared.samples.validation,
        training_config=spec.training_config,
    )
    fit_model = prepared_runtime.fit_model
    training_runtime_plan = prepared_runtime.batch_plan
    runtime_plan = training_runtime_plan.runtime_plan
    prediction_training_state = training_runtime_plan.prediction_training_state
    start_epoch = 1
    optimizer_state = None
    if spec.checkpoint is not None:
        fit_model.load_state_dict(spec.checkpoint.model_state)
        policy.load_state_dict(spec.checkpoint.policy_state)
        optimizer_state = spec.checkpoint.optimizer_state
        start_epoch = spec.checkpoint.completed_epoch + 1
    objective_scoring_plan = EvaluationScoringRuntimePlan(
        model=fit_model,
        prediction_contract=spec.prediction_contract,
        execution_policy=spec.prepared.execution_policy,
        store=spec.prepared.store,
        action_space=spec.prepared.samples.validation.action_space,
        runtime_plan=runtime_plan,
    )
    module = SpiceLightningModule(
        model=fit_model,
        prediction_contract=spec.prediction_contract,
        objective_runtime=spec.objective_runtime,
        objective_scoring_plan=objective_scoring_plan,
        prediction_training_state=prediction_training_state,
        training_config=spec.training_config,
        policy=policy,
        callbacks=active_callbacks,
        start_epoch=start_epoch,
        optimizer_state=optimizer_state,
    )
    remaining_epochs = max(0, spec.training_config.max_epochs - start_epoch + 1)
    if remaining_epochs > 0:
        trainer = pl.Trainer(
            accelerator="gpu",
            devices=1,
            precision="32-true",
            max_epochs=remaining_epochs,
            num_sanity_val_steps=0,
            use_distributed_sampler=False,
            logger=False,
            enable_checkpointing=False,
            enable_progress_bar=False,
            deterministic=spec.training_config.deterministic,
            log_every_n_steps=spec.training_config.log_every_n_steps,
        )
        with modeling_backend_scope(runtime_plan):
            trainer.fit(
                module,
                train_dataloaders=training_runtime_plan.train_batch_plan.source,
                val_dataloaders=training_runtime_plan.validation_batch_plan.source,
            )

    best = module.finalized_best()
    best_epoch = best.best_epoch
    best_state = best.best_state
    best_value = best.best_objective_value
    spec.model.load_state_dict(best_state)

    return TrainingResult(
        best_epoch=best_epoch,
        objective_metric_id=spec.objective_runtime.contract.metric_id,
        best_objective_value=best_value,
        train_history=policy.train_history,
        validation_history=policy.validation_history,
        objective_history=policy.objective_history,
        prediction_training_state=prediction_training_state,
        runtime_plan=runtime_plan,
    )
