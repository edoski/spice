from __future__ import annotations

from pathlib import Path

from spice.storage.catalog.records import (
    CatalogArtifactRecord,
    CatalogCorpusRecord,
    CatalogStudyRecord,
)


def dataset_record(
    root_path: Path,
    *,
    corpus_id: str = "dataset-1",
    corpus_name: str = "corpus",
    chain_name: str = "ethereum",
    state_db: Path | None = None,
) -> CatalogCorpusRecord:
    del root_path, state_db
    return CatalogCorpusRecord(
        corpus_id=corpus_id,
        corpus_name=corpus_name,
        chain_name=chain_name,
    )


def study_record(
    root_path: Path,
    *,
    study_id: str = "study-1",
    study_name: str = "study",
    corpus_id: str = "dataset-1",
    corpus_name: str = "corpus",
    chain_name: str = "ethereum",
    features_id: str = "features",
    prediction_id: str = "prediction",
    model_id: str = "model",
    problem_id: str = "problem",
    state_db: Path | None = None,
) -> CatalogStudyRecord:
    del root_path, state_db
    return CatalogStudyRecord(
        study_id=study_id,
        study_name=study_name,
        corpus_id=corpus_id,
        corpus_name=corpus_name,
        chain_name=chain_name,
        features_id=features_id,
        prediction_id=prediction_id,
        model_id=model_id,
        problem_id=problem_id,
    )


def artifact_record(
    root_path: Path,
    *,
    artifact_id: str = "artifact-1",
    corpus_id: str = "dataset-1",
    corpus_name: str = "corpus",
    chain_name: str = "ethereum",
    features_id: str = "features",
    prediction_id: str = "prediction",
    model_id: str = "model",
    problem_id: str = "problem",
    variant: str = "baseline",
    study_id: str | None = None,
    study_name: str | None = None,
    state_db: Path | None = None,
) -> CatalogArtifactRecord:
    del root_path, state_db
    return CatalogArtifactRecord(
        artifact_id=artifact_id,
        corpus_id=corpus_id,
        corpus_name=corpus_name,
        chain_name=chain_name,
        features_id=features_id,
        prediction_id=prediction_id,
        model_id=model_id,
        problem_id=problem_id,
        variant=variant,
        study_id=study_id,
        study_name=study_name,
    )
