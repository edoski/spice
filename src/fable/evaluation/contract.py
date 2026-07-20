"""Canonical durable evaluation schemas."""

import polars as pl

from ..config import EvaluateRequest
from ..modeling import ArtifactAssociation

OBSERVATION_SCHEMA = pl.Schema(
    {
        "origin_block": pl.Int64,
        "predicted_action_k": pl.Int64,
        "predicted_minimum_log_base_fee_z": pl.Float32,
    }
)


def validate_request_artifact(
    request: EvaluateRequest,
    association: ArtifactAssociation,
) -> None:
    if association.request.artifact_id != request.artifact_id:
        raise ValueError("artifact request ID must match the evaluation artifact")
    if association.request.source.corpus_id != request.corpus_id:
        raise ValueError("artifact source Corpus must match the evaluation Corpus")


__all__ = ["OBSERVATION_SCHEMA", "validate_request_artifact"]
