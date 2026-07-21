"""Fresh request constructors."""

from __future__ import annotations

from uuid import UUID, uuid4

from .config import (
    BlockWindow,
    EvaluateRequest,
    StudyDefinition,
    TrainingSource,
    TrainRequest,
    TuneRequest,
)


def fresh_train_request(source: TrainingSource) -> TrainRequest:
    return TrainRequest(workflow="train", artifact_id=uuid4(), source=source)


def fresh_tune_request(corpus_id: UUID, study_definition: StudyDefinition) -> TuneRequest:
    return TuneRequest(
        workflow="tune",
        study_id=uuid4(),
        corpus_id=corpus_id,
        study_definition=study_definition,
    )


def fresh_evaluate_request(
    artifact_id: UUID,
    corpus_id: UUID,
    testing_window: BlockWindow,
) -> EvaluateRequest:
    return EvaluateRequest(
        workflow="evaluate",
        evaluation_id=uuid4(),
        artifact_id=artifact_id,
        corpus_id=corpus_id,
        testing_window=testing_window,
    )
