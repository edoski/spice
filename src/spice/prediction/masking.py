"""Shared prediction logit masking helpers."""

from __future__ import annotations

import torch


def masked_distribution_logits(logits: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    """Mask logits used by probabilistic losses and metrics."""

    if logits.shape != mask.shape:
        raise ValueError(f"logits and mask shapes must match: {logits.shape} != {mask.shape}")
    if mask.ndim == 0:
        raise ValueError("mask must have at least one dimension")
    if not torch.all(mask.any(dim=-1)):
        raise ValueError("mask must allow at least one candidate per row")
    return logits.masked_fill(~mask, torch.finfo(logits.dtype).min)
