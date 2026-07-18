"""Shared Transformer family rules and modules."""

from __future__ import annotations

import math
from typing import Protocol

import torch
from torch import nn


def add_sinusoidal_positions(inputs: torch.Tensor) -> torch.Tensor:
    sequence_length = inputs.size(1)
    model_width = inputs.size(2)
    position = torch.arange(
        sequence_length,
        dtype=inputs.dtype,
        device=inputs.device,
    ).unsqueeze(1)
    div_term = torch.exp(
        torch.arange(
            0,
            model_width,
            2,
            dtype=inputs.dtype,
            device=inputs.device,
        )
        * (-math.log(10000.0) / model_width)
    )
    encoding = torch.zeros(
        sequence_length,
        model_width,
        dtype=inputs.dtype,
        device=inputs.device,
    )
    encoding[:, 0::2] = torch.sin(position * div_term)
    encoding[:, 1::2] = torch.cos(position * div_term)
    return inputs + encoding.unsqueeze(0)


class TransformerEncoderConfig(Protocol):
    d_model: int
    nhead: int
    feedforward_dim: int
    dropout: float
    transformer_layers: int


def build_transformer_encoder(config: TransformerEncoderConfig) -> nn.TransformerEncoder:
    encoder_layer = nn.TransformerEncoderLayer(
        d_model=config.d_model,
        nhead=config.nhead,
        dim_feedforward=config.feedforward_dim,
        dropout=config.dropout,
        activation="gelu",
        batch_first=True,
    )
    return nn.TransformerEncoder(encoder_layer, num_layers=config.transformer_layers)
