"""Legacy observed-window config and runtime-metadata decoding."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from pydantic import SerializeAsAny, field_validator

from ...core.config_model import ConfigModel
from ...core.specs import coerce_spec_config, lookup_local_spec
from ...core.validation import validate_path_segment
from .base import ProblemCompilerConfig


class ObservedTimeWindowSlotSpacingConfig(ConfigModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return validate_path_segment(value, label="observed_time_window.slot_spacing.id")


class ObservedTimeWindowNominalSlotSpacingConfig(ObservedTimeWindowSlotSpacingConfig):
    id: str = "nominal"

    @field_validator("id")
    @classmethod
    def validate_nominal_id(cls, value: str) -> str:
        value = ObservedTimeWindowSlotSpacingConfig.validate_id(value)
        if value != "nominal":
            raise ValueError("observed_time_window.slot_spacing.id must be nominal")
        return value


class ObservedTimeWindowRecentMedianSlotSpacingConfig(
    ObservedTimeWindowSlotSpacingConfig
):
    id: str = "recent_median"

    @field_validator("id")
    @classmethod
    def validate_recent_median_id(cls, value: str) -> str:
        value = ObservedTimeWindowSlotSpacingConfig.validate_id(value)
        if value != "recent_median":
            raise ValueError("observed_time_window.slot_spacing.id must be recent_median")
        return value


_SLOT_SPACING_CONFIG_TYPES: dict[str, type[ObservedTimeWindowSlotSpacingConfig]] = {
    "nominal": ObservedTimeWindowNominalSlotSpacingConfig,
    "recent_median": ObservedTimeWindowRecentMedianSlotSpacingConfig,
}


def _slot_spacing_config_type(
    slot_spacing_id: str,
) -> type[ObservedTimeWindowSlotSpacingConfig]:
    return lookup_local_spec(
        _SLOT_SPACING_CONFIG_TYPES,
        slot_spacing_id,
        "observed_time_window.slot_spacing.id",
    )


class ObservedTimeWindowCompilerConfig(ProblemCompilerConfig):
    id: str = "observed_time_window"
    slot_spacing: SerializeAsAny[ObservedTimeWindowSlotSpacingConfig]

    @field_validator("id")
    @classmethod
    def validate_observed_time_window_id(cls, value: str) -> str:
        value = ProblemCompilerConfig.validate_id(value)
        if value != "observed_time_window":
            raise ValueError("problem.compiler.id must be observed_time_window")
        return value

    @field_validator("slot_spacing", mode="before")
    @classmethod
    def validate_slot_spacing(
        cls,
        value: object,
    ) -> ObservedTimeWindowSlotSpacingConfig:
        return coerce_spec_config(
            value,
            owner="observed_time_window.slot_spacing",
            base_config_type=ObservedTimeWindowSlotSpacingConfig,
            id_label="observed_time_window.slot_spacing.id",
            lookup_spec=_slot_spacing_config_type,
            spec_config_type=lambda config_type: config_type,
        )


@dataclass(frozen=True, slots=True)
class ObservedTimeWindowRuntimeMetadata:
    slot_spacing_id: str
    slot_spacing_seconds: float


def runtime_metadata_from_payload(
    payload: Mapping[str, object],
) -> ObservedTimeWindowRuntimeMetadata:
    raw_payload = dict(payload)
    return ObservedTimeWindowRuntimeMetadata(
        slot_spacing_id=_str_payload(raw_payload, "slot_spacing_id"),
        slot_spacing_seconds=_float_payload(raw_payload, "slot_spacing_seconds"),
    )


def _float_payload(payload: Mapping[str, object], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"Invalid float runtime metadata field: {key}")
    return float(value)


def _str_payload(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"Invalid string runtime metadata field: {key}")
    return value
