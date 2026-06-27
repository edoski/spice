"""Shared training-runner callback types."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import torch

from ._fit_policy import TrainingEpochProgress


@dataclass(frozen=True, slots=True)
class TrainingCheckpoint:
    completed_epoch: int
    model_state: dict[str, torch.Tensor]
    optimizer_state: dict[str, object]
    policy_state: dict[str, object]


EpochEndCallback = Callable[[TrainingEpochProgress], None]
EarlyStopCallback = Callable[[int, int], None]
CheckpointCallback = Callable[[TrainingCheckpoint], None]


@dataclass(frozen=True, slots=True)
class TrainingCallbacks:
    on_epoch_end: EpochEndCallback | None = None
    on_early_stop: EarlyStopCallback | None = None
    on_checkpoint: CheckpointCallback | None = None
