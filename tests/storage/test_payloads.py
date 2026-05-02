from __future__ import annotations

import pytest
from pydantic import RootModel, TypeAdapter

from spice.core.errors import StateLayoutError
from spice.storage.payloads import (
    PayloadModel,
    decode_payload_model,
    int_list_payload,
    model_payload,
    optional_int_payload,
    sequence_payload,
    type_adapter_value,
)


class _DemoPayload(PayloadModel):
    count: int


def test_decode_payload_model_rejects_extra_and_loose_scalars() -> None:
    with pytest.raises(StateLayoutError, match="Invalid demo payload"):
        decode_payload_model("demo", _DemoPayload, {"count": "1"}, lambda model: model)

    with pytest.raises(StateLayoutError, match="Invalid demo payload"):
        decode_payload_model(
            "demo",
            _DemoPayload,
            {"count": 1, "extra": 2},
            lambda model: model,
        )


def test_model_payload_requires_mapping_dump() -> None:
    model = RootModel[list[int]]([1, 2, 3])

    with pytest.raises(StateLayoutError, match="root must serialize to a mapping payload"):
        model_payload(model, label="root")


def test_type_adapter_value_wraps_validation_errors() -> None:
    adapter = TypeAdapter(_DemoPayload)

    with pytest.raises(StateLayoutError, match="Invalid demo payload"):
        type_adapter_value(adapter, {"count": "1"}, label="demo payload", strict=True)


def test_sequence_payload_rejects_strings_and_non_sequences() -> None:
    with pytest.raises(StateLayoutError, match="items must be a sequence"):
        sequence_payload("abc", label="items")

    with pytest.raises(StateLayoutError, match="items must be a sequence"):
        sequence_payload(1, label="items")


def test_int_list_payload_rejects_bool_items() -> None:
    with pytest.raises(StateLayoutError, match="items must be an integer"):
        int_list_payload([1, True], label="items")


def test_optional_int_payload_accepts_none_and_int() -> None:
    assert optional_int_payload(None, label="value") is None
    assert optional_int_payload(3, label="value") == 3
