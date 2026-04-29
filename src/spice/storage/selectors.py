"""Catalog selectors for persisted storage roots."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatasetSelector:
    chain_name: str | None = None
    dataset_name: str | None = None


@dataclass(frozen=True, slots=True)
class StudySelector:
    study_id: str | None = None
    chain_name: str | None = None
    dataset_name: str | None = None
    features_id: str | None = None
    prediction_id: str | None = None
    model_id: str | None = None
    problem_id: str | None = None
    study_name: str | None = None


@dataclass(frozen=True, slots=True)
class ArtifactSelector:
    artifact_id: str | None = None
    chain_name: str | None = None
    dataset_name: str | None = None
    features_id: str | None = None
    prediction_id: str | None = None
    model_id: str | None = None
    problem_id: str | None = None
    variant: str | None = None
    study_name: str | None = None
