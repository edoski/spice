from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fable.addresses import (
    artifact_checkpoint_path,
    artifact_directory,
    corpus_blocks_path,
    corpus_directory,
    corpus_json_path,
    evaluation_directory,
    evaluation_json_path,
    evaluation_observations_path,
    study_json_path,
)
from fable.config import (
    BaselineSource,
    BlockWindow,
    ExperimentSemantics,
    FitMethod,
    LstmDefinition,
    Method,
    TrainingDefinition,
)
from fable.requests import (
    fresh_evaluate_request,
    fresh_train_request,
    fresh_tune_request,
)

CORPUS_ID = UUID("00000000-0000-4000-8000-000000000001")
STUDY_ID = UUID("00000000-0000-4000-8000-000000000002")
ARTIFACT_ID = UUID("00000000-0000-4000-8000-000000000003")
EVALUATION_ID = UUID("00000000-0000-4000-8000-000000000004")


def _fit() -> FitMethod:
    return FitMethod(
        learning_rate=0.001,
        weight_decay=0.0,
        accumulation=1,
        gradient_clip_norm=0.75,
        seed=17,
        max_epochs=9,
        validate_every_completed_epoch=1,
        patience=3,
        min_delta=0.01,
    )


def _experiment() -> ExperimentSemantics:
    return ExperimentSemantics(
        training_window=BlockWindow(
            first_parent_block=100,
            last_parent_block=199,
        ),
        validation_window=BlockWindow(
            first_parent_block=210,
            last_parent_block=249,
        ),
        context_blocks=20,
        horizon_blocks=10,
        ordered_features=("base_fee", "gas_utilization"),
    )


def test_request_constructors_mint_one_id_each(monkeypatch) -> None:
    minted = (STUDY_ID, ARTIFACT_ID, EVALUATION_ID)
    minted_ids = iter(minted)
    monkeypatch.setattr("fable.requests.uuid4", lambda: next(minted_ids))

    experiment = _experiment()
    fit = _fit()
    method = Method(
        model=LstmDefinition(
            family="lstm",
            hidden=32,
            layers=1,
            head_hidden=16,
            dropout=0.2,
        ),
        fit=fit,
    )
    tune = fresh_tune_request(
        CORPUS_ID,
        experiment,
        (method,),
    )
    train = fresh_train_request(
        BaselineSource(
            kind="baseline",
            corpus_id=CORPUS_ID,
            training_definition=TrainingDefinition(
                experiment=experiment,
                method=method,
            ),
        )
    )
    evaluate = fresh_evaluate_request(
        train.artifact_id,
        CORPUS_ID,
        BlockWindow(
            first_parent_block=300,
            last_parent_block=349,
        ),
    )

    assert (
        tune.study_id,
        train.artifact_id,
        evaluate.evaluation_id,
    ) == minted


def test_addresses_map_ids_to_canonical_paths() -> None:
    root = Path("/storage")
    cases = (
        (corpus_directory(root, CORPUS_ID), root / "corpora" / str(CORPUS_ID)),
        (corpus_json_path(root, CORPUS_ID), root / "corpora" / str(CORPUS_ID) / "corpus.json"),
        (
            corpus_blocks_path(root, CORPUS_ID),
            root / "corpora" / str(CORPUS_ID) / "blocks.parquet",
        ),
        (study_json_path(root, STUDY_ID), root / "studies" / f"{STUDY_ID}.json"),
        (
            artifact_directory(root, ARTIFACT_ID),
            root / "artifacts" / str(ARTIFACT_ID),
        ),
        (
            artifact_checkpoint_path(root, ARTIFACT_ID),
            root / "artifacts" / str(ARTIFACT_ID) / "model.ckpt",
        ),
        (
            evaluation_directory(root, EVALUATION_ID),
            root / "evaluations" / str(EVALUATION_ID),
        ),
        (
            evaluation_json_path(root, EVALUATION_ID),
            root / "evaluations" / str(EVALUATION_ID) / "evaluation.json",
        ),
        (
            evaluation_observations_path(root, EVALUATION_ID),
            root / "evaluations" / str(EVALUATION_ID) / "observations.parquet",
        ),
    )
    assert all(actual == expected for actual, expected in cases)
