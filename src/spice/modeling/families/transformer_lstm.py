"""Transformer-LSTM model-family spec."""

from __future__ import annotations

import torch
from torch import nn

from ...prediction import PredictionOutputSpec
from ..models import ModelOutputs, TemporalModel
from ._heads import TemporalOutputHead
from ._sequence import take_last_valid
from ._transformer_shared import (
    SinusoidalPositionalEncoding,
    build_transformer_encoder,
)
from .base import (
    TransformerLstmCapacity,
    TransformerLstmDefinition,
    TransformerLstmMethod,
    TransformerLstmMethodSpace,
)

__all__ = [
    "TransformerLstmCapacity",
    "TransformerLstmDefinition",
    "TransformerLstmMethod",
    "TransformerLstmMethodSpace",
]


class TransformerLSTMBaseline(TemporalModel):
    def __init__(
        self,
        n_features: int,
        output_spec: PredictionOutputSpec,
        config: TransformerLstmModelConfig,
    ) -> None:
        super().__init__()
        self.input_projection = nn.Linear(n_features, config.d_model)
        self.position_encoding = SinusoidalPositionalEncoding(config.d_model)
        self.encoder = build_transformer_encoder(config)
        self.lstm = nn.LSTM(
            input_size=config.d_model,
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
        encoded = self.encoder(
            self.position_encoding(projected),
            src_key_padding_mask=~input_mask.bool(),
        )
        recurrent, _ = self.lstm(encoded)
        last_state = take_last_valid(recurrent, input_mask)
        return self.output_head(last_state)


def _build_model(
    n_features: int,
    output_spec: PredictionOutputSpec,
    config: TransformerLstmModelConfig,
) -> TemporalModel:
    return TransformerLSTMBaseline(n_features, output_spec, config)
