"""JSON serialization helpers."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from .files import write_text_atomic

JsonPrimitive = None | bool | int | float | str
JsonValue = JsonPrimitive | dict[str, "JsonValue"] | list["JsonValue"]
Jsonable = (
    BaseModel
    | Path
    | JsonPrimitive
    | dict[str, "Jsonable"]
    | list["Jsonable"]
    | tuple["Jsonable", ...]
)
JsonObject = dict[str, JsonValue]


def _jsonable(payload: Jsonable) -> JsonValue:
    if isinstance(payload, BaseModel):
        return payload.model_dump(mode="json", exclude_none=True)
    if isinstance(payload, Path):
        return str(payload)
    if isinstance(payload, dict):
        return {str(key): _jsonable(value) for key, value in payload.items()}
    if isinstance(payload, (list, tuple)):
        return [_jsonable(value) for value in payload]
    return payload


def write_json(path: Path, payload: Jsonable) -> None:
    write_text_atomic(path, json.dumps(_jsonable(payload), indent=2), encoding="utf-8")
