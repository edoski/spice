"""Inference helpers for trained temporal models."""

from __future__ import annotations

from collections.abc import Sequence

import torch
from torch.utils.data import DataLoader

from spice_temporal.contracts import TemporalModel
from spice_temporal.records import SupervisedExample
from spice_temporal.torch_datasets import SequenceDataset
from spice_temporal.training import choose_microbatch_size, resolve_device


def predict_class_offsets(
    model: TemporalModel,
    *,
    examples: Sequence[SupervisedExample],
    effective_batch_size: int,
    device: str,
) -> list[int]:
    if not examples:
        raise ValueError("examples must be non-empty")

    resolved_device = resolve_device(device)
    model.to(resolved_device)
    model.eval()
    microbatch_size = choose_microbatch_size(effective_batch_size, resolved_device)
    loader = DataLoader(
        SequenceDataset(examples),
        batch_size=microbatch_size,
        shuffle=False,
    )

    predictions: list[int] = []
    with torch.no_grad():
        for batch in loader:
            logits = model(batch["inputs"].to(resolved_device)).logits
            predictions.extend(logits.argmax(dim=-1).cpu().tolist())
    return predictions
