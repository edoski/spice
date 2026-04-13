"""Lightning module for temporal SPICE models."""

from __future__ import annotations

import lightning as L
import torch

from ..config import TrainingConfig
from .models import ModelOutputs, TemporalModel
from .objective import (
    BatchMetrics,
    EpochMetrics,
    compute_temporal_batch_metrics,
    summarize_epoch_metrics,
)
from .representations import SequenceEventBatch


class TemporalLightningModule(L.LightningModule):
    """Training harness that keeps the project-specific task semantics custom."""

    def __init__(
        self,
        model: TemporalModel,
        *,
        training_config: TrainingConfig,
    ) -> None:
        super().__init__()
        self.model = model
        self.training_config = training_config
        self.train_history: list[EpochMetrics] = []
        self.validation_history: list[EpochMetrics] = []
        self._train_batches: list[BatchMetrics] = []
        self._validation_batches: list[BatchMetrics] = []

    def forward(self, inputs: torch.Tensor, input_mask: torch.Tensor) -> ModelOutputs:
        return self.model(inputs, input_mask)

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

    def _shared_step(self, batch: SequenceEventBatch, *, stage: str) -> torch.Tensor:
        outputs = self.model(batch.inputs, batch.input_mask)
        objective_loss, metrics = compute_temporal_batch_metrics(
            outputs.logits,
            batch.candidate_log_fees,
            batch.candidate_mask,
        )
        self.log(
            f"{stage}/objective_loss",
            objective_loss,
            on_step=False,
            on_epoch=True,
            prog_bar=False,
        )
        self.log(
            f"{stage}/exact_optimum_hit_rate",
            metrics.exact_hit_count / metrics.count,
            on_step=False,
            on_epoch=True,
            prog_bar=(stage != "train"),
        )
        self.log(
            f"{stage}_objective_loss",
            objective_loss,
            on_step=False,
            on_epoch=True,
            prog_bar=False,
        )
        self.log(
            f"{stage}_exact_optimum_hit_rate",
            metrics.exact_hit_count / metrics.count,
            on_step=False,
            on_epoch=True,
            prog_bar=False,
        )

        if stage == "train":
            self._train_batches.append(metrics)
        else:
            self._validation_batches.append(metrics)
        return objective_loss

    def training_step(self, batch: SequenceEventBatch, _batch_idx: int) -> torch.Tensor:
        return self._shared_step(batch, stage="train")

    def validation_step(self, batch: SequenceEventBatch, _batch_idx: int) -> torch.Tensor:
        return self._shared_step(batch, stage="validation")

    def on_train_epoch_end(self) -> None:
        if self._train_batches:
            metrics = summarize_epoch_metrics(self._train_batches)
            self.train_history.append(metrics)
            self.log(
                "train/profit_over_baseline",
                metrics.profit_over_baseline,
                prog_bar=False,
            )
            self.log("train_profit_over_baseline", metrics.profit_over_baseline, prog_bar=False)
            self.log("train/cost_over_optimum", metrics.cost_over_optimum, prog_bar=False)
            self.log("train_cost_over_optimum", metrics.cost_over_optimum, prog_bar=False)

    def on_validation_epoch_end(self) -> None:
        if self._validation_batches:
            metrics = summarize_epoch_metrics(self._validation_batches)
            self.validation_history.append(metrics)
            self.log(
                "validation/profit_over_baseline",
                metrics.profit_over_baseline,
                prog_bar=True,
            )
            self.log(
                "validation_profit_over_baseline",
                metrics.profit_over_baseline,
                prog_bar=False,
            )
            self.log(
                "validation/cost_over_optimum",
                metrics.cost_over_optimum,
                prog_bar=False,
            )
            self.log(
                "validation_cost_over_optimum",
                metrics.cost_over_optimum,
                prog_bar=False,
            )
