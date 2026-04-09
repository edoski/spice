"""Inference helpers for trained temporal models."""

from __future__ import annotations

import numpy as np
import torch
from numpy.typing import NDArray
from torch.utils.data import DataLoader

from spice_temporal.contracts import TemporalModel
from spice_temporal.datasets import TemporalDatasetStore
from spice_temporal.torch_datasets import SequenceDataset
from spice_temporal.training import choose_microbatch_size, resolve_device

IntVector = NDArray[np.int64]


def predict_class_offsets(
    model: TemporalModel,
    *,
    store: TemporalDatasetStore,
    sample_indices: IntVector,
    lookback_steps: int,
    effective_batch_size: int,
    device: str,
) -> list[int]:
    if sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")

    resolved_device = resolve_device(device)
    model.to(resolved_device)
    model.eval()
    microbatch_size = choose_microbatch_size(effective_batch_size, resolved_device)
    loader = DataLoader(
        SequenceDataset(store, sample_indices, lookback_steps=lookback_steps),
        batch_size=microbatch_size,
        shuffle=False,
    )

    predictions: list[int] = []
    with torch.no_grad():
        for batch in loader:
            logits = model(batch["inputs"].to(resolved_device)).logits
            predictions.extend(logits.argmax(dim=-1).cpu().tolist())
    return predictions
