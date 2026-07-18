from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

import pytest
from pydantic import ValidationError

from spice.config import (
    METHOD_ADAPTER,
    WORKFLOW_REQUEST_ADAPTER,
    AdamWMethod,
    BaselineSource,
    CorpusDefinition,
    CorpusRequest,
    EvaluateRequest,
    ExperimentSemantics,
    FitMethod,
    LstmCapacity,
    LstmDefinition,
    LstmMethod,
    LstmMethodSpace,
    OriginWindow,
    SelectedStudySource,
    StudyDefinition,
    TrainingDefinition,
    TrainRequest,
    TransformerCapacity,
    TransformerDefinition,
    TransformerLstmCapacity,
    TransformerLstmDefinition,
    TransformerLstmMethod,
    TransformerLstmMethodSpace,
    TransformerMethod,
    TransformerMethodSpace,
    TuneRequest,
)
from spice.storage.ids import (
    fresh_corpus_request,
    fresh_evaluate_request,
    fresh_train_request,
    fresh_tune_request,
)
from spice.storage.layout import (
    artifact_checkpoint_path,
    corpus_blocks_path,
    corpus_directory,
    corpus_json_path,
    evaluation_directory,
    evaluation_json_path,
    evaluation_observations_path,
    study_json_path,
)

CORPUS_ID = UUID("00000000-0000-4000-8000-000000000001")
STUDY_ID = UUID("00000000-0000-4000-8000-000000000002")
ARTIFACT_ID = UUID("00000000-0000-4000-8000-000000000003")
EVALUATION_ID = UUID("00000000-0000-4000-8000-000000000004")


def _window(
    role: Literal["training", "validation", "testing"] = "validation",
) -> OriginWindow:
    bounds = {
        "training": (100, 199),
        "validation": (210, 249),
        "testing": (300, 349),
    }
    first, last = bounds[role]
    return OriginWindow(
        role=role,
        first_parent_block=first,
        last_parent_block=last,
    )


def _experiment() -> ExperimentSemantics:
    return ExperimentSemantics(
        training_window=_window("training"),
        validation_window=_window("validation"),
        context_blocks=20,
        horizon_blocks=10,
        ordered_features=("base_fee", "gas_utilization"),
        classification_loss="unweighted",
    )


def _fit() -> FitMethod:
    return FitMethod(
        accumulation=1,
        gradient_clip_norm=1.0,
        scheduler="none",
        seed=2026,
        max_epochs=36,
        validate_every_completed_epoch=1,
        patience=8,
        min_delta=0.0,
        improvement="strict_lower",
        restore="earliest_best",
        minimum_epoch_floor=False,
    )


def _optimizer() -> AdamWMethod:
    return AdamWMethod(learning_rate=0.001, weight_decay=0.0)


def _branches() -> tuple[tuple[Any, Any, Any], ...]:
    common = {"dropout": 0.2, "optimizer": _optimizer(), "training_batch": 64, "fit": _fit()}
    lstm_capacity = LstmCapacity(projection=16, hidden=32, layers=1, head_hidden=16)
    transformer_capacity = TransformerCapacity(
        model_width=32,
        attention_heads=4,
        transformer_layers=2,
        feedforward_width=64,
        head_hidden=16,
    )
    hybrid_capacity = TransformerLstmCapacity(
        model_width=32,
        attention_heads=4,
        transformer_layers=2,
        feedforward_width=64,
        lstm_hidden=24,
        lstm_layers=1,
        head_hidden=16,
    )
    return (
        (
            LstmDefinition(family="lstm", dropout=0.2, **lstm_capacity.model_dump()),
            LstmMethod(family="lstm", capacity=lstm_capacity, **common),
            LstmMethodSpace(
                family="lstm",
                capacities=(lstm_capacity,),
                dropouts=(0.2,),
                learning_rates=(0.001,),
                weight_decays=(0.0,),
            ),
        ),
        (
            TransformerDefinition(
                family="transformer", dropout=0.2, **transformer_capacity.model_dump()
            ),
            TransformerMethod(family="transformer", capacity=transformer_capacity, **common),
            TransformerMethodSpace(
                family="transformer",
                capacities=(transformer_capacity,),
                dropouts=(0.2,),
                learning_rates=(0.001,),
                weight_decays=(0.0,),
            ),
        ),
        (
            TransformerLstmDefinition(
                family="transformer_lstm", dropout=0.2, **hybrid_capacity.model_dump()
            ),
            TransformerLstmMethod(family="transformer_lstm", capacity=hybrid_capacity, **common),
            TransformerLstmMethodSpace(
                family="transformer_lstm",
                capacities=(hybrid_capacity,),
                dropouts=(0.2,),
                learning_rates=(0.001,),
                weight_decays=(0.0,),
            ),
        ),
    )


def test_positive_branch_matrix() -> None:
    experiment = _experiment()
    for model, method, method_space in _branches():
        training = TrainingDefinition(
            experiment=experiment,
            model=model,
            optimizer=_optimizer(),
            training_batch=64,
            fit=_fit(),
        )
        sources = (
            BaselineSource(
                kind="baseline",
                corpus_id=CORPUS_ID,
                training_definition=training,
            ),
            SelectedStudySource(
                kind="selected_study",
                corpus_id=CORPUS_ID,
                study_id=STUDY_ID,
                experiment=experiment,
            ),
        )
        for source in sources:
            hydrated = WORKFLOW_REQUEST_ADAPTER.validate_python(
                TrainRequest(workflow="train", artifact_id=ARTIFACT_ID, source=source).model_dump()
            )
            assert isinstance(hydrated, TrainRequest)
            assert hydrated.source.kind == source.kind

        standalone_method = METHOD_ADAPTER.validate_json(method.model_dump_json())
        assert standalone_method == method
        study = StudyDefinition(experiment=experiment, method_space=method_space)
        tune = TuneRequest(
            workflow="tune",
            study_id=STUDY_ID,
            corpus_id=CORPUS_ID,
            study_definition=study,
        )
        assert tune.study_definition.method_space.family == method.family

    for role in ("validation", "testing"):
        hydrated = WORKFLOW_REQUEST_ADAPTER.validate_python(
            EvaluateRequest(
                workflow="evaluate",
                evaluation_id=EVALUATION_ID,
                artifact_id=ARTIFACT_ID,
                corpus_id=CORPUS_ID,
                window=_window(role),
            ).model_dump()
        )
        assert isinstance(hydrated, EvaluateRequest)
        assert hydrated.window.role == role


def _invalid_cases() -> tuple[tuple[Callable[..., object], dict[str, object]], ...]:
    model, method, method_space = _branches()[0]
    experiment = _experiment()
    return (
        (OriginWindow, {"role": "holdout", "first_parent_block": 1, "last_parent_block": 2}),
        (
            lambda **payload: METHOD_ADAPTER.validate_python(payload),
            {**method.model_dump(), "family": "cnn"},
        ),
        (
            lambda **payload: WORKFLOW_REQUEST_ADAPTER.validate_python(payload),
            {
                "workflow": "tune",
                "study_id": STUDY_ID,
                "corpus_id": CORPUS_ID,
                "study_definition": {
                    "experiment": experiment.model_dump(),
                    "method_space": method_space.model_dump(),
                },
            },
        ),
        (CorpusDefinition, {"chain_id": 1, "first_block": 1, "last_block": 2, "extra": 3}),
        (CorpusDefinition, {"chain_id": True, "first_block": 1, "last_block": 2}),
        (CorpusDefinition, {"chain_id": 1, "first_block": 2, "last_block": 1}),
        (
            TransformerCapacity,
            {
                "model_width": 31,
                "attention_heads": 4,
                "transformer_layers": 1,
                "feedforward_width": 32,
                "head_hidden": 8,
            },
        ),
        (LstmMethod, {**method.model_dump(), "training_batch": 32}),
        (LstmMethodSpace, {**method_space.model_dump(), "dropouts": (0.2, 0.2)}),
        (
            ExperimentSemantics,
            {
                **experiment.model_dump(),
                "validation_window": _window("testing"),
            },
        ),
        (
            ExperimentSemantics,
            {
                **experiment.model_dump(),
                "validation_window": OriginWindow(
                    role="validation", first_parent_block=209, last_parent_block=249
                ),
            },
        ),
        (
            EvaluateRequest,
            {
                "workflow": "evaluate",
                "evaluation_id": EVALUATION_ID,
                "artifact_id": ARTIFACT_ID,
                "corpus_id": CORPUS_ID,
                "window": _window("training"),
            },
        ),
        (
            TrainingDefinition,
            {
                **TrainingDefinition(
                    experiment=experiment,
                    model=model,
                    optimizer=_optimizer(),
                    training_batch=64,
                    fit=_fit(),
                ).model_dump(),
                "training_batch": 65,
            },
        ),
    )


@pytest.mark.parametrize(("value_type", "payload"), _invalid_cases())
def test_invalid_value_table(
    value_type: Callable[..., object],
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        value_type(**payload)


def test_four_constructors_mint_once_while_hydration_preserves_ids(monkeypatch) -> None:
    minted = iter((CORPUS_ID, STUDY_ID, ARTIFACT_ID, EVALUATION_ID))
    calls = 0

    def uuid4_once() -> UUID:
        nonlocal calls
        calls += 1
        return next(minted)

    monkeypatch.setattr("spice.storage.ids.uuid4", uuid4_once)
    corpus = fresh_corpus_request(CorpusDefinition(chain_id=1, first_block=1, last_block=100))
    model, _, method_space = _branches()[0]
    training = TrainingDefinition(
        experiment=_experiment(),
        model=model,
        optimizer=_optimizer(),
        training_batch=64,
        fit=_fit(),
    )
    tune = fresh_tune_request(
        corpus.corpus_id,
        StudyDefinition(experiment=_experiment(), method_space=method_space),
    )
    train = fresh_train_request(
        BaselineSource(
            kind="baseline",
            corpus_id=corpus.corpus_id,
            training_definition=training,
        )
    )
    evaluate = fresh_evaluate_request(train.artifact_id, corpus.corpus_id, _window())

    assert calls == 4
    assert CorpusRequest.model_validate_json(corpus.model_dump_json()).corpus_id == CORPUS_ID
    assert TuneRequest.model_validate_json(tune.model_dump_json()).study_id == STUDY_ID
    assert (
        WORKFLOW_REQUEST_ADAPTER.validate_json(train.model_dump_json()).artifact_id == ARTIFACT_ID
    )
    assert (
        WORKFLOW_REQUEST_ADAPTER.validate_json(evaluate.model_dump_json()).evaluation_id
        == EVALUATION_ID
    )
    assert corpus_directory(Path("root"), corpus.corpus_id) == Path("root/corpora") / str(CORPUS_ID)
    assert calls == 4


def test_exact_eight_address_table() -> None:
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
            artifact_checkpoint_path(root, ARTIFACT_ID),
            root / "artifacts" / f"{ARTIFACT_ID}.ckpt",
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
