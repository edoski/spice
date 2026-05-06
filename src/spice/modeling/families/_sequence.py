"""Shared sequence hidden-state helpers."""

from __future__ import annotations

import torch


def sequence_lengths_from_mask(input_mask: torch.Tensor) -> torch.Tensor:
    lengths = input_mask.to(dtype=torch.int64).sum(dim=1)
    if torch.any(lengths <= 0):
        raise ValueError("input_mask must contain at least one valid timestep per sample")
    return lengths


def take_last_valid(encoded: torch.Tensor, input_mask: torch.Tensor) -> torch.Tensor:
    lengths = sequence_lengths_from_mask(input_mask)
    last_positions = (lengths - 1).to(device=encoded.device)
    batch_indices = torch.arange(encoded.size(0), device=encoded.device)
    return encoded[batch_indices, last_positions]
