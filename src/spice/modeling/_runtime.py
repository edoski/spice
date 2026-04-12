"""Internal PyTorch runtime helpers shared by training and inference."""

from __future__ import annotations

import random

import numpy as np
import torch
from numpy.typing import NDArray

from ..core.config import CompileMode, ModelFamily, TrainingConfig, TrainingPrecision
from ..data.datasets import TemporalDatasetStore
from .torch_datasets import SequenceBatchLoader

IntVector = NDArray[np.int64]


def resolve_device(device: str) -> torch.device:
    if device != "auto":
        return torch.device(device)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def set_global_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def resolve_trainer_precision(
    training_config: TrainingConfig,
    *,
    device: torch.device,
    family: ModelFamily,
) -> str:
    precision = training_config.precision
    if precision is TrainingPrecision.AUTO:
        if device.type == "cpu":
            precision = TrainingPrecision.FP32
        elif device.type == "mps" and family is ModelFamily.LSTM:
            precision = TrainingPrecision.FP32
        elif device.type == "mps":
            precision = TrainingPrecision.BF16_MIXED
        elif device.type == "cuda" and torch.cuda.is_bf16_supported():
            precision = TrainingPrecision.BF16_MIXED
        elif device.type == "cuda":
            precision = TrainingPrecision.FP16_MIXED
        else:
            precision = TrainingPrecision.FP32

    if precision is TrainingPrecision.FP32:
        return "32-true"
    if precision is TrainingPrecision.FP16_MIXED:
        return "16-mixed"
    if precision is TrainingPrecision.BF16_MIXED:
        return "bf16-mixed"
    raise ValueError(f"Unsupported training precision: {precision}")


def resolve_compile_enabled(
    training_config: TrainingConfig,
    *,
    device: torch.device,
    precision: str,
    family: ModelFamily,
) -> bool:
    compile_mode = training_config.compile
    if compile_mode is CompileMode.AUTO:
        enabled = device.type in {"mps", "cuda"}
    else:
        enabled = compile_mode is CompileMode.ON
    if device.type == "mps":
        return enabled and precision == "32-true" and family is ModelFamily.LSTM
    return enabled


def build_sequence_loader(
    store: TemporalDatasetStore,
    sample_indices: IntVector,
    *,
    lookback_steps: int,
    batch_size: int,
    shuffle: bool = False,
) -> SequenceBatchLoader:
    return SequenceBatchLoader(
        store,
        sample_indices,
        lookback_steps=lookback_steps,
        batch_size=batch_size,
        shuffle=shuffle,
    )
