from __future__ import annotations

import pytest

from spice.temporal import (
    TemporalCapability,
    temporal_capability_from_payload,
    temporal_capability_payload,
)
from spice.temporal.compilers.observed_time_window import ObservedTimeWindowRuntimeMetadata


def _capability() -> TemporalCapability:
    return TemporalCapability(
        compiler_id="observed_time_window",
        max_delay_seconds=36,
        action_width=4,
        compiler_runtime_metadata=ObservedTimeWindowRuntimeMetadata(
            slot_spacing_id="nominal",
            slot_spacing_seconds=12.0,
        ),
    )


def test_temporal_capability_semantics_projects_authoritative_delay_and_width() -> None:
    semantics = _capability().semantics

    assert semantics.compiler_id == "observed_time_window"
    assert semantics.max_delay_seconds == 36
    assert semantics.action_width == 4


def test_temporal_capability_payload_round_trips_compiler_metadata() -> None:
    capability = _capability()

    assert temporal_capability_from_payload(
        temporal_capability_payload(capability)
    ) == capability


def test_temporal_capability_payload_rejects_malformed_values() -> None:
    payload = temporal_capability_payload(_capability())
    payload["action_width"] = True

    with pytest.raises(ValueError, match="action_width"):
        temporal_capability_from_payload(payload)
