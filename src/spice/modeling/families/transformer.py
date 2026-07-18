"""Transformer model-family spec."""

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
    TransformerCapacity,
    TransformerDefinition,
    TransformerMethod,
    TransformerMethodSpace,
)

__all__ = [
    "TransformerCapacity",
    "TransformerDefinition",
    "TransformerMethod",
    "TransformerMethodSpace",
]


class TransformerBaseline(TemporalModel):
    def __init__(
        self,
        n_features: int,
        output_spec: PredictionOutputSpec,
        config: TransformerModelConfig,
    ) -> None:
        super().__init__()
        self.input_projection = nn.Linear(n_features, config.d_model)
        self.position_encoding = SinusoidalPositionalEncoding(config.d_model)
        self.encoder = build_transformer_encoder(config)
        self.output_head = TemporalOutputHead(
            config.d_model,
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
        return self.output_head(take_last_valid(encoded, input_mask))


def _build_model(
    n_features: int,
    output_spec: PredictionOutputSpec,
    config: TransformerModelConfig,
) -> TemporalModel:
    return TransformerBaseline(n_features, output_spec, config)
