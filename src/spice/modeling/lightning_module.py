"""Thin Lightning host for SPICE training fit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import lightning.pytorch as pl
import torch

from ..config.models import TrainingConfig
from ..prediction import CompiledPredictionContract
from ..prediction.contracts import PredictionBatch
from ._fit_policy import CompletedEpoch, FitPolicyDecision, TrainingFitPolicy
from ._runtime import precision_context
from .models import TemporalModel
from .objective_runtime import CompiledObjectiveRuntime
from .scoring import EvaluationScoringRuntimePlan
from .training_runner_types import TrainingCallbacks, TrainingCheckpoint


@dataclass(frozen=True, slots=True)
class LightningFitResult:
    best_epoch: int
    best_state: dict[str, torch.Tensor]
    best_objective_value: float


class SpiceLightningModule(pl.LightningModule):
    def __init__(
        self,
        *,
        model: TemporalModel,
        prediction_contract: CompiledPredictionContract,
        objective_runtime: CompiledObjectiveRuntime,
        objective_scoring_plan: EvaluationScoringRuntimePlan,
        prediction_training_state: object | None,
        training_config: TrainingConfig,
        policy: TrainingFitPolicy,
        callbacks: TrainingCallbacks,
        start_epoch: int,
        optimizer_state: dict[str, object] | None,
    ) -> None:
        super().__init__()
        self.model = model
        self.prediction_contract = prediction_contract
        self.objective_runtime = objective_runtime
        self.objective_scoring_plan = objective_scoring_plan
        self.prediction_training_state = prediction_training_state
        self.training_config = training_config
        self.policy = policy
        self.callbacks = callbacks
        self.start_epoch = start_epoch
        self.optimizer_state = optimizer_state
        self._train_accumulator = None
        self._validation_accumulator = None
        self._last_train_metrics = None
        self._stop_before_validation = False
        self._optimizer_state_loaded = False
        self.automatic_optimization = False

    def configure_optimizers(self) -> torch.optim.Optimizer:
        return torch.optim.AdamW(
            self.model.parameters(),
            lr=self.training_config.learning_rate,
            weight_decay=self.training_config.weight_decay,
        )

    def transfer_batch_to_device(
        self,
        batch: PredictionBatch,
        device: torch.device,
        dataloader_idx: int,
    ) -> PredictionBatch:
        del device, dataloader_idx
        return batch

    def on_fit_start(self) -> None:
        if self.optimizer_state is None or self._optimizer_state_loaded:
            return
        optimizer = self._optimizer()
        optimizer.load_state_dict(self.optimizer_state)
        self._optimizer_state_loaded = True

    def on_train_epoch_start(self) -> None:
        self._train_accumulator = self.prediction_contract.create_epoch_accumulator()
        self._last_train_metrics = None
        self._stop_before_validation = False

    def training_step(self, batch: PredictionBatch, batch_idx: int) -> None:
        del batch_idx
        optimizer = self._optimizer()
        device_batch = batch.to_device(self.objective_scoring_plan.runtime_plan.resolved_device)
        optimizer.zero_grad(set_to_none=True)
        with precision_context(precision=self.objective_scoring_plan.runtime_plan.precision):
            outputs = self.model(**device_batch.model_kwargs())
            loss, batch_state = self.prediction_contract.compute_batch_loss_and_state(
                outputs,
                device_batch.targets,
                training_state=self.prediction_training_state,
            )
        self.manual_backward(loss)
        torch.nn.utils.clip_grad_norm_(
            self.model.parameters(),
            self.training_config.gradient_clip_norm,
        )
        optimizer.step()
        if self._train_accumulator is None:
            raise RuntimeError("train accumulator is not initialized")
        self._train_accumulator.update(batch_state)

    def on_train_epoch_end(self) -> None:
        if self._train_accumulator is None:
            raise RuntimeError("train accumulator is not initialized")
        epoch = self._spice_epoch()
        train_metrics = self._train_accumulator.finalize()
        decision = self.policy.handle_nonfinite_metrics(
            epoch=epoch,
            phase="train",
            metrics=train_metrics,
        )
        self._last_train_metrics = train_metrics
        if decision is None:
            return
        self._emit_early_stop(decision)
        self._stop_before_validation = True
        if self.trainer is not None:
            self.trainer.should_stop = True

    def on_validation_epoch_start(self) -> None:
        self._validation_accumulator = self.prediction_contract.create_epoch_accumulator()

    def validation_step(self, batch: PredictionBatch, batch_idx: int) -> None:
        del batch_idx
        if self._stop_before_validation:
            return
        device_batch = batch.to_device(self.objective_scoring_plan.runtime_plan.resolved_device)
        with precision_context(precision=self.objective_scoring_plan.runtime_plan.precision):
            outputs = self.model(**device_batch.model_kwargs())
            _, batch_state = self.prediction_contract.compute_batch_loss_and_state(
                outputs,
                device_batch.targets,
                training_state=self.prediction_training_state,
            )
        if self._validation_accumulator is None:
            raise RuntimeError("validation accumulator is not initialized")
        self._validation_accumulator.update(batch_state)

    def on_validation_epoch_end(self) -> None:
        if self._stop_before_validation:
            return
        if self._last_train_metrics is None:
            return
        if self._validation_accumulator is None:
            raise RuntimeError("validation accumulator is not initialized")
        epoch = self._spice_epoch()
        validation_metrics = self._validation_accumulator.finalize()
        validation_decision = self.policy.handle_nonfinite_metrics(
            epoch=epoch,
            phase="validation",
            metrics=validation_metrics,
        )
        if validation_decision is not None:
            self._emit_early_stop(validation_decision)
            if self.trainer is not None:
                self.trainer.should_stop = True
            return
        objective_metrics = self.objective_runtime.evaluate_metrics(
            validation_metrics,
            scoring_plan=self.objective_scoring_plan,
        )
        objective_decision = self.policy.handle_nonfinite_metrics(
            epoch=epoch,
            phase="objective",
            metrics=objective_metrics,
        )
        if objective_decision is not None:
            self._emit_early_stop(objective_decision)
            if self.trainer is not None:
                self.trainer.should_stop = True
            return
        fit_decision = self.policy.record_completed_epoch(
            CompletedEpoch(
                epoch=epoch,
                train_metrics=self._last_train_metrics,
                validation_metrics=validation_metrics,
                objective_metrics=objective_metrics,
            ),
            model=self.model,
        )
        if fit_decision.progress is not None and self.callbacks.on_epoch_end is not None:
            self.callbacks.on_epoch_end(fit_decision.progress)
        if self.callbacks.on_checkpoint is not None:
            optimizer = self._optimizer()
            self.callbacks.on_checkpoint(
                TrainingCheckpoint(
                    completed_epoch=epoch,
                    model_state={
                        key: value.detach().cpu().clone()
                        for key, value in self.model.state_dict().items()
                    },
                    optimizer_state=optimizer.state_dict(),
                    policy_state=self.policy.state_dict(),
                )
            )
        if fit_decision.should_stop:
            self._emit_early_stop(fit_decision)
            if self.trainer is not None:
                self.trainer.should_stop = True

    def finalized_best(self) -> LightningFitResult:
        best_epoch, best_state, best_value = self.policy.finalized_best(model=self.model)
        return LightningFitResult(
            best_epoch=best_epoch,
            best_state=best_state,
            best_objective_value=best_value,
        )

    def _spice_epoch(self) -> int:
        return self.start_epoch + int(self.current_epoch)

    def _emit_early_stop(self, decision: FitPolicyDecision) -> None:
        if decision.early_stop is not None and self.callbacks.on_early_stop is not None:
            self.callbacks.on_early_stop(*decision.early_stop)

    def _optimizer(self) -> torch.optim.Optimizer:
        optimizer = self.optimizers(use_pl_optimizer=False)
        if isinstance(optimizer, list):
            if len(optimizer) != 1:
                raise RuntimeError("SPICE training expects exactly one optimizer")
            return cast(torch.optim.Optimizer, optimizer[0])
        return cast(torch.optim.Optimizer, optimizer)
