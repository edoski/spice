"""LSTM model-family spec."""

from __future__ import annotations

import torch
from torch import nn

from ...prediction import PredictionOutputSpec
from ..models import ModelOutputs, TemporalModel
from ._heads import TemporalOutputHead
from ._sequence import take_last_valid
from .base import (
    LstmCapacity,
    LstmDefinition,
    LstmMethod,
    LstmMethodSpace,
)

__all__ = [
    "LstmCapacity",
    "LstmDefinition",
    "LstmMethod",
    "LstmMethodSpace",
]


class LSTMBaseline(TemporalModel):
    def __init__(
        self,
        n_features: int,
        output_spec: PredictionOutputSpec,
        config: LstmModelConfig,
    ) -> None:
        super().__init__()
        self.input_projection = nn.Linear(n_features, config.input_projection_dim)
        self.backbone = nn.LSTM(
            input_size=config.input_projection_dim,
            hidden_size=config.hidden_size,
            num_layers=config.num_layers,
            dropout=config.dropout if config.num_layers > 1 else 0.0,
            batch_first=True,
        )
        self.output_head = TemporalOutputHead(
            config.hidden_size,
            output_spec,
            config.head_hidden_dim,
            dropout=config.dropout,
        )

    def forward(self, inputs: torch.Tensor, input_mask: torch.Tensor) -> ModelOutputs:
        projected = self.input_projection(inputs)
        recurrent, _ = self.backbone(projected)
        last_state = take_last_valid(recurrent, input_mask)
        return self.output_head(last_state)


def _build_model(
    n_features: int,
    output_spec: PredictionOutputSpec,
    config: LstmModelConfig,
) -> TemporalModel:
    return LSTMBaseline(n_features, output_spec, config)
