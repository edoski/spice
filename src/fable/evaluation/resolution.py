"""Transient scientific reduction of canonical evaluation predictions."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import numpy as np
import polars as pl

from ..addresses import evaluation_json_path, evaluation_observations_path
from ..config import EvaluateRequest
from ..corpus import Corpus, load_corpus
from ..modeling import load_artifact
from .contract import OBSERVATION_SCHEMA, validate_request_artifact

_RESULT_SCHEMA = pl.Schema(
    {
        "accuracy": pl.Float64,
        "f1_macro": pl.Float64,
        "log_fee_mae": pl.Float64,
        "log_fee_mse": pl.Float64,
        "base_fee_savings": pl.Float64,
        "base_fee_optimality_gap": pl.Float64,
    }
)


def reduce_evaluation(storage_root: Path, evaluation_id: UUID) -> pl.DataFrame:
    """Derive one testing evaluation's six metrics from predictions and its Corpus."""

    request = EvaluateRequest.model_validate_json(
        evaluation_json_path(storage_root, evaluation_id).read_text(encoding="utf-8"),
        strict=True,
    )
    if request.evaluation_id != evaluation_id:
        raise ValueError("evaluation request ID must match the requested evaluation")

    association, _ = load_artifact(storage_root, request.artifact_id)
    validate_request_artifact(request, association)
    experiment = association.training_definition.experiment
    if (
        experiment.validation_window.last_parent_block + experiment.horizon_blocks
        >= request.testing_window.first_parent_block
    ):
        raise ValueError("testing window must follow complete validation outcomes")

    corpus = load_corpus(storage_root, request.corpus_id)
    if corpus.request.corpus_id != request.corpus_id:
        raise ValueError("Corpus request ID must match the evaluation Corpus")
    observations = _load_observations(storage_root, request, experiment.horizon_blocks)
    outcomes = _corpus_outcomes(corpus, request, experiment.horizon_blocks)
    return _reduce(
        observations,
        outcomes,
        target_mean=association.target_state.mean,
        target_standard_deviation=association.target_state.standard_deviation,
    )


def _load_observations(
    storage_root: Path,
    request: EvaluateRequest,
    horizon_blocks: int,
) -> pl.DataFrame:
    path = evaluation_observations_path(storage_root, request.evaluation_id)
    if pl.read_parquet_schema(path) != OBSERVATION_SCHEMA:
        raise ValueError("observations must have the canonical ordered schema")
    observations = pl.read_parquet(path)
    window = request.testing_window
    expected_origins = np.arange(
        window.first_parent_block,
        window.last_parent_block + 1,
        dtype=np.int64,
    )
    if observations.height != expected_origins.size or any(observations.null_count().row(0)):
        raise ValueError("observations must cover every testing origin with non-null predictions")

    origins = observations["origin_block"].to_numpy()
    actions = observations["predicted_action_k"].to_numpy()
    predicted_z = observations["predicted_minimum_log_base_fee_z"].to_numpy()
    if not np.array_equal(origins, expected_origins):
        raise ValueError("observation origins must exactly match the ordered testing window")
    if np.any(actions < 0) or np.any(actions >= horizon_blocks):
        raise ValueError("predicted actions must be within the artifact horizon")
    if not np.isfinite(predicted_z).all():
        raise ValueError("predicted minimum-log-fee z values must be finite")
    return observations


def _corpus_outcomes(
    corpus: Corpus,
    request: EvaluateRequest,
    horizon_blocks: int,
) -> np.ndarray:
    window = request.testing_window
    selected = corpus.blocks.select_range(
        window.first_parent_block + 1,
        window.last_parent_block + horizon_blocks,
    )
    fees = np.asarray(selected.to_polars()["base_fee_per_gas"].to_numpy(), dtype=np.int64)
    origin_count = window.last_parent_block - window.first_parent_block + 1
    outcomes = fees[
        np.arange(origin_count, dtype=np.int64)[:, None] + np.arange(horizon_blocks, dtype=np.int64)
    ]
    if np.any(outcomes <= 0):
        raise ValueError("required Corpus base fees must be positive")
    return outcomes


def _reduce(
    observations: pl.DataFrame,
    outcomes: np.ndarray,
    *,
    target_mean: float,
    target_standard_deviation: float,
) -> pl.DataFrame:
    actions = observations["predicted_action_k"].to_numpy()
    predicted_z = (
        observations["predicted_minimum_log_base_fee_z"]
        .to_numpy()
        .astype(
            np.float64,
            copy=False,
        )
    )
    origins = np.arange(outcomes.shape[0], dtype=np.int64)
    true_actions = outcomes.argmin(axis=1)
    immediate_fees = outcomes[:, 0].astype(np.float64, copy=False)
    selected_fees = outcomes[origins, actions].astype(np.float64, copy=False)
    optimal_fees = outcomes[origins, true_actions].astype(np.float64, copy=False)

    log_errors = target_mean + target_standard_deviation * predicted_z - np.log(optimal_fees)
    classes = np.union1d(true_actions, actions)
    f1_by_class = [
        2.0
        * np.count_nonzero((true_actions == action) & (actions == action))
        / (np.count_nonzero(true_actions == action) + np.count_nonzero(actions == action))
        for action in classes
    ]
    metrics = {
        "accuracy": float(np.mean(actions == true_actions)),
        "f1_macro": float(np.mean(f1_by_class)),
        "log_fee_mae": float(np.mean(np.abs(log_errors))),
        "log_fee_mse": float(np.mean(np.square(log_errors))),
        "base_fee_savings": float(np.mean((immediate_fees - selected_fees) / immediate_fees)),
        "base_fee_optimality_gap": float(np.mean((selected_fees - optimal_fees) / optimal_fees)),
    }
    if not np.isfinite(tuple(metrics.values())).all():
        raise ValueError("evaluation reduction must contain only finite metrics")
    return pl.DataFrame(
        {name: [value] for name, value in metrics.items()},
        schema=_RESULT_SCHEMA,
    )


__all__ = ["reduce_evaluation"]
