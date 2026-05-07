"""LSTM model-family spec."""

from __future__ import annotations

from typing import Literal

import torch
from pydantic import Field
from torch import nn

from ...prediction import PredictionOutputSpec
from ..models import ModelOutputs, TemporalModel
from ._heads import TemporalOutputHead
from ._sequence import take_last_valid
from .base import (
    DropoutTuningCandidates,
    ModelConfig,
    ModelTuningSpaceConfig,
    PositiveIntTuningCandidates,
    TunableFieldSpec,
    TunedModelParams,
)
from .registry import ModelSpec


class LstmModelConfig(ModelConfig[Literal["lstm"]]):
    id: Literal["lstm"] = "lstm"
    input_projection_dim: int = Field(gt=0)
    hidden_size: int = Field(gt=0)
    num_layers: int = Field(gt=0)
    dropout: float = Field(ge=0.0, lt=1.0)
    head_hidden_dim: int = Field(gt=0)


class LstmTuningSpaceModelConfig(ModelTuningSpaceConfig[Literal["lstm"]]):
    id: Literal["lstm"] = "lstm"
    input_projection_dim: PositiveIntTuningCandidates = None
    hidden_size: PositiveIntTuningCandidates = None
    num_layers: PositiveIntTuningCandidates = None
    head_hidden_dim: PositiveIntTuningCandidates = None
    dropout: DropoutTuningCandidates = None


class LstmTunedModelParams(TunedModelParams[Literal["lstm"]]):
    id: Literal["lstm"] = "lstm"
    input_projection_dim: int | None = Field(default=None, gt=0)
    hidden_size: int | None = Field(default=None, gt=0)
    num_layers: int | None = Field(default=None, gt=0)
    head_hidden_dim: int | None = Field(default=None, gt=0)
    dropout: float | None = Field(default=None, ge=0.0, lt=1.0)

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


MODEL_SPEC = ModelSpec(
    model_config_type=LstmModelConfig,
    tuning_space_type=LstmTuningSpaceModelConfig,
    tuned_params_type=LstmTunedModelParams,
    build_model=_build_model,
    tunable_fields=(
        TunableFieldSpec("input_projection_dim", int),
        TunableFieldSpec("hidden_size", int),
        TunableFieldSpec("num_layers", int),
        TunableFieldSpec("head_hidden_dim", int),
        TunableFieldSpec("dropout", float),
    ),
)
