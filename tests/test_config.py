from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

import pytest
from pydantic import ValidationError

from fable.config import (
    METHOD_ADAPTER,
    WORKFLOW_REQUEST_ADAPTER,
    AdamWMethod,
    BlockWindow,
    CorpusDefinition,
    EvaluateRequest,
    ExperimentSemantics,
    FitMethod,
    LstmCapacity,
    LstmMethod,
    LstmMethodSpace,
    StudyDefinition,
    TransformerCapacity,
)

STUDY_ID = UUID("00000000-0000-4000-8000-000000000002")
CORPUS_ID = UUID("00000000-0000-4000-8000-000000000001")
ARTIFACT_ID = UUID("00000000-0000-4000-8000-000000000003")
EVALUATION_ID = UUID("00000000-0000-4000-8000-000000000004")


def _window(first: int = 210, last: int = 249) -> BlockWindow:
    return BlockWindow(
        first_parent_block=first,
        last_parent_block=last,
    )


def _experiment() -> ExperimentSemantics:
    return ExperimentSemantics(
        training_window=_window(100, 199),
        validation_window=_window(),
        context_blocks=20,
        horizon_blocks=10,
        ordered_features=("base_fee", "gas_utilization"),
    )


def _method() -> LstmMethod:
    return LstmMethod(
        family="lstm",
        capacity=LstmCapacity(hidden=32, layers=1, head_hidden=16),
        dropout=0.2,
        optimizer=AdamWMethod(learning_rate=0.001, weight_decay=0.0),
        training_batch=48,
        fit=FitMethod(
            accumulation=2,
            gradient_clip_norm=0.75,
            scheduler="none",
            seed=17,
            max_epochs=9,
            validate_every_completed_epoch=2,
            patience=3,
            min_delta=0.01,
            improvement="strict_lower",
            restore="earliest_best",
        ),
    )


def _invalid_cases() -> tuple[tuple[Callable[..., object], dict[str, object], str], ...]:
    experiment = _experiment()
    method = _method()
    method_space = LstmMethodSpace(family="lstm", methods=(method,))
    return (
        (
            CorpusDefinition,
            {"chain_id": 1, "first_block": 2, "last_block": 1},
            "last_block must not precede first_block",
        ),
        (
            lambda **payload: METHOD_ADAPTER.validate_python(payload),
            {**method.model_dump(), "family": "cnn"},
            "cnn",
        ),
        (
            lambda **payload: WORKFLOW_REQUEST_ADAPTER.validate_python(payload),
            {
                "workflow": "tune",
                "study_id": STUDY_ID,
                "corpus_id": CORPUS_ID,
                "study_definition": StudyDefinition(
                    experiment=experiment,
                    method_space=method_space,
                ).model_dump(),
            },
            "tune",
        ),
        (
            TransformerCapacity,
            {
                "model_width": 31,
                "attention_heads": 1,
                "transformer_layers": 1,
                "feedforward_width": 32,
                "head_hidden": 8,
            },
            "model_width must be even",
        ),
        (
            TransformerCapacity,
            {
                "model_width": 30,
                "attention_heads": 4,
                "transformer_layers": 1,
                "feedforward_width": 32,
                "head_hidden": 8,
            },
            "model_width must be divisible by attention_heads",
        ),
        (
            LstmMethodSpace,
            {**method_space.model_dump(), "methods": (method, method)},
            "methods must not contain duplicates",
        ),
        (
            ExperimentSemantics,
            {
                **experiment.model_dump(),
                "validation_window": BlockWindow(
                    first_parent_block=209,
                    last_parent_block=249,
                ),
            },
            "validation_window must follow complete training outcomes",
        ),
    )


@pytest.mark.parametrize(("value_type", "payload", "message"), _invalid_cases())
def test_domain_contract_rejects_invalid_values(
    value_type: Callable[..., object],
    payload: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        value_type(**payload)


def test_evaluate_request_serializes_only_a_testing_window() -> None:
    request = EvaluateRequest(
        workflow="evaluate",
        evaluation_id=EVALUATION_ID,
        artifact_id=ARTIFACT_ID,
        corpus_id=CORPUS_ID,
        testing_window=_window(300, 349),
    )

    assert request.model_dump()["testing_window"] == {
        "first_parent_block": 300,
        "last_parent_block": 349,
    }
