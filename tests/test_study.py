from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from fable.addresses import study_json_path
from fable.config import (
    AdamWMethod,
    BlockWindow,
    ExperimentSemantics,
    FitMethod,
    LstmCapacity,
    LstmDefinition,
    LstmMethod,
    LstmMethodSpace,
    Method,
    MethodSpace,
    SelectedStudySource,
    StudyDefinition,
    TrainingDefinition,
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
from fable.study import (
    RetainedResult,
    Study,
    apply_method,
    materialize_selected_training,
    publish_study,
    retain_result,
    training_definition_from_method,
)

STUDY_ID = UUID("10000000-0000-4000-8000-000000000001")
CORPUS_ID = UUID("20000000-0000-4000-8000-000000000001")
OTHER_CORPUS_ID = UUID("20000000-0000-4000-8000-000000000002")

FIT = FitMethod(
    accumulation=3,
    gradient_clip_norm=0.75,
    seed=17,
    max_epochs=12,
    validate_every_completed_epoch=2,
    patience=4,
    min_delta=0.01,
)

LSTM_CAPACITY = LstmCapacity(hidden=256, layers=1, head_hidden=128)
TRANSFORMER_CAPACITY = TransformerCapacity(
    model_width=192,
    attention_heads=4,
    transformer_layers=3,
    feedforward_width=384,
    head_hidden=192,
)
TRANSFORMER_LSTM_CAPACITY = TransformerLstmCapacity(
    model_width=192,
    attention_heads=4,
    transformer_layers=3,
    feedforward_width=384,
    lstm_hidden=192,
    lstm_layers=1,
    head_hidden=192,
)

LSTM_METHOD = LstmMethod(
    family="lstm",
    capacity=LSTM_CAPACITY,
    dropout=0.2,
    optimizer=AdamWMethod(learning_rate=3e-4, weight_decay=1e-4),
    fit=FIT,
)
TRANSFORMER_METHOD = TransformerMethod(
    family="transformer",
    capacity=TRANSFORMER_CAPACITY,
    dropout=0.2,
    optimizer=AdamWMethod(learning_rate=1e-4, weight_decay=1e-4),
    fit=FIT,
)
TRANSFORMER_LSTM_METHOD = TransformerLstmMethod(
    family="transformer_lstm",
    capacity=TRANSFORMER_LSTM_CAPACITY,
    dropout=0.2,
    optimizer=AdamWMethod(learning_rate=1e-4, weight_decay=1e-4),
    fit=FIT,
)

LSTM_SPACE = LstmMethodSpace(
    family="lstm",
    methods=(LSTM_METHOD,),
)
TRANSFORMER_SPACE = TransformerMethodSpace(
    family="transformer",
    methods=(TRANSFORMER_METHOD,),
)
TRANSFORMER_LSTM_SPACE = TransformerLstmMethodSpace(
    family="transformer_lstm",
    methods=(TRANSFORMER_LSTM_METHOD,),
)
RESULT = RetainedResult(
    method=LSTM_METHOD,
    objective=0.5,
    selected_epoch=2,
    completed_epochs=5,
)


def _experiment(*, shift: int = 0) -> ExperimentSemantics:
    return ExperimentSemantics(
        training_window=BlockWindow(
            first_parent_block=100 + shift,
            last_parent_block=199 + shift,
        ),
        validation_window=BlockWindow(
            first_parent_block=220 + shift,
            last_parent_block=249 + shift,
        ),
        context_blocks=200,
        horizon_blocks=5,
        ordered_features=("base_fee", "gas_used"),
    )


def _request(
    space: MethodSpace = LSTM_SPACE,
    *,
    corpus_id: UUID = CORPUS_ID,
) -> TuneRequest:
    return TuneRequest(
        workflow="tune",
        study_id=STUDY_ID,
        corpus_id=corpus_id,
        study_definition=StudyDefinition(experiment=_experiment(), method_space=space),
    )


@pytest.mark.parametrize(
    ("space", "method", "model"),
    [
        (
            LSTM_SPACE,
            LSTM_METHOD,
            LstmDefinition(
                family="lstm",
                hidden=256,
                layers=1,
                head_hidden=128,
                dropout=0.2,
            ),
        ),
        (
            TRANSFORMER_SPACE,
            TRANSFORMER_METHOD,
            TransformerDefinition(
                family="transformer",
                model_width=192,
                attention_heads=4,
                transformer_layers=3,
                feedforward_width=384,
                head_hidden=192,
                dropout=0.2,
            ),
        ),
        (
            TRANSFORMER_LSTM_SPACE,
            TRANSFORMER_LSTM_METHOD,
            TransformerLstmDefinition(
                family="transformer_lstm",
                model_width=192,
                attention_heads=4,
                transformer_layers=3,
                feedforward_width=384,
                lstm_hidden=192,
                lstm_layers=1,
                head_hidden=192,
                dropout=0.2,
            ),
        ),
    ],
)
def test_composes_all_three_method_families(
    space: MethodSpace,
    method: Method,
    model: LstmDefinition | TransformerDefinition | TransformerLstmDefinition,
) -> None:
    request = _request(space)

    pure = training_definition_from_method(request.study_definition.experiment, method)

    assert pure == TrainingDefinition(
        experiment=request.study_definition.experiment,
        model=model,
        optimizer=method.optimizer,
        fit=method.fit,
    )
    assert apply_method(request, method) == pure


def test_retain_publish_and_materialize_selected_training(tmp_path: Path) -> None:
    request = _request()
    first = RetainedResult(
        method=LSTM_METHOD,
        objective=-0.4,
        selected_epoch=3,
        completed_epochs=8,
    )
    duplicate_at_cap = RetainedResult(
        method=LSTM_METHOD,
        objective=-0.4,
        selected_epoch=LSTM_METHOD.fit.max_epochs,
        completed_epochs=LSTM_METHOD.fit.max_epochs,
    )

    retain_result(tmp_path, request, first)
    retain_result(tmp_path, request, duplicate_at_cap)
    progress = tmp_path / "studies" / f".{STUDY_ID}" / "progress.json"
    assert Study.model_validate_json(progress.read_bytes(), strict=True) == Study(
        request=request,
        trials=(first, duplicate_at_cap),
    )

    publish_study(tmp_path, STUDY_ID)
    source = SelectedStudySource(
        kind="selected_study",
        corpus_id=CORPUS_ID,
        study_id=STUDY_ID,
        study_result_index=1,
        experiment=_experiment(shift=1_000),
    )

    selected = materialize_selected_training(tmp_path, source)

    assert not progress.exists()
    assert selected.study_result_index == 1
    assert selected.method == LSTM_METHOD
    assert selected.training_definition == training_definition_from_method(
        source.experiment,
        LSTM_METHOD,
    )


@pytest.mark.parametrize(
    ("selected_epoch", "completed_epochs", "message"),
    [
        (3, 2, "selected_epoch must not exceed completed_epochs"),
        (1, 13, "completed_epochs must not exceed method.fit.max_epochs"),
    ],
)
def test_retained_result_rejects_invalid_epoch_bounds(
    selected_epoch: int,
    completed_epochs: int,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        RetainedResult(
            method=LSTM_METHOD,
            objective=0.5,
            selected_epoch=selected_epoch,
            completed_epochs=completed_epochs,
        )


def test_study_rejects_method_outside_space() -> None:
    outside = LSTM_METHOD.model_copy(update={"dropout": 0.3})

    with pytest.raises(ValidationError, match="Method is outside the MethodSpace"):
        Study(
            request=_request(),
            trials=(
                RetainedResult(
                    method=outside,
                    objective=0.5,
                    selected_epoch=1,
                    completed_epochs=1,
                ),
            ),
        )


def test_retain_result_rejects_conflicting_request(tmp_path: Path) -> None:
    retain_result(tmp_path, _request(), RESULT)

    with pytest.raises(ValueError, match="does not match existing progress"):
        retain_result(tmp_path, _request(corpus_id=OTHER_CORPUS_ID), RESULT)


def test_materialize_selected_training_rejects_corpus_mismatch(tmp_path: Path) -> None:
    canonical = study_json_path(tmp_path, STUDY_ID)
    canonical.parent.mkdir(parents=True)
    canonical.write_text(
        Study(request=_request(), trials=(RESULT,)).model_dump_json(),
        encoding="utf-8",
    )
    source = SelectedStudySource(
        kind="selected_study",
        corpus_id=OTHER_CORPUS_ID,
        study_id=STUDY_ID,
        study_result_index=0,
        experiment=_experiment(),
    )

    with pytest.raises(ValueError, match="Corpus ID does not match"):
        materialize_selected_training(tmp_path, source)


def test_publish_study_rejects_occupied_canonical(tmp_path: Path) -> None:
    retain_result(tmp_path, _request(), RESULT)
    study_json_path(tmp_path, STUDY_ID).write_text("occupied", encoding="utf-8")

    with pytest.raises(FileExistsError):
        publish_study(tmp_path, STUDY_ID)
