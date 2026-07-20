from __future__ import annotations

import importlib
import json
import math
from pathlib import Path
from uuid import UUID

import numpy as np
import polars as pl
import pytest
from torch import nn

from fable.addresses import (
    corpus_blocks_path,
    corpus_directory,
    corpus_json_path,
    evaluation_directory,
)
from fable.config import (
    AdamWMethod,
    BaselineSource,
    BlockWindow,
    CorpusDefinition,
    CorpusRequest,
    EvaluateRequest,
    ExperimentSemantics,
    FitMethod,
    LstmDefinition,
    TrainingDefinition,
    TrainRequest,
)
from fable.evaluation import reduce_evaluation
from fable.min_block_fee import TargetState
from fable.modeling import ArtifactAssociation
from fable.temporal.features import FeatureState

resolution_module = importlib.import_module("fable.evaluation.resolution")

_EVALUATION_ID = UUID("10000000-0000-4000-8000-000000000001")
_OTHER_EVALUATION_ID = UUID("10000000-0000-4000-8000-000000000002")
_ARTIFACT_ID = UUID("20000000-0000-4000-8000-000000000001")
_OTHER_ARTIFACT_ID = UUID("20000000-0000-4000-8000-000000000002")
_CORPUS_ID = UUID("30000000-0000-4000-8000-000000000001")
_OTHER_CORPUS_ID = UUID("30000000-0000-4000-8000-000000000002")

_OBSERVATION_SCHEMA = pl.Schema(
    {
        "origin_block": pl.Int64,
        "predicted_action_k": pl.Int64,
        "predicted_minimum_log_base_fee_z": pl.Float32,
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


def _experiment() -> ExperimentSemantics:
    return ExperimentSemantics(
        training_window=BlockWindow(first_parent_block=8, last_parent_block=8),
        validation_window=BlockWindow(first_parent_block=14, last_parent_block=14),
        context_blocks=2,
        horizon_blocks=5,
        ordered_features=("log_base_fee_per_gas",),
    )


def _association(
    *,
    artifact_id: UUID = _ARTIFACT_ID,
    corpus_id: UUID = _CORPUS_ID,
) -> ArtifactAssociation:
    experiment = _experiment()
    return ArtifactAssociation(
        request=TrainRequest(
            workflow="train",
            artifact_id=artifact_id,
            source=BaselineSource(
                kind="baseline",
                corpus_id=corpus_id,
                training_definition=TrainingDefinition(
                    experiment=experiment,
                    model=LstmDefinition(
                        family="lstm",
                        hidden=4,
                        layers=1,
                        head_hidden=3,
                        dropout=0.0,
                    ),
                    optimizer=AdamWMethod(learning_rate=0.01, weight_decay=0.0),
                    fit=FitMethod(
                        accumulation=1,
                        gradient_clip_norm=1.0,
                        seed=17,
                        max_epochs=2,
                        validate_every_completed_epoch=1,
                        patience=1,
                        min_delta=0.0,
                    ),
                ),
            ),
        ),
        feature_state=FeatureState(means=(0.0,), standard_deviations=(1.0,)),
        target_state=TargetState(mean=math.log(5.0), standard_deviation=2.0),
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
        testing_window=testing_window or BlockWindow(first_parent_block=20, last_parent_block=23),
    )


def _observations() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "origin_block": [20, 21, 22, 23],
            "predicted_action_k": [1, 2, 0, 2],
            "predicted_minimum_log_base_fee_z": [
                0.5,
                -0.5,
                1.0,
                -1.0,
            ],
        },
        schema=_OBSERVATION_SCHEMA,
    )


def _write_corpus(
    storage_root: Path,
    *,
    embedded_corpus_id: UUID = _CORPUS_ID,
    invalid_fee: bool = False,
) -> None:
    definition = CorpusDefinition(chain_id=9, first_block=7, last_block=28)
    request = CorpusRequest(corpus_id=embedded_corpus_id, definition=definition)
    corpus_directory(storage_root, _CORPUS_ID).mkdir(parents=True)
    corpus_json_path(storage_root, _CORPUS_ID).write_text(
        json.dumps(
            {
                "request": request.model_dump(mode="json"),
                "finalized_anchor": {
                    "block_number": 28,
                    "block_hash": "a" * 64,
                },
            }
        ),
        encoding="utf-8",
    )
    block_numbers = np.arange(7, 29, dtype=np.int64)
    base_fees = np.full(block_numbers.size, 30, dtype=np.int64)
    base_fees[21 - definition.first_block :] = [10, 5, 5, 20, 5, 8, 6, 9]
    if invalid_fee:
        base_fees[21 - definition.first_block] = 0
    pl.DataFrame(
        {
            "block_number": block_numbers,
            "timestamp": block_numbers * 12,
            "chain_id": np.full(block_numbers.size, 9, dtype=np.int64),
            "base_fee_per_gas": base_fees,
            "gas_used": np.full(block_numbers.size, 50, dtype=np.int64),
            "gas_limit": np.full(block_numbers.size, 100, dtype=np.int64),
            "tx_count": np.full(block_numbers.size, 5, dtype=np.int64),
        },
        schema={
            "block_number": pl.Int64,
            "timestamp": pl.Int64,
            "chain_id": pl.Int64,
            "base_fee_per_gas": pl.Int64,
            "gas_used": pl.Int64,
            "gas_limit": pl.Int64,
            "tx_count": pl.Int64,
        },
    ).write_parquet(corpus_blocks_path(storage_root, _CORPUS_ID))


def _publish_evaluation(
    storage_root: Path,
    request: EvaluateRequest,
    observations: pl.DataFrame,
) -> None:
    directory = evaluation_directory(storage_root, _EVALUATION_ID)
    directory.mkdir(parents=True)
    (directory / "evaluation.json").write_text(request.model_dump_json(), encoding="utf-8")
    observations.write_parquet(directory / "observations.parquet")


def _stub_artifact(
    monkeypatch: pytest.MonkeyPatch,
    association: ArtifactAssociation,
) -> None:
    monkeypatch.setattr(
        resolution_module,
        "load_artifact",
        lambda storage_root, artifact_id: (association, nn.Identity()),
    )


def test_reduce_evaluation_derives_exact_metrics_from_corpus_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_corpus(tmp_path)
    _publish_evaluation(tmp_path, _request(), _observations())
    _stub_artifact(monkeypatch, _association())

    result = reduce_evaluation(tmp_path, _EVALUATION_ID)

    assert result.schema == _RESULT_SCHEMA
    assert result.height == 1
    assert result.row(0) == pytest.approx(
        (
            0.5,
            4.0 / 9.0,
            1.5,
            2.5,
            -0.475,
            0.9,
        ),
        rel=1e-6,
        abs=1e-6,
    )


@pytest.mark.parametrize(
    "case",
    [
        "evaluation_id",
        "artifact_id",
        "source_corpus",
        "corpus_id",
        "testing_window",
        "schema",
        "null",
        "origins",
        "action",
        "z",
        "fee",
    ],
)
def test_reduce_evaluation_rejects_invalid_contracts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    request = _request()
    observations = _observations()
    association = _association()
    embedded_corpus_id = _CORPUS_ID
    invalid_fee = False

    if case == "evaluation_id":
        request = _request(evaluation_id=_OTHER_EVALUATION_ID)
    elif case == "artifact_id":
        association = _association(artifact_id=_OTHER_ARTIFACT_ID)
    elif case == "source_corpus":
        association = _association(corpus_id=_OTHER_CORPUS_ID)
    elif case == "corpus_id":
        embedded_corpus_id = _OTHER_CORPUS_ID
    elif case == "testing_window":
        request = _request(testing_window=BlockWindow(first_parent_block=19, last_parent_block=22))
    elif case == "schema":
        observations = observations.select(
            "predicted_action_k",
            "origin_block",
            "predicted_minimum_log_base_fee_z",
        )
    elif case == "null":
        observations = observations.with_columns(
            pl.Series(
                "predicted_minimum_log_base_fee_z",
                [None, -0.5, 0.0, 0.5],
                dtype=pl.Float32,
            )
        )
    elif case == "origins":
        observations = observations.with_columns(
            pl.Series("origin_block", [20, 22, 22, 23], dtype=pl.Int64)
        )
    elif case == "action":
        observations = observations.with_columns(
            pl.Series("predicted_action_k", [5, 2, 0, 2], dtype=pl.Int64)
        )
    elif case == "z":
        observations = observations.with_columns(
            pl.Series(
                "predicted_minimum_log_base_fee_z",
                [math.inf, -0.5, 0.0, 0.5],
                dtype=pl.Float32,
            )
        )
    elif case == "fee":
        invalid_fee = True

    _write_corpus(
        tmp_path,
        embedded_corpus_id=embedded_corpus_id,
        invalid_fee=invalid_fee,
    )
    _publish_evaluation(tmp_path, request, observations)
    _stub_artifact(monkeypatch, association)

    with pytest.raises(ValueError):
        reduce_evaluation(tmp_path, _EVALUATION_ID)
