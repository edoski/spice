from __future__ import annotations

import math
from pathlib import Path
from uuid import UUID

import polars as pl
import pytest

from fable.addresses import evaluation_directory
from fable.config import BlockWindow, EvaluateRequest
from fable.evaluation import reduce_evaluation

_EVALUATION_ID = UUID("10000000-0000-4000-8000-000000000001")
_OTHER_EVALUATION_ID = UUID("10000000-0000-4000-8000-000000000002")
_ARTIFACT_ID = UUID("20000000-0000-4000-8000-000000000001")
_CORPUS_ID = UUID("30000000-0000-4000-8000-000000000001")

_OBSERVATION_SCHEMA = pl.Schema(
    {
        "origin_block": pl.Int64,
        "predicted_action_k": pl.Int64,
        "predicted_minimum_log_base_fee": pl.Float64,
        "minimum_action_k": pl.Int64,
        "immediate_base_fee_per_gas": pl.Int64,
        "selected_base_fee_per_gas": pl.Int64,
        "minimum_base_fee_per_gas": pl.Int64,
    }
)
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


def _request(
    *,
    evaluation_id: UUID = _EVALUATION_ID,
    testing_window: BlockWindow | None = None,
) -> EvaluateRequest:
    return EvaluateRequest(
        workflow="evaluate",
        evaluation_id=evaluation_id,
        artifact_id=_ARTIFACT_ID,
        corpus_id=_CORPUS_ID,
        testing_window=testing_window or BlockWindow(first_parent_block=20, last_parent_block=26),
    )


def _row(
    origin: int,
    predicted_action: int,
    predicted_log: float | None,
    minimum_action: int,
    immediate_fee: int,
    selected_fee: int,
    minimum_fee: int,
) -> dict[str, int | float | None]:
    return {
        "origin_block": origin,
        "predicted_action_k": predicted_action,
        "predicted_minimum_log_base_fee": predicted_log,
        "minimum_action_k": minimum_action,
        "immediate_base_fee_per_gas": immediate_fee,
        "selected_base_fee_per_gas": selected_fee,
        "minimum_base_fee_per_gas": minimum_fee,
    }


def _rows() -> list[dict[str, int | float | None]]:
    return [
        _row(20, 0, math.log(10) + 1.0, 0, 10, 10, 10),
        _row(21, 1, math.log(10) - 1.0, 2, 20, 15, 10),
        _row(22, 2, math.log(12) + 2.0, 2, 30, 12, 12),
        _row(23, 3, math.log(10) - 2.0, 1, 40, 20, 10),
        _row(24, 1, math.log(25), 1, 50, 25, 25),
        _row(25, 0, math.log(15) + 0.5, 3, 60, 60, 15),
        _row(26, 2, math.log(14) - 0.5, 0, 14, 20, 14),
    ]


def _observations(rows: list[dict[str, int | float | None]] | None = None) -> pl.DataFrame:
    return pl.DataFrame(rows or _rows(), schema=_OBSERVATION_SCHEMA)


def _publish_evaluation(
    storage_root: Path,
    request: EvaluateRequest,
    observations: pl.DataFrame,
) -> None:
    directory = evaluation_directory(storage_root, _EVALUATION_ID)
    directory.mkdir(parents=True)
    (directory / "evaluation.json").write_text(request.model_dump_json(), encoding="utf-8")
    observations.write_parquet(directory / "observations.parquet")


def test_reduce_evaluation_derives_exact_metrics_from_self_contained_observations(
    tmp_path: Path,
) -> None:
    _publish_evaluation(tmp_path, _request(), _observations())

    result = reduce_evaluation(tmp_path, _EVALUATION_ID)

    assert result.schema == _RESULT_SCHEMA
    assert result.height == 1
    assert result.row(0) == pytest.approx(
        (
            3.0 / 7.0,
            0.375,
            1.0,
            1.5,
            199.0 / 980.0,
            69.0 / 98.0,
        )
    )


@pytest.mark.parametrize(
    "case",
    [
        "uuid",
        "window",
        "schema",
        "null",
        "origins",
        "nonfinite_log",
        "negative_action",
        "nonpositive_fee",
        "minimum_above_fees",
        "predicted_zero_fee",
        "minimum_zero_fee",
        "same_action_fee",
    ],
)
def test_reduce_evaluation_rejects_invalid_observation_contract(
    tmp_path: Path,
    case: str,
) -> None:
    request = _request()
    rows = _rows()
    if case == "uuid":
        request = _request(evaluation_id=_OTHER_EVALUATION_ID)
    elif case == "window":
        request = _request(testing_window=BlockWindow(first_parent_block=19, last_parent_block=25))
    elif case == "null":
        rows[0]["predicted_minimum_log_base_fee"] = None
    elif case == "origins":
        rows[1]["origin_block"] = 22
    elif case == "nonfinite_log":
        rows[0]["predicted_minimum_log_base_fee"] = math.inf
    elif case == "negative_action":
        rows[0]["predicted_action_k"] = -1
    elif case == "nonpositive_fee":
        rows[0]["immediate_base_fee_per_gas"] = 0
    elif case == "minimum_above_fees":
        rows[1]["minimum_base_fee_per_gas"] = 21
    elif case == "predicted_zero_fee":
        rows[5]["selected_base_fee_per_gas"] = 59
    elif case == "minimum_zero_fee":
        rows[6]["minimum_base_fee_per_gas"] = 13
    elif case == "same_action_fee":
        rows[2]["selected_base_fee_per_gas"] = 13

    observations = _observations(rows)
    if case == "schema":
        observations = observations.select(
            "predicted_action_k",
            *[name for name in _OBSERVATION_SCHEMA if name != "predicted_action_k"],
        )
    _publish_evaluation(tmp_path, request, observations)

    with pytest.raises(ValueError):
        reduce_evaluation(tmp_path, _EVALUATION_ID)
