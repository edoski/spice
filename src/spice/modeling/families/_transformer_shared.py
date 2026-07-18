"""Shared Transformer family rules and modules."""

from __future__ import annotations

import math
from typing import Protocol, cast

import torch
from torch import nn


class SinusoidalPositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_length: int = 4096) -> None:
        super().__init__()
        position = torch.arange(max_length, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float32) * (-math.log(10000.0) / d_model)
        )
        pe = torch.zeros(max_length, d_model, dtype=torch.float32)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0), persistent=False)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        positional_encoding = cast(torch.Tensor, self.get_buffer("pe"))
        return inputs + positional_encoding[:, : inputs.size(1)]


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
