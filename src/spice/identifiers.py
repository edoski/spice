"""Deterministic storage identifiers for materialized runtime objects."""

from __future__ import annotations

from hashlib import sha256

_DIGEST_LENGTH = 20


def _stable_id(prefix: str, *parts: str) -> str:
    digest = sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:_DIGEST_LENGTH]
    return f"{prefix}_{digest}"


def dataset_storage_id(*, chain_name: str, dataset_name: str) -> str:
    return _stable_id("dst", chain_name, dataset_name)


def study_storage_id(
    *,
    chain_name: str,
    dataset_id: str,
    feature_set_name: str,
    model_name: str,
    task_name: str,
    study_name: str,
) -> str:
    return _stable_id(
        "std",
        chain_name,
        dataset_id,
        feature_set_name,
        model_name,
        task_name,
        study_name,
    )


def artifact_storage_id(
    *,
    chain_name: str,
    dataset_id: str,
    feature_set_name: str,
    model_name: str,
    task_name: str,
    variant: str,
    study_id: str | None = None,
) -> str:
    return _stable_id(
        "art",
        chain_name,
        dataset_id,
        feature_set_name,
        model_name,
        task_name,
        variant,
        "" if study_id is None else study_id,
    )
