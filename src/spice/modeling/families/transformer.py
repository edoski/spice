"""Transformer model-family spec."""

from __future__ import annotations

from typing import Literal

import torch
from pydantic import Field, field_validator, model_validator
from torch import nn

from ...prediction import PredictionOutputSpec
from ..models import ModelOutputs, TemporalModel
from ._heads import TemporalOutputHead
from ._sequence import take_last_valid
from ._transformer_shared import (
    SinusoidalPositionalEncoding,
    build_transformer_encoder,
    derive_feedforward_dim_from_multiplier,
    validate_transformer_dimensions,
    validate_transformer_tuning_space,
)
from .base import (
    ModelConfig,
    ModelTuningSpaceConfig,
    TunableFieldSpec,
    TunedModelParams,
)
from .registry import ModelSpec


class TransformerModelConfig(ModelConfig[Literal["transformer"]]):
    id: Literal["transformer"] = "transformer"
    dropout: float = Field(ge=0.0, lt=1.0)
    d_model: int = Field(gt=0)
    nhead: int = Field(gt=0)
    transformer_layers: int = Field(gt=0)
    feedforward_dim: int = Field(gt=0)
    head_hidden_dim: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_transformer_dimensions(self) -> TransformerModelConfig:
        validate_transformer_dimensions(self)
        return self


class TransformerTuningSpaceModelConfig(ModelTuningSpaceConfig[Literal["transformer"]]):
    id: Literal["transformer"] = "transformer"
    d_model: list[int] | None = Field(default=None, min_length=1)
    nhead: list[int] | None = Field(default=None, min_length=1)
    transformer_layers: list[int] | None = Field(default=None, min_length=1)
    feedforward_multiplier: list[int] | None = Field(default=None, min_length=1)
    head_hidden_dim: list[int] | None = Field(default=None, min_length=1)
    dropout: list[float] | None = Field(default=None, min_length=1)

    @field_validator(
        "d_model",
        "nhead",
        "transformer_layers",
        "feedforward_multiplier",
        "head_hidden_dim",
    )
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


class TransformerTunedModelParams(TunedModelParams[Literal["transformer"]]):
    id: Literal["transformer"] = "transformer"
    d_model: int | None = Field(default=None, gt=0)
    nhead: int | None = Field(default=None, gt=0)
    transformer_layers: int | None = Field(default=None, gt=0)
    feedforward_dim: int | None = Field(default=None, gt=0)
    head_hidden_dim: int | None = Field(default=None, gt=0)
    dropout: float | None = Field(default=None, ge=0.0, lt=1.0)

    @model_validator(mode="after")
    def validate_non_empty_group(self) -> TransformerTunedModelParams:
        if (
            self.d_model is None
            and self.nhead is None
            and self.transformer_layers is None
            and self.feedforward_dim is None
            and self.head_hidden_dim is None
            and self.dropout is None
        ):
            raise ValueError("tuned model params must declare at least one field")
        return self


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


def _validate_tuning_space(
    model_config: TransformerModelConfig,
    tuning_space: TransformerTuningSpaceModelConfig,
) -> None:
    validate_transformer_tuning_space(model_config, tuning_space)


MODEL_SPEC = ModelSpec(
    model_config_type=TransformerModelConfig,
    tuning_space_type=TransformerTuningSpaceModelConfig,
    tuned_params_type=TransformerTunedModelParams,
    build_model=_build_model,
    validate_tuning_space=_validate_tuning_space,
    tunable_fields=(
        TunableFieldSpec("d_model", int),
        TunableFieldSpec("nhead", int),
        TunableFieldSpec("transformer_layers", int),
        TunableFieldSpec("feedforward_multiplier", int),
        TunableFieldSpec("head_hidden_dim", int),
        TunableFieldSpec("dropout", float),
    ),
    derive_tuned_values=derive_feedforward_dim_from_multiplier,
)
