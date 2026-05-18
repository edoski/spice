"""Typed catalog rows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True, slots=True)
class CatalogCorpusRecord:
    corpus_id: str
    corpus_name: str
    chain_name: str


@dataclass(frozen=True, slots=True)
class CatalogStudyRecord:
    study_id: str
    study_name: str
    corpus_id: str
    corpus_name: str
    chain_name: str
    features_id: str
    prediction_id: str
    model_id: str
    problem_id: str


@dataclass(frozen=True, slots=True)
class CatalogArtifactRecord:
    artifact_id: str
    corpus_id: str
    corpus_name: str
    chain_name: str
    features_id: str
    prediction_id: str
    model_id: str
    problem_id: str
    variant: str
    study_id: str | None
    study_name: str | None


CatalogRecord: TypeAlias = CatalogCorpusRecord | CatalogStudyRecord | CatalogArtifactRecord
