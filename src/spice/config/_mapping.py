"""Small mapping helpers for config payload handling."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from ..core.errors import ConfigResolutionError


def mapping_copy(value: Mapping[object, object]) -> dict[str, object]:
    return {str(key): child for key, child in value.items()}


def require_mapping(raw: object, *, label: str) -> dict[str, object]:
    if not isinstance(raw, Mapping):
        raise ConfigResolutionError(f"{label} must be provided as a mapping")
    return mapping_copy(cast(Mapping[object, object], raw))
