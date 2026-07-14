"""HISTORICAL DISPOSABLE PROTOTYPE: initial Lightning host candidate.

Comparison evidence only. Its broad-best/plain-state projection is superseded by the
native weights-only artifact in decision-contract.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import lightning.pytorch as pl
import torch
from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint
from task_fixture import (
    CLIP_NORM,
    MAX_EPOCHS,
    PATIENCE,
    SEED,
    TRAIN_BATCH_SIZE,
    VALIDATION_BATCH_SIZE,
    CompleteValidationLoss,
    FitResult,
    TensorMapDataset,
    ValidationTotals,
    batch_loss,
    build_frozen_model,
    loss_terms,
    move_model_inputs,
)
from torch.utils.data import DataLoader

MONITOR = "validation_total_loss"


class _AutomaticTask(pl.LightningModule):
    def __init__(
        self,
        definition: object,
        classification: object,
        validation_samples: int,
    ) -> None:
        super().__init__()
        self.model = build_frozen_model(definition)
        self.classification = classification
        self.validation_samples = validation_samples
        self._fit_binding = {"family": definition.family}
        self._validation = CompleteValidationLoss()
        self._last_validation: ValidationTotals | None = None

    def training_step(
        self,
        batch: dict[str, torch.Tensor],
        batch_idx: int,
    ) -> torch.Tensor:
        del batch_idx
        output = self.model(batch["inputs"])
        loss = batch_loss(output, batch, self.classification)
        if not bool(torch.isfinite(loss)):
            raise FloatingPointError("training loss must be finite")
        return loss

    def transfer_batch_to_device(
        self,
        batch: dict[str, torch.Tensor],
        device: torch.device,
        dataloader_idx: int,
    ) -> dict[str, torch.Tensor]:
        del dataloader_idx
        return move_model_inputs(batch, device)

    def configure_gradient_clipping(
        self,
        optimizer: torch.optim.Optimizer,
        gradient_clip_val: float | None = None,
        gradient_clip_algorithm: str | None = None,
    ) -> None:
        del optimizer, gradient_clip_algorithm
        torch.nn.utils.clip_grad_norm_(
            self.model.parameters(),
            max_norm=cast(float, gradient_clip_val),
            error_if_nonfinite=True,
        )

    def on_validation_epoch_start(self) -> None:
        self._validation = CompleteValidationLoss()

    def validation_step(
        self,
        batch: dict[str, torch.Tensor],
        batch_idx: int,
    ) -> None:
        del batch_idx
        output = self.model(batch["inputs"])
        classification_terms, regression_terms = loss_terms(
            output,
            batch,
            self.classification,
        )
        self._validation.update(classification_terms, regression_terms)

    def on_validation_epoch_end(self) -> None:
        totals, total = self._validation.finalize(self.validation_samples)
        self._last_validation = totals
        self.log(
            MONITOR,
            total,
            on_step=False,
            on_epoch=True,
            prog_bar=True,
            logger=False,
            sync_dist=False,
        )

    def on_save_checkpoint(self, checkpoint: dict[str, Any]) -> None:
        validation = cast(ValidationTotals, self._last_validation)
        checkpoint["spice_fit"] = {
            "binding": self._fit_binding,
            "validation_sample_count": validation.sample_count,
            "validation_classification_sum": validation.classification_sum,
            "validation_regression_sum": validation.regression_sum,
        }

    def on_load_checkpoint(self, checkpoint: dict[str, Any]) -> None:
        if checkpoint["spice_fit"]["binding"] != self._fit_binding:
            raise ValueError("native checkpoint provenance does not match the requested fit")

    def configure_optimizers(self) -> torch.optim.Optimizer:
        return torch.optim.AdamW(self.model.parameters(), lr=0.0, weight_decay=0.0)


def fit_lightning(
    definition: object,
    training: TensorMapDataset,
    validation: TensorMapDataset,
    classification: object,
    work_dir: Path,
    *,
    resume: bool = False,
    _job_epoch_limit: int | None = None,
) -> FitResult | None:
    """Run one Lightning candidate; the underscored limit only simulates job interruption."""
    pl.seed_everything(SEED, workers=True, verbose=False)
    generator = torch.Generator().manual_seed(SEED)
    work_dir.mkdir(parents=True, exist_ok=True)
    module = _AutomaticTask(definition, classification, len(validation))
    train_loader = DataLoader(
        training,
        batch_size=TRAIN_BATCH_SIZE,
        shuffle=True,
        generator=generator,
        drop_last=False,
    )
    validation_loader = DataLoader(
        validation,
        batch_size=VALIDATION_BATCH_SIZE,
        shuffle=False,
        drop_last=False,
    )
    early_stopping = EarlyStopping(
        monitor=MONITOR,
        mode="min",
        min_delta=0.0,
        patience=PATIENCE,
        strict=True,
        check_finite=False,
        check_on_train_epoch_end=False,
    )
    best_checkpointing = ModelCheckpoint(
        dirpath=work_dir,
        filename="best",
        monitor=MONITOR,
        mode="min",
        save_top_k=1,
        save_on_train_epoch_end=False,
        enable_version_counter=False,
    )
    last_checkpointing = ModelCheckpoint(
        dirpath=work_dir,
        filename="last",
        save_on_train_epoch_end=False,
        enable_version_counter=False,
    )
    trainer = pl.Trainer(
        accelerator="cpu",
        devices=1,
        precision="32-true",
        max_epochs=_job_epoch_limit or MAX_EPOCHS,
        callbacks=[early_stopping, best_checkpointing, last_checkpointing],
        logger=False,
        enable_progress_bar=False,
        enable_model_summary=False,
        num_sanity_val_steps=0,
        gradient_clip_val=CLIP_NORM,
        gradient_clip_algorithm="norm",
        deterministic=True,
    )
    checkpoint_path = work_dir / "last.ckpt"
    trainer.fit(
        module,
        train_dataloaders=train_loader,
        val_dataloaders=validation_loader,
        ckpt_path=checkpoint_path if resume else None,
    )
    if _job_epoch_limit is not None:
        return None

    best_path = Path(best_checkpointing.best_model_path)
    if not best_path.is_file() or not checkpoint_path.is_file():
        raise RuntimeError("native best and completed-boundary checkpoints are required")
    best_checkpoint = torch.load(best_path, map_location="cpu", weights_only=True)
    boundary_checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    best_state = _extract_model_state(best_checkpoint["state_dict"])
    module.model.to("cpu")
    module.model.load_state_dict(best_state, strict=True)
    module.model.eval()
    completed_epochs = int(boundary_checkpoint["epoch"]) + 1
    best_epoch = int(best_checkpoint["epoch"]) + 1
    fit_metadata = best_checkpoint["spice_fit"]
    best_validation = ValidationTotals(
        sample_count=int(fit_metadata["validation_sample_count"]),
        classification_sum=float(fit_metadata["validation_classification_sum"]),
        regression_sum=float(fit_metadata["validation_regression_sum"]),
    )
    stop_reason = "patience" if early_stopping.wait_count >= PATIENCE else "max_epochs"
    return FitResult(
        best_state_dict=best_state,
        best_validation=best_validation,
        earliest_best_epoch=best_epoch,
        completed_epochs=completed_epochs,
        stop_reason=stop_reason,
        optimization_examples=completed_epochs * len(training),
        minibatches=int(boundary_checkpoint["global_step"]),
        optimizer_updates=int(boundary_checkpoint["global_step"]),
    )


def _extract_model_state(state: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    prefix = "model."
    selected = {
        name.removeprefix(prefix): value for name, value in state.items() if name.startswith(prefix)
    }
    if not selected or len(selected) != len(state):
        raise ValueError("best checkpoint must contain only the exact model.* state")
    return selected


def inspect_lightning_checkpoint(path: Path) -> dict[str, Any]:
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    return {
        "keys": sorted(checkpoint),
        "completed_epochs": int(checkpoint["epoch"]) + 1,
        "global_step": int(checkpoint["global_step"]),
        "callback_states": sorted(str(key) for key in checkpoint["callbacks"]),
        "optimizer_states": len(checkpoint["optimizer_states"]),
        "loop_state": bool(checkpoint["loops"]),
    }
