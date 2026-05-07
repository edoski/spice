from __future__ import annotations

import pytest
from pydantic import RootModel, TypeAdapter

from spice.core.errors import StateLayoutError
from spice.storage.payloads import (
    PayloadRecord,
    decode_payload_record,
    mapping_model_payload,
    type_adapter_value,
)


class _DemoPayload(PayloadRecord):
    count: int


def test_decode_payload_record_rejects_extra_and_loose_scalars() -> None:
    with pytest.raises(StateLayoutError, match="Invalid demo payload"):
        decode_payload_record("demo", _DemoPayload, {"count": "1"}, lambda model: model)

    with pytest.raises(StateLayoutError, match="Invalid demo payload"):
        decode_payload_record(
            "demo",
            _DemoPayload,
            {"count": 1, "extra": 2},
            lambda model: model,
        )


def test_mapping_model_payload_requires_mapping_dump() -> None:
    model = RootModel[list[int]]([1, 2, 3])

    with pytest.raises(StateLayoutError, match="root must serialize to a mapping payload"):
        mapping_model_payload(model, label="root")


def test_type_adapter_value_wraps_validation_errors() -> None:
    adapter = TypeAdapter(_DemoPayload)

    with pytest.raises(StateLayoutError, match="Invalid demo payload"):
        type_adapter_value(adapter, {"count": "1"}, label="demo payload", strict=True)
