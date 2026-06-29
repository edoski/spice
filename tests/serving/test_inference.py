from __future__ import annotations

from spice.serving.inference import _max_allowed_offset


def test_max_allowed_offset_respects_tolerance_and_action_width() -> None:
    assert _max_allowed_offset(
        max_wait_seconds=0,
        slot_spacing_seconds=12.0,
        action_width=4,
    ) == 0
    assert _max_allowed_offset(
        max_wait_seconds=24,
        slot_spacing_seconds=12.0,
        action_width=4,
    ) == 2
    assert _max_allowed_offset(
        max_wait_seconds=120,
        slot_spacing_seconds=12.0,
        action_width=4,
    ) == 3
