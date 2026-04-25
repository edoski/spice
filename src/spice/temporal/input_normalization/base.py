"""Input-normalization seam types."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

from pydantic import field_validator

from ...core.specs import lookup_local_spec, require_mapping_id
from ...core.validation import validate_path_segment
from ...modeling.families.base import ConfigModel
from ...semantics import InputNormalizationSemantics
from ..scaling import FloatMatrix, IntVector, ScalerStats


class InputNormalizationConfig(ConfigModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return validate_path_segment(value, label="training.input_normalization.id")


class FitScalerFn(Protocol):
    def __call__(
        self,
        feature_matrix: FloatMatrix,
        *,
        context_start_rows: IntVector,
        anchor_rows: IntVector,
        sample_indices: IntVector,
    ) -> ScalerStats: ...


@dataclass(frozen=True, slots=True)
class CompiledInputNormalizationContract:
    input_normalization_id: str
    fit_scaler_fn: FitScalerFn

    @property
    def semantics(self) -> InputNormalizationSemantics:
        return InputNormalizationSemantics(
            input_normalization_id=self.input_normalization_id,
        )

    def fit_scaler(
        self,
        feature_matrix: FloatMatrix,
        *,
        context_start_rows: IntVector,
        anchor_rows: IntVector,
        sample_indices: IntVector,
    ) -> ScalerStats:
        return self.fit_scaler_fn(
            feature_matrix,
            context_start_rows=context_start_rows,
            anchor_rows=anchor_rows,
            sample_indices=sample_indices,
    )


@dataclass(frozen=True, slots=True)
class InputNormalizationSpec:
    config_type: type[InputNormalizationConfig]
    compile_contract: Callable[[InputNormalizationConfig], CompiledInputNormalizationContract]


def _compile_row_standard(
    config: InputNormalizationConfig,
) -> CompiledInputNormalizationContract:
    from .row_standard import RowStandardConfig, compile_input_normalization

    return compile_input_normalization(RowStandardConfig.model_validate(config))


def _compile_window_weighted_standard(
    config: InputNormalizationConfig,
) -> CompiledInputNormalizationContract:
    from .window_weighted_standard import (
        WindowWeightedStandardConfig,
        compile_input_normalization,
    )

    return compile_input_normalization(WindowWeightedStandardConfig.model_validate(config))


def _input_normalization_specs() -> dict[str, InputNormalizationSpec]:
    from .row_standard import RowStandardConfig
    from .window_weighted_standard import WindowWeightedStandardConfig

    return {
        "row_standard": InputNormalizationSpec(
            config_type=RowStandardConfig,
            compile_contract=_compile_row_standard,
        ),
        "window_weighted_standard": InputNormalizationSpec(
            config_type=WindowWeightedStandardConfig,
            compile_contract=_compile_window_weighted_standard,
        ),
    }


def input_normalization_spec(normalization_id: str) -> InputNormalizationSpec:
    return lookup_local_spec(
        _input_normalization_specs(),
        normalization_id,
        "training.input_normalization.id",
    )


def coerce_input_normalization_config(
    payload: Mapping[str, object] | InputNormalizationConfig,
) -> InputNormalizationConfig:
    if isinstance(payload, InputNormalizationConfig):
        raw_payload = payload.model_dump(mode="json")
        normalization_id = payload.id
    elif isinstance(payload, Mapping):
        raw_payload = dict(payload)
        normalization_id = require_mapping_id(raw_payload, "training.input_normalization.id")
    else:
        raise TypeError("training.input_normalization must be a mapping or config model")
    return input_normalization_spec(normalization_id).config_type.model_validate(raw_payload)


def compile_input_normalization_contract(
    config: InputNormalizationConfig,
) -> CompiledInputNormalizationContract:
    return input_normalization_spec(config.id).compile_contract(config)
