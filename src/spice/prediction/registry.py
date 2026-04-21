"""Closed dispatch for supported prediction families."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from ..core.errors import ConfigResolutionError
from .base import PredictionFamilyConfig
from .contracts import CompiledPredictionContract

if TYPE_CHECKING:
    from ..config.models import TunedPredictionParams


@dataclass(frozen=True, slots=True)
class PredictionFamilySpec:
    id: str
    config_type: type[PredictionFamilyConfig]
    compile: Callable[[str, PredictionFamilyConfig], CompiledPredictionContract]


_KNOWN_PREDICTION_FAMILIES = ("candidate_offset_selection", "min_block_fee_multitask")


def prediction_family_spec(family_id: str) -> PredictionFamilySpec:
    if family_id == "candidate_offset_selection":
        from .families.candidate_offset_selection import (
            CandidateOffsetSelectionFamilyConfig,
        )
        from .families.candidate_offset_selection import (
            compile_prediction_family as compile_candidate_offset_selection,
        )

        return PredictionFamilySpec(
            id="candidate_offset_selection",
            config_type=CandidateOffsetSelectionFamilyConfig,
            compile=cast(Any, compile_candidate_offset_selection),
        )
    if family_id == "min_block_fee_multitask":
        from .families.min_block_fee_multitask import (
            MinBlockFeeMultitaskFamilyConfig,
        )
        from .families.min_block_fee_multitask import (
            compile_prediction_family as compile_min_block_fee_multitask,
        )

        return PredictionFamilySpec(
            id="min_block_fee_multitask",
            config_type=MinBlockFeeMultitaskFamilyConfig,
            compile=cast(Any, compile_min_block_fee_multitask),
        )
    known = ", ".join(_KNOWN_PREDICTION_FAMILIES)
    raise ConfigResolutionError(
        f"Unknown prediction.family.id: {family_id}. Known values: {known}"
    )


def coerce_prediction_family_config(
    raw_config: Mapping[str, object] | PredictionFamilyConfig,
) -> PredictionFamilyConfig:
    if isinstance(raw_config, PredictionFamilyConfig):
        family_id = raw_config.id
        payload = raw_config.model_dump(mode="json")
    elif isinstance(raw_config, Mapping):
        if "id" not in raw_config:
            raise ConfigResolutionError("prediction.family.id is required")
        family_id = str(raw_config["id"])
        payload = dict(raw_config)
    else:
        raise ConfigResolutionError("prediction.family must be a mapping")
    return prediction_family_spec(family_id).config_type.model_validate(payload)


def compile_prediction_contract(
    *,
    prediction_id: str,
    family_config: PredictionFamilyConfig,
) -> CompiledPredictionContract:
    spec = prediction_family_spec(family_config.id)
    return spec.compile(prediction_id, cast(Any, family_config))


def apply_tuned_prediction_family_parameters(
    family_config: PredictionFamilyConfig,
    params: TunedPredictionParams,
) -> PredictionFamilyConfig:
    spec = prediction_family_spec(family_config.id)
    payload = family_config.model_dump(mode="json")
    updates = {
        "classification_loss_weight": params.classification_loss_weight,
        "regression_loss_weight": params.regression_loss_weight,
    }
    unsupported_fields = [
        field_name
        for field_name, value in updates.items()
        if value is not None and field_name not in spec.config_type.model_fields
    ]
    if unsupported_fields:
        joined = ", ".join(unsupported_fields)
        raise ConfigResolutionError(
            "prediction tuning fields are unsupported for "
            f"prediction.family.id={family_config.id}: {joined}"
        )
    for field_name, value in updates.items():
        if value is not None:
            payload[field_name] = value
    return spec.config_type.model_validate(payload)
