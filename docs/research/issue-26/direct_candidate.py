"""HISTORICAL DISPOSABLE PROTOTYPE: direct-PyTorch host candidate.

Comparison evidence only. The approved contract chooses Lightning and rejects this
custom lifecycle. See decision-contract.md.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
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


def seed_direct(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def cpu_state_dict(state: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    return {
        name: value.detach().to(device="cpu", dtype=value.dtype).clone()
        for name, value in state.items()
    }


@dataclass(slots=True)
class _FitState:
    completed_epoch: int = 0
    best_validation: ValidationTotals | None = None
    best_model_state: dict[str, torch.Tensor] | None = None
    best_epoch: int = 0
    non_improvements: int = 0

    def observe(self, epoch: int, validation: ValidationTotals) -> bool:
        improved = (
            self.best_validation is None or validation.total_loss < self.best_validation.total_loss
        )
        if improved:
            self.best_validation = validation
            self.best_epoch = epoch
            self.non_improvements = 0
        else:
            self.non_improvements += 1
        self.completed_epoch = epoch
        return improved


def fit_direct(
    definition: object,
    training: TensorMapDataset,
    validation: TensorMapDataset,
    classification: object,
    work_dir: Path,
    *,
    resume: bool = False,
    _job_epoch_limit: int | None = None,
) -> FitResult | None:
    """Run one direct candidate; the underscored limit only simulates job interruption."""
    seed_direct()
    train_generator = torch.Generator().manual_seed(SEED)
    device = torch.device("cpu")
    model = build_frozen_model(definition).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.0, weight_decay=0.0)
    train_loader = DataLoader(
        training,
        batch_size=TRAIN_BATCH_SIZE,
        shuffle=True,
        generator=train_generator,
        drop_last=False,
    )
    validation_loader = DataLoader(
        validation,
        batch_size=VALIDATION_BATCH_SIZE,
        shuffle=False,
        drop_last=False,
    )
    work_dir.mkdir(parents=True, exist_ok=True)
    boundary_path = work_dir / "boundary.pt"
    state = _FitState()

    if resume:
        checkpoint = torch.load(boundary_path, map_location=device, weights_only=True)
        if checkpoint["family"] != definition.family:
            raise ValueError("boundary checkpoint family does not match the requested definition")
        model.load_state_dict(checkpoint["model_state"], strict=True)
        optimizer.load_state_dict(checkpoint["optimizer_state"])
        state = _FitState(
            completed_epoch=int(checkpoint["completed_epoch"]),
            best_validation=ValidationTotals(
                sample_count=int(checkpoint["best_sample_count"]),
                classification_sum=float(checkpoint["best_classification_sum"]),
                regression_sum=float(checkpoint["best_regression_sum"]),
            ),
            best_model_state=checkpoint["best_model_state"],
            best_epoch=int(checkpoint["best_epoch"]),
            non_improvements=int(checkpoint["non_improvements"]),
        )

    for epoch in range(state.completed_epoch + 1, MAX_EPOCHS + 1):
        model.train()
        for raw_batch in train_loader:
            batch = move_model_inputs(raw_batch, device)
            optimizer.zero_grad(set_to_none=True)
            output = model(batch["inputs"])
            loss = batch_loss(output, batch, classification)
            if not bool(torch.isfinite(loss)):
                raise FloatingPointError("training loss must be finite")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                max_norm=CLIP_NORM,
                error_if_nonfinite=True,
            )
            optimizer.step()

        validation_totals = _validate(model, validation_loader, classification, device)
        improved = state.observe(epoch, validation_totals)
        if improved:
            state.best_model_state = cpu_state_dict(model.state_dict())
        _save_boundary(
            boundary_path,
            definition=definition,
            model=model,
            optimizer=optimizer,
            state=state,
        )

        if _job_epoch_limit is not None and epoch >= _job_epoch_limit:
            return None
        if state.non_improvements >= PATIENCE:
            stop_reason = "patience"
            break
    else:
        stop_reason = "max_epochs"

    best_state = cast(dict[str, torch.Tensor], state.best_model_state)
    best_validation = cast(ValidationTotals, state.best_validation)
    model.to("cpu")
    model.load_state_dict(best_state, strict=True)
    model.eval()
    return FitResult(
        best_state_dict=best_state,
        best_validation=best_validation,
        earliest_best_epoch=state.best_epoch,
        completed_epochs=state.completed_epoch,
        stop_reason=stop_reason,
        optimization_examples=state.completed_epoch * len(training),
        minibatches=state.completed_epoch * len(train_loader),
        optimizer_updates=state.completed_epoch * len(train_loader),
    )


def _validate(
    model: torch.nn.Module,
    loader: DataLoader[dict[str, torch.Tensor]],
    classification: object,
    device: torch.device,
) -> ValidationTotals:
    accumulator = CompleteValidationLoss()
    model.eval()
    with torch.inference_mode():
        for raw_batch in loader:
            batch = move_model_inputs(raw_batch, device)
            output = model(batch["inputs"])
            classification_terms, regression_terms = loss_terms(output, batch, classification)
            accumulator.update(classification_terms, regression_terms)
    totals, _ = accumulator.finalize(len(loader.dataset))
    return totals


def _save_boundary(
    path: Path,
    *,
    definition: object,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    state: _FitState,
) -> None:
    best_validation = cast(ValidationTotals, state.best_validation)
    torch.save(
        {
            "family": definition.family,
            "model_state": cpu_state_dict(model.state_dict()),
            "optimizer_state": optimizer.state_dict(),
            "completed_epoch": state.completed_epoch,
            "best_model_state": state.best_model_state,
            "best_sample_count": best_validation.sample_count,
            "best_classification_sum": best_validation.classification_sum,
            "best_regression_sum": best_validation.regression_sum,
            "best_epoch": state.best_epoch,
            "non_improvements": state.non_improvements,
        },
        path,
    )


def inspect_direct_checkpoint(path: Path) -> dict[str, Any]:
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    return {
        "keys": sorted(checkpoint),
        "completed_epoch": int(checkpoint["completed_epoch"]),
        "best_epoch": int(checkpoint["best_epoch"]),
        "non_improvements": int(checkpoint["non_improvements"]),
        "optimizer_state_entries": len(checkpoint["optimizer_state"]["state"]),
    }
