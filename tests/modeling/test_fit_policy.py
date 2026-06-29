from __future__ import annotations

from typing import Any, cast

import pytest
import torch

from spice.core.errors import SpiceOperatorError
from spice.metrics import MetricSet
from spice.modeling._fit_policy import (
    CompletedEpoch,
    TrainingFitPolicy,
    require_finite_metrics,
)


def _policy(*, patience: int = 2, min_delta: float = 0.1) -> TrainingFitPolicy:
    return TrainingFitPolicy.create(
        max_epochs=3,
        patience=patience,
        min_delta=min_delta,
    )


def _completed(epoch: int, total_loss: float) -> CompletedEpoch:
    metrics = MetricSet({"total_loss": total_loss})
    return CompletedEpoch(
        epoch=epoch,
        train_metrics=metrics,
        validation_metrics=metrics,
    )


def test_fit_policy_appends_histories_and_uses_strict_min_delta() -> None:
    model = torch.nn.Linear(1, 1)
    policy = _policy()

    first = policy.record_completed_epoch(_completed(1, 1.0), model=cast(Any, model))
    second = policy.record_completed_epoch(_completed(2, 0.95), model=cast(Any, model))

    assert len(policy.train_history) == 2
    assert len(policy.validation_history) == 2
    assert first.progress is not None
    assert first.progress.best_epoch == 1
    assert first.progress.best_validation_loss == 1.0
    assert second.progress is not None
    assert second.progress.best_epoch == 1
    assert second.progress.best_validation_loss == 1.0
    assert second.should_stop is False


def test_fit_policy_tracks_lower_validation_total_loss_as_best() -> None:
    model = torch.nn.Linear(1, 1)
    policy = _policy()

    first = policy.record_completed_epoch(_completed(1, 1.0), model=cast(Any, model))
    model.bias.data.fill_(2.0)
    second = policy.record_completed_epoch(_completed(2, 0.89), model=cast(Any, model))

    assert first.progress is not None
    assert first.progress.best_epoch == 1
    assert second.progress is not None
    assert second.progress.best_epoch == 2
    assert second.progress.best_validation_loss == 0.89
    best_epoch, best_state, best_value = policy.finalized_best()
    assert best_epoch == 2
    assert best_value == 0.89
    assert best_state["bias"].device.type == "cpu"
    assert best_state["bias"].item() == pytest.approx(2.0)


def test_fit_policy_nonfinite_before_best_state_raises_without_append() -> None:
    policy = _policy()

    with pytest.raises(SpiceOperatorError, match="before any valid best state"):
        policy.handle_nonfinite_metrics(
            epoch=1,
            phase="train",
            metrics=MetricSet({"total_loss": float("nan")}),
        )

    assert policy.train_history == []
    assert policy.validation_history == []


def test_fit_policy_nonfinite_after_best_state_stops_without_progress() -> None:
    model = torch.nn.Linear(1, 1)
    policy = _policy()
    policy.record_completed_epoch(_completed(1, 1.0), model=cast(Any, model))

    decision = policy.handle_nonfinite_metrics(
        epoch=2,
        phase="validation",
        metrics=MetricSet({"total_loss": float("nan")}),
    )

    assert decision is not None
    assert decision.should_stop is True
    assert decision.progress is None
    assert decision.early_stop == (2, 1)
    assert len(policy.validation_history) == 1


def test_fit_policy_patience_stop() -> None:
    model = torch.nn.Linear(1, 1)
    policy = _policy(patience=1)

    first = policy.record_completed_epoch(_completed(1, 1.0), model=cast(Any, model))
    second = policy.record_completed_epoch(_completed(2, 1.05), model=cast(Any, model))

    assert first.should_stop is False
    assert second.should_stop is True
    assert second.early_stop == (2, 1)
    assert second.progress is not None
    assert second.progress.best_validation_loss == 1.0


def test_fit_policy_round_trips_resume_state() -> None:
    model = torch.nn.Linear(1, 1)
    policy = _policy()
    policy.record_completed_epoch(_completed(1, 1.0), model=cast(Any, model))

    restored = _policy()
    restored.load_state_dict(policy.state_dict())

    assert restored.best_epoch == 1
    assert restored.epochs_without_improvement == 0
    assert restored.validation_history == [MetricSet({"total_loss": 1.0})]
    assert restored.finalized_best()[2] == 1.0


def test_require_finite_metrics_rejects_nan() -> None:
    with pytest.raises(SpiceOperatorError, match="Non-finite validation metrics"):
        require_finite_metrics(
            MetricSet({"total_loss": float("nan")}),
            phase="validation",
        )
