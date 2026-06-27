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


def sequence_runtime_metadata(
    *,
    sequence_length: int,
    median_dt_seconds: float,
    min_length: int,
    max_length: int,
) -> SequenceRuntimeMetadata:
    return SequenceRuntimeMetadata(
        sequence_length=sequence_length,
        median_dt_seconds=median_dt_seconds,
        min_length=min_length,
        max_length=max_length,
    )


def validate_feature_prerequisites(
    actual,
    expected,
) -> None:
    if actual != expected:
        raise ValueError(
            "Resolved feature prerequisites do not match the current feature graph: "
            f"expected {expected.model_dump(mode='json')}, "
            f"got {actual.model_dump(mode='json')}"
        )
