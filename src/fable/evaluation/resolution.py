"""Transient scientific reduction of canonical evaluation observations."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import numpy as np
import polars as pl

from ..addresses import evaluation_json_path, evaluation_observations_path
from ..config import EvaluateRequest
from .contract import OBSERVATION_SCHEMA

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
    """Derive one testing evaluation's six metrics from its observations."""

    request = EvaluateRequest.model_validate_json(
        evaluation_json_path(storage_root, evaluation_id).read_text(encoding="utf-8"),
        strict=True,
    )
    if request.evaluation_id != evaluation_id:
        raise ValueError("evaluation request ID must match the requested evaluation")
    return _reduce(_load_observations(storage_root, request))


def _load_observations(storage_root: Path, request: EvaluateRequest) -> pl.DataFrame:
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
        raise ValueError("observations must cover every testing origin with non-null values")

    origins = observations["origin_block"].to_numpy()
    if not np.array_equal(origins, expected_origins):
        raise ValueError("observation origins must exactly match the ordered testing window")
    return observations


def _reduce(observations: pl.DataFrame) -> pl.DataFrame:
    predicted_actions = observations["predicted_action_k"].to_numpy()
    minimum_actions = observations["minimum_action_k"].to_numpy()
    predicted_logs = observations["predicted_minimum_log_base_fee"].to_numpy()
    immediate_fees = observations["immediate_base_fee_per_gas"].to_numpy().astype(np.float64)
    selected_fees = observations["selected_base_fee_per_gas"].to_numpy().astype(np.float64)
    minimum_fees = observations["minimum_base_fee_per_gas"].to_numpy().astype(np.float64)

    log_errors = predicted_logs - np.log(minimum_fees)
    classes = np.union1d(minimum_actions, predicted_actions)
    f1_by_class = [
        2.0
        * np.count_nonzero((minimum_actions == action) & (predicted_actions == action))
        / (
            np.count_nonzero(minimum_actions == action)
            + np.count_nonzero(predicted_actions == action)
        )
        for action in classes
    ]
    metrics = {
        "accuracy": float(np.mean(predicted_actions == minimum_actions)),
        "f1_macro": float(np.mean(f1_by_class)),
        "log_fee_mae": float(np.mean(np.abs(log_errors))),
        "log_fee_mse": float(np.mean(np.square(log_errors))),
        "base_fee_savings": float(np.mean((immediate_fees - selected_fees) / immediate_fees)),
        "base_fee_optimality_gap": float(np.mean((selected_fees - minimum_fees) / minimum_fees)),
    }
    if not np.isfinite(tuple(metrics.values())).all():
        raise ValueError("evaluation reduction must contain only finite metrics")
    return pl.DataFrame(
        {name: [value] for name, value in metrics.items()},
        schema=_RESULT_SCHEMA,
    )


__all__ = ["reduce_evaluation"]
