"""Shared base types for model-family configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any, Generic, Self, TypeAlias, TypeVar

from pydantic import AfterValidator, Field, field_validator, model_validator

from ...core.config_model import ConfigModel as _ConfigModel
from ...core.validation import validate_path_segment

ModelIdT = TypeVar("ModelIdT", bound=str)
TunedScalar: TypeAlias = int | float
TunableScalarType: TypeAlias = type[int] | type[float]


def _validate_positive_int_candidates(values: list[int] | None) -> list[int] | None:
    if values is not None and any(value <= 0 for value in values):
        raise ValueError("tuning_space.model integer candidates must be positive")
    return values


def _validate_dropout_candidates(values: list[float] | None) -> list[float] | None:
    if values is not None and any(value < 0.0 or value >= 1.0 for value in values):
        raise ValueError("tuning_space.model.dropout values must be in [0.0, 1.0)")
    return values


PositiveIntTuningCandidates: TypeAlias = Annotated[
    list[int] | None,
    Field(min_length=1),
    AfterValidator(_validate_positive_int_candidates),
]
DropoutTuningCandidates: TypeAlias = Annotated[
    list[float] | None,
    Field(min_length=1),
    AfterValidator(_validate_dropout_candidates),
]


@dataclass(frozen=True, slots=True)
class TunableFieldSpec:
    name: str
    value_type: TunableScalarType

    @property
    def parameter_name(self) -> str:
        return f"model.{self.name}"

    def coerce_sample(self, value: Any) -> TunedScalar:
        return self.value_type(value)


class ModelConfig(_ConfigModel, Generic[ModelIdT]):
    id: ModelIdT

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return validate_path_segment(value, label="model.id")


class ModelTuningSpaceConfig(_ConfigModel, Generic[ModelIdT]):
    id: ModelIdT

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return validate_path_segment(value, label="tuning_space.model.id")


class TunedModelParams(_ConfigModel, Generic[ModelIdT]):
    id: ModelIdT

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return validate_path_segment(value, label="tuned model params id")

    @model_validator(mode="after")
    def validate_non_empty_group(self) -> Self:
        if not self.model_dump(exclude={"id"}, exclude_none=True):
            raise ValueError("tuned model params must declare at least one field")
        return self
