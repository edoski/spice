"""Temporal capability carried by trained artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..core.validation import validate_path_segment


@dataclass(frozen=True, slots=True)
class TemporalCapabilitySemantics:
    """Stable semantic projection of the trained artifact's temporal capability."""

    compiler_id: str
    max_delay_seconds: int
    action_width: int


@dataclass(frozen=True, slots=True)
class TemporalCapability:
    compiler_id: str
    max_delay_seconds: int
    action_width: int
    compiler_runtime_metadata: object

    def __post_init__(self) -> None:
        validate_path_segment(self.compiler_id, label="temporal_capability.compiler_id")
        if self.max_delay_seconds <= 0:
            raise ValueError("temporal_capability.max_delay_seconds must be positive")
        if self.action_width <= 0:
            raise ValueError("temporal_capability.action_width must be positive")

    @property
    def semantics(self) -> TemporalCapabilitySemantics:
        return TemporalCapabilitySemantics(
            compiler_id=self.compiler_id,
            max_delay_seconds=self.max_delay_seconds,
            action_width=self.action_width,
        )


def temporal_capability_payload(capability: TemporalCapability) -> dict[str, object]:
    from .compilers import problem_runtime_metadata_payload

    return {
        "compiler_id": capability.compiler_id,
        "max_delay_seconds": capability.max_delay_seconds,
        "action_width": capability.action_width,
        "compiler_runtime_metadata": problem_runtime_metadata_payload(
            capability.compiler_id,
            capability.compiler_runtime_metadata,
        ),
    }


def temporal_capability_from_payload(payload: Mapping[str, object]) -> TemporalCapability:
    from .compilers import problem_runtime_metadata_from_compiler_payload

    compiler_id = _string_payload(payload, "compiler_id")
    return TemporalCapability(
        compiler_id=compiler_id,
        max_delay_seconds=_int_payload(payload, "max_delay_seconds"),
        action_width=_int_payload(payload, "action_width"),
        compiler_runtime_metadata=problem_runtime_metadata_from_compiler_payload(
            compiler_id,
            _mapping_payload(payload, "compiler_runtime_metadata"),
        ),
    )


def _mapping_payload(payload: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = payload[key]
    if not isinstance(value, dict):
        raise ValueError(f"temporal_capability.{key} must be a mapping")
    return {str(item_key): item_value for item_key, item_value in value.items()}


def _string_payload(payload: Mapping[str, object], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise ValueError(f"temporal_capability.{key} must be a string")
    return value


def _int_payload(payload: Mapping[str, object], key: str) -> int:
    value = payload[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"temporal_capability.{key} must be an integer")
    return value
