"""Internal training fit-policy state machine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import numpy as np
import torch

from ..core.errors import SpiceOperatorError
from ..metrics import MetricSet
from .models import TemporalModel

SELECTION_METRIC_ID = "total_loss"


@dataclass(frozen=True, slots=True)
class TrainingEpochProgress:
    epoch: int
    max_epochs: int
    train_metrics: MetricSet
    validation_metrics: MetricSet
    best_epoch: int
    best_validation_loss: float


@dataclass(frozen=True, slots=True)
class CompletedEpoch:
    epoch: int
    train_metrics: MetricSet
    validation_metrics: MetricSet


@dataclass(frozen=True, slots=True)
class FitPolicyDecision:
    should_stop: bool = False
    progress: TrainingEpochProgress | None = None
    early_stop: tuple[int, int] | None = None


@dataclass(slots=True)
class TrainingFitPolicy:
    max_epochs: int
    patience: int
    min_delta: float
    train_history: list[MetricSet]
    validation_history: list[MetricSet]
    best_state: dict[str, torch.Tensor] | None
    best_epoch: int
    epochs_without_improvement: int

    @classmethod
    def create(
        cls,
        *,
        max_epochs: int,
        patience: int,
        min_delta: float,
    ) -> TrainingFitPolicy:
        return cls(
            max_epochs=max_epochs,
            patience=patience,
            min_delta=min_delta,
            train_history=[],
            validation_history=[],
            best_state=None,
            best_epoch=0,
            epochs_without_improvement=0,
        )

    def handle_nonfinite_metrics(
        self,
        *,
        epoch: int,
        phase: str,
        metrics: MetricSet,
    ) -> FitPolicyDecision | None:
        if _all_metrics_finite(metrics):
            return None
        if self.best_epoch > 0:
            return FitPolicyDecision(
                should_stop=True,
                early_stop=(epoch, self.best_epoch),
            )
        raise _nonfinite_metric_error(
            epoch=epoch,
            phase=phase,
            best_epoch=self.best_epoch,
        )

    def record_completed_epoch(
        self,
        completed: CompletedEpoch,
        *,
        model: TemporalModel,
    ) -> FitPolicyDecision:
        self.train_history.append(completed.train_metrics)
        self.validation_history.append(completed.validation_metrics)

        if _is_improvement(
            current_epoch=completed.epoch,
            best_epoch=self.best_epoch,
            history=self.validation_history,
            min_delta=self.min_delta,
        ):
            self.best_state = _clone_cpu_state(model)
            self.best_epoch = completed.epoch
            self.epochs_without_improvement = 0
        else:
            self.epochs_without_improvement += 1

        best_value = self.validation_history[self.best_epoch - 1].require(SELECTION_METRIC_ID)
        progress = TrainingEpochProgress(
            epoch=completed.epoch,
            max_epochs=self.max_epochs,
            train_metrics=completed.train_metrics,
            validation_metrics=completed.validation_metrics,
            best_epoch=self.best_epoch,
            best_validation_loss=best_value,
        )
        if self.epochs_without_improvement >= self.patience:
            return FitPolicyDecision(
                should_stop=True,
                progress=progress,
                early_stop=(completed.epoch, self.best_epoch),
            )
        return FitPolicyDecision(progress=progress)

    def finalized_best(self) -> tuple[int, dict[str, torch.Tensor], float]:
        if self.best_state is None:
            raise SpiceOperatorError("Training completed without a finite best validation state")
        best_value = self.validation_history[self.best_epoch - 1].require(SELECTION_METRIC_ID)
        return self.best_epoch, self.best_state, best_value

    def state_dict(self) -> dict[str, object]:
        return {
            "train_history": [_metric_payload(metrics) for metrics in self.train_history],
            "validation_history": [
                _metric_payload(metrics) for metrics in self.validation_history
            ],
            "best_state": self.best_state,
            "best_epoch": self.best_epoch,
            "epochs_without_improvement": self.epochs_without_improvement,
        }

    def load_state_dict(self, state: dict[str, object]) -> None:
        self.train_history = [
            MetricSet(dict(cast(dict[str, float], payload)))
            for payload in cast(list[object], state["train_history"])
        ]
        self.validation_history = [
            MetricSet(dict(cast(dict[str, float], payload)))
            for payload in cast(list[object], state["validation_history"])
        ]
        self.best_state = cast(dict[str, torch.Tensor] | None, state["best_state"])
        self.best_epoch = int(cast(int, state["best_epoch"]))
        self.epochs_without_improvement = int(
            cast(int, state["epochs_without_improvement"])
        )


def _clone_cpu_state(model: TemporalModel) -> dict[str, torch.Tensor]:
    return {
        key: value.detach().cpu().clone()
        for key, value in model.state_dict().items()
    }


def _metric_payload(metrics: MetricSet) -> dict[str, float]:
    return dict(metrics.values)


def _all_metrics_finite(metrics: MetricSet) -> bool:
    return all(np.isfinite(value) for value in metrics.values.values())


def require_finite_metrics(
    metrics: MetricSet,
    *,
    phase: str,
) -> None:
    if _all_metrics_finite(metrics):
        return
    raise SpiceOperatorError(f"Non-finite {phase} metrics")


def _nonfinite_metric_error(
    *,
    epoch: int,
    phase: str,
    best_epoch: int,
) -> SpiceOperatorError:
    return SpiceOperatorError(
        f"Non-finite {phase} metrics at epoch {epoch} before any valid best state"
    )


def _is_improvement(
    *,
    current_epoch: int,
    best_epoch: int,
    history: list[MetricSet],
    min_delta: float,
) -> bool:
    if best_epoch == 0:
        return True
    current_value = history[current_epoch - 1].require(SELECTION_METRIC_ID)
    best_value = history[best_epoch - 1].require(SELECTION_METRIC_ID)
    return current_value < best_value - min_delta
