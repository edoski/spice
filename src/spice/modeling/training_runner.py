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
from .runtime_planning import ModelingRuntimePlan, modeling_backend_scope
from .training_runner_types import (
    TrainingCallbacks,
    TrainingCheckpoint,
)
from .training_runtime import prepare_training_runtime


@dataclass(slots=True)
class TrainingResult:
    best_epoch: int
    best_validation_loss: float
    train_history: list[MetricSet]
    validation_history: list[MetricSet]
    prediction_training_state: object | None
    runtime_plan: ModelingRuntimePlan


@dataclass(slots=True)
class TrainingFitSpec:
    model: TemporalModel
    prediction_contract: CompiledPredictionContract
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
    module = SpiceLightningModule(
        model=fit_model,
        prediction_contract=spec.prediction_contract,
        runtime_plan=runtime_plan,
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
    best_value = best.best_validation_loss
    spec.model.load_state_dict(best_state)

    return TrainingResult(
        best_epoch=best_epoch,
        best_validation_loss=best_value,
        train_history=policy.train_history,
        validation_history=policy.validation_history,
        prediction_training_state=prediction_training_state,
        runtime_plan=runtime_plan,
    )
