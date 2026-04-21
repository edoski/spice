"""Deterministic storage identifiers for materialized runtime objects."""

from __future__ import annotations

import json
from collections.abc import Mapping
from hashlib import sha256

_DIGEST_LENGTH = 20


def _stable_id(prefix: str, *parts: str) -> str:
    digest = sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:_DIGEST_LENGTH]
    return f"{prefix}_{digest}"


def _canonical_payload(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def corpus_storage_id(*, chain_name: str, dataset_name: str) -> str:
    return _stable_id("cor", chain_name, dataset_name)


def study_storage_id(
    *,
    identity: Mapping[str, object],
) -> str:
    return _stable_id(
        "std",
        _canonical_payload(identity),
    )


def artifact_storage_id(
    *,
    identity: Mapping[str, object],
) -> str:
    return _stable_id(
        "art",
        _canonical_payload(identity),
    )
