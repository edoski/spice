"""Internal PyTorch runtime helpers shared by training and inference."""

from __future__ import annotations

import random

import numpy as np
import torch
from numpy.typing import NDArray

from ..core.config import CompileMode, ModelConfig, TrainingConfig, TrainingPrecision
from ..data.datasets import TemporalDatasetStore
from .registry import resolve_auto_compile, resolve_default_precision
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
    model_config: ModelConfig,
) -> str:
    precision = training_config.precision
    if precision is TrainingPrecision.AUTO:
        precision = resolve_default_precision(model_config.id, device)

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
    model_config: ModelConfig,
) -> bool:
    compile_mode = training_config.compile
    if compile_mode is CompileMode.AUTO:
        enabled = device.type in {"mps", "cuda"}
    else:
        enabled = compile_mode is CompileMode.ON
    if not enabled:
        return False
    return resolve_auto_compile(model_config.id, device, precision)


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
