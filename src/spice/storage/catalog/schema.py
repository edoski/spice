"""Relational catalog schema."""

from __future__ import annotations

from sqlalchemy import Column, Integer, MetaData, String, Table

metadata = MetaData()

corpus_index = Table(
    "corpus_index",
    metadata,
    Column("corpus_id", String, primary_key=True),
    Column("corpus_name", String, nullable=False),
    Column("chain_name", String, nullable=False),
    Column("created_at", Integer, nullable=False),
    Column("updated_at", Integer, nullable=False),
)

study_index = Table(
    "study_index",
    metadata,
    Column("study_id", String, primary_key=True),
    Column("study_name", String, nullable=False),
    Column("corpus_id", String, nullable=False),
    Column("corpus_name", String, nullable=False),
    Column("chain_name", String, nullable=False),
    Column("features_id", String, nullable=False),
    Column("prediction_id", String, nullable=False),
    Column("model_id", String, nullable=False),
    Column("problem_id", String, nullable=False),
    Column("created_at", Integer, nullable=False),
    Column("updated_at", Integer, nullable=False),
)

artifact_index = Table(
    "artifact_index",
    metadata,
    Column("artifact_id", String, primary_key=True),
    Column("corpus_id", String, nullable=False),
    Column("corpus_name", String, nullable=False),
    Column("chain_name", String, nullable=False),
    Column("features_id", String, nullable=False),
    Column("prediction_id", String, nullable=False),
    Column("model_id", String, nullable=False),
    Column("problem_id", String, nullable=False),
    Column("variant", String, nullable=False),
    Column("study_id", String),
    Column("study_name", String),
    Column("created_at", Integer, nullable=False),
    Column("updated_at", Integer, nullable=False),
)
