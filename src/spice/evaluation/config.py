"""Evaluation config models."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..core.validation import validate_path_segment


class EvaluationConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class EvaluationSampler(StrEnum):
    FULLSET = "fullset"
    POISSON_ARRIVALS = "poisson_arrivals"


class EvaluationAggregationId(StrEnum):
    EVENT_MEAN = "event_mean"
    TOTAL_RATIO = "total_ratio"


class EvaluationAggregationConfig(EvaluationConfigModel):
    id: EvaluationAggregationId


class EvaluatorConfig(EvaluationConfigModel):
    id: str
    engine: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return validate_path_segment(value, label="evaluation.id")


class ReplayEvaluatorConfig(EvaluatorConfig):
    engine: str = "replay"
    sampler: EvaluationSampler | None = None
    window_seconds: int | None = Field(default=None, gt=0)
    repetitions: int | None = Field(default=None, gt=0)
    seed: int | None = Field(default=None, ge=0)
    arrival_rate_per_second: float | None = Field(default=None, gt=0.0)
    aggregation: EvaluationAggregationConfig | None = None

    @property
    def aggregation_id(self) -> EvaluationAggregationId:
        if self.aggregation is None:
            raise ValueError("Missing required field: evaluation.aggregation")
        return self.aggregation.id

    @model_validator(mode="after")
    def validate_sampler_fields(self) -> Self:
        if self.engine != "replay":
            raise ValueError("evaluation.engine must be replay")
        if self.sampler is None:
            raise ValueError("Missing required fields: evaluation.sampler")
        _require_present(
            self.aggregation,
            labels=("evaluation.aggregation",),
        )
        if self.sampler is EvaluationSampler.FULLSET:
            _require_absent(
                self.window_seconds,
                self.repetitions,
                self.seed,
                self.arrival_rate_per_second,
                labels=(
                    "evaluation.window_seconds",
                    "evaluation.repetitions",
                    "evaluation.seed",
                    "evaluation.arrival_rate_per_second",
                ),
            )
            return self
        _require_present(
            self.window_seconds,
            self.repetitions,
            self.seed,
            self.arrival_rate_per_second,
            labels=(
                "evaluation.window_seconds",
                "evaluation.repetitions",
                "evaluation.seed",
                "evaluation.arrival_rate_per_second",
            ),
        )
        return self


class ZeroStopRolloutEvaluatorConfig(EvaluatorConfig):
    engine: str = "zero_stop_rollout"

    @model_validator(mode="after")
    def validate_engine(self) -> Self:
        if self.engine != "zero_stop_rollout":
            raise ValueError("evaluation.engine must be zero_stop_rollout")
        return self


class AnchorBasefeeEvaluatorConfig(EvaluatorConfig):
    engine: str = "anchor_basefee"

    @model_validator(mode="after")
    def validate_engine(self) -> Self:
        if self.engine != "anchor_basefee":
            raise ValueError("evaluation.engine must be anchor_basefee")
        return self


def _require_present(*values: object, labels: tuple[str, ...]) -> None:
    missing = [label for label, value in zip(labels, values, strict=True) if value is None]
    if missing:
        raise ValueError("Missing required fields: " + ", ".join(missing))


def _require_absent(*values: object, labels: tuple[str, ...]) -> None:
    unexpected = [label for label, value in zip(labels, values, strict=True) if value is not None]
    if unexpected:
        raise ValueError("Unexpected fields for evaluation sampler: " + ", ".join(unexpected))
