"""Shared model-family output heads."""

from __future__ import annotations

import torch
from torch import nn

from ...prediction import PredictionOutputSpec
from ..models import ModelOutputs


class MLPHead(nn.Module):
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        *,
        dropout: float,
    ) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.layers(inputs)


class TemporalOutputHead(nn.Module):
    def __init__(
        self,
        hidden_dim: int,
        output_spec: PredictionOutputSpec,
        head_hidden_dim: int,
        *,
        dropout: float,
    ) -> None:
        super().__init__()
        self.heads = nn.ModuleDict(
            {
                head.id: MLPHead(
                    hidden_dim,
                    head_hidden_dim,
                    head.size,
                    dropout=dropout,
                )
                for head in output_spec.heads
            }
        )

    def forward(self, encoded: torch.Tensor) -> ModelOutputs:
        return ModelOutputs(
            heads={head_id: head(encoded) for head_id, head in self.heads.items()}
        )
