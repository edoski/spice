"""Shared sequence-dataset preparation helpers."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ...core.config_model import ConfigModel


class SequenceRuntimeMetadata(ConfigModel):
    sequence_length: int = Field(gt=0)
    median_dt_seconds: float = Field(gt=0.0)
    min_length: int = Field(gt=0)
    max_length: int = Field(gt=0)
    split_strategy: Literal["global_feature_table"] = "global_feature_table"

    @model_validator(mode="after")
    def validate_sequence_bounds(self) -> SequenceRuntimeMetadata:
        if self.max_length < self.min_length:
            raise ValueError("max_length must be >= min_length")
        if not self.min_length <= self.sequence_length <= self.max_length:
            raise ValueError("sequence_length must be within configured bounds")
        return self
