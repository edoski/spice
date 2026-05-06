"""LSTM model-family spec."""

from __future__ import annotations

from typing import Literal

import torch
from pydantic import Field, field_validator, model_validator
from torch import nn

from ...prediction import PredictionOutputSpec
from ..models import ModelOutputs, TemporalModel
from ._heads import TemporalOutputHead
from ._sequence import take_last_valid
from .base import ModelConfig, ModelTuningSpaceConfig, TunableFieldSpec, TunedModelParams
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
    input_projection_dim: list[int] | None = Field(default=None, min_length=1)
    hidden_size: list[int] | None = Field(default=None, min_length=1)
    num_layers: list[int] | None = Field(default=None, min_length=1)
    head_hidden_dim: list[int] | None = Field(default=None, min_length=1)
    dropout: list[float] | None = Field(default=None, min_length=1)

    @field_validator("input_projection_dim", "hidden_size", "num_layers", "head_hidden_dim")
    @classmethod
    def validate_int_candidates(cls, values: list[int] | None) -> list[int] | None:
        if values is not None and any(value <= 0 for value in values):
            raise ValueError("tuning_space.model integer candidates must be positive")
        return values

    @field_validator("dropout")
    @classmethod
    def validate_dropout_candidates(cls, values: list[float] | None) -> list[float] | None:
        if values is not None and any(value < 0.0 or value >= 1.0 for value in values):
            raise ValueError("tuning_space.model.dropout values must be in [0.0, 1.0)")
        return values


class LstmTunedModelParams(TunedModelParams[Literal["lstm"]]):
    id: Literal["lstm"] = "lstm"
    input_projection_dim: int | None = Field(default=None, gt=0)
    hidden_size: int | None = Field(default=None, gt=0)
    num_layers: int | None = Field(default=None, gt=0)
    head_hidden_dim: int | None = Field(default=None, gt=0)
    dropout: float | None = Field(default=None, ge=0.0, lt=1.0)

    @model_validator(mode="after")
    def validate_non_empty_group(self) -> LstmTunedModelParams:
        if (
            self.input_projection_dim is None
            and self.hidden_size is None
            and self.num_layers is None
            and self.head_hidden_dim is None
            and self.dropout is None
        ):
            raise ValueError("tuned model params must declare at least one field")
        return self


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
