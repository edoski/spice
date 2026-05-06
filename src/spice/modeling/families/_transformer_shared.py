"""Shared Transformer family rules and modules."""

from __future__ import annotations

import math
from typing import Protocol, cast

import torch
from torch import nn

from .base import TunedScalar


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


class TransformerTuningSpaceConfig(Protocol):
    d_model: list[int] | None
    nhead: list[int] | None
    feedforward_multiplier: list[int] | None


def validate_transformer_dimensions(config: TransformerEncoderConfig) -> None:
    if config.d_model % config.nhead != 0:
        raise ValueError("d_model must be divisible by nhead")
    if config.d_model % 2 != 0:
        raise ValueError("d_model must be even for sinusoidal positional encodings")


def validate_transformer_tuning_space(
    model_config: TransformerEncoderConfig,
    tuning_space: TransformerTuningSpaceConfig,
) -> None:
    d_model_values = tuning_space.d_model or [model_config.d_model]
    nhead_values = tuning_space.nhead or [model_config.nhead]
    for d_model in d_model_values:
        if d_model % 2 != 0:
            raise ValueError("tuning_space.model.d_model values must be even")
        for nhead in nhead_values:
            if d_model % nhead != 0:
                raise ValueError(
                    "tuning_space.model d_model values must be divisible by nhead values"
                )
    if tuning_space.feedforward_multiplier is not None and tuning_space.d_model is None:
        raise ValueError("tuning_space.model.feedforward_multiplier requires d_model")


def derive_feedforward_dim_from_multiplier(
    sampled: dict[str, TunedScalar],
) -> dict[str, TunedScalar]:
    values = dict(sampled)
    multiplier = values.pop("feedforward_multiplier", None)
    if multiplier is not None:
        d_model = values.get("d_model")
        if d_model is None:
            raise ValueError("tuning_space.model.feedforward_multiplier requires d_model")
        values["feedforward_dim"] = int(d_model) * int(multiplier)
    return values


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
