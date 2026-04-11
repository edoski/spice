"""Lightning module for temporal SPICE models."""

from __future__ import annotations

from dataclasses import dataclass

import lightning as L
import torch
from torch import nn
from torchmetrics.classification import MulticlassAccuracy

from ..core.config import TrainingConfig
from .evaluation import BatchMetrics, compute_batch_metrics
from .models import ModelOutputs, TemporalModel


@dataclass(slots=True)
class EpochMetrics:
    total_loss: float
    accuracy: float
    mean_cost_over_optimum: float
    mean_profit_over_baseline: float


def mean_metrics(metrics: list[BatchMetrics]) -> EpochMetrics:
    if not metrics:
        raise ValueError("Cannot summarize an empty metric list")
    denominator = sum(item.count for item in metrics)
    total_loss_sum = sum(item.total_loss_sum for item in metrics)
    correct_count = sum(item.correct_count for item in metrics)
    realized_fee_sum = sum(item.realized_fee_sum for item in metrics)
    baseline_fee_sum = sum(item.baseline_fee_sum for item in metrics)
    optimal_fee_sum = sum(item.optimal_fee_sum for item in metrics)
    return EpochMetrics(
        total_loss=total_loss_sum / denominator,
        accuracy=correct_count / denominator,
        mean_cost_over_optimum=(realized_fee_sum - optimal_fee_sum) / optimal_fee_sum,
        mean_profit_over_baseline=(baseline_fee_sum - realized_fee_sum) / baseline_fee_sum,
    )


class TemporalLightningModule(L.LightningModule):
    """Training harness that keeps the project-specific task semantics custom."""

    def __init__(
        self,
        model: TemporalModel,
        *,
        class_weights: torch.Tensor,
        action_count: int,
        training_config: TrainingConfig,
    ) -> None:
        super().__init__()
        self.model = model
        self.class_weights = class_weights
        self.action_count = action_count
        self.training_config = training_config
        self.train_accuracy = MulticlassAccuracy(num_classes=action_count)
        self.validation_accuracy = MulticlassAccuracy(num_classes=action_count)
        self.train_history: list[EpochMetrics] = []
        self.validation_history: list[EpochMetrics] = []
        self._train_batches: list[BatchMetrics] = []
        self._validation_batches: list[BatchMetrics] = []
        self._ce_loss = nn.CrossEntropyLoss(weight=class_weights)
        self._smooth_l1 = nn.SmoothL1Loss()

    def forward(self, inputs: torch.Tensor) -> ModelOutputs:
        return self.model(inputs)

    def configure_optimizers(self) -> torch.optim.Optimizer:
        return torch.optim.AdamW(
            self.model.parameters(),
            lr=self.training_config.learning_rate,
            weight_decay=self.training_config.weight_decay,
        )

    def on_train_epoch_start(self) -> None:
        self._train_batches = []

    def on_validation_epoch_start(self) -> None:
        self._validation_batches = []

    def _shared_step(self, batch: dict[str, torch.Tensor], *, stage: str) -> torch.Tensor:
        outputs = self.model(batch["inputs"])
        block_loss = self._ce_loss(outputs.logits, batch["class_label"])
        fee_loss = self._smooth_l1(outputs.fee_hat, batch["target_log_fee"])
        total_loss = (
            self.training_config.action_loss_weight * block_loss
            + self.training_config.fee_loss_weight * fee_loss
        )

        accuracy_metric = (
            self.train_accuracy if stage == "train" else self.validation_accuracy
        )
        accuracy = accuracy_metric(outputs.logits, batch["class_label"])
        self.log(
            f"{stage}/loss",
            total_loss,
            on_step=False,
            on_epoch=True,
            prog_bar=(stage != "train"),
        )
        self.log(
            f"{stage}/accuracy",
            accuracy,
            on_step=False,
            on_epoch=True,
            prog_bar=(stage != "train"),
        )
        self.log(
            f"{stage}_loss",
            total_loss,
            on_step=False,
            on_epoch=True,
            prog_bar=False,
        )
        self.log(
            f"{stage}_accuracy",
            accuracy,
            on_step=False,
            on_epoch=True,
            prog_bar=False,
        )

        metrics = compute_batch_metrics(
            logits=outputs.logits.detach(),
            total_loss=total_loss.detach(),
            class_labels=batch["class_label"].detach(),
            action_log_fees=batch["action_log_fees"].detach(),
            next_block_log_fee=batch["next_block_log_fee"].detach(),
            optimal_log_fee=batch["optimal_log_fee"].detach(),
        )
        if stage == "train":
            self._train_batches.append(metrics)
        else:
            self._validation_batches.append(metrics)
        return total_loss

    def training_step(self, batch: dict[str, torch.Tensor], _batch_idx: int) -> torch.Tensor:
        return self._shared_step(batch, stage="train")

    def validation_step(self, batch: dict[str, torch.Tensor], _batch_idx: int) -> torch.Tensor:
        return self._shared_step(batch, stage="validation")

    def on_train_epoch_end(self) -> None:
        if self._train_batches:
            metrics = mean_metrics(self._train_batches)
            self.train_history.append(metrics)
            self.log(
                "train/profit_over_baseline",
                metrics.mean_profit_over_baseline,
                prog_bar=False,
            )
            self.log("train/cost_over_optimum", metrics.mean_cost_over_optimum, prog_bar=False)

    def on_validation_epoch_end(self) -> None:
        if self._validation_batches:
            metrics = mean_metrics(self._validation_batches)
            self.validation_history.append(metrics)
            self.log(
                "validation/profit_over_baseline",
                metrics.mean_profit_over_baseline,
                prog_bar=True,
            )
            self.log(
                "validation/cost_over_optimum",
                metrics.mean_cost_over_optimum,
                prog_bar=False,
            )
