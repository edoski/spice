from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest
import torch

from spice.metrics import MetricSet
from spice.modeling.batch_plan import BatchRuntimeContext
from spice.modeling.persisted_training import run_persisted_training, run_trial_training
from spice.modeling.runtime_planning import ModelingRuntimePlan
from spice.modeling.training_run import TrainingRunResult
from spice.modeling.training_runner import TrainingResult
from spice.modeling.training_runner_types import TrainingCheckpoint
from spice.temporal.execution_policy import PreparedActionSpace


def _sample_role(indices: list[int]):
    sample_indices = np.array(indices, dtype=np.int64)
    action_space = PreparedActionSpace(
        sample_indices=sample_indices,
        max_candidate_slots=1,
        action_mask=np.ones((sample_indices.shape[0], 1), dtype=np.bool_),
    )
    return SimpleNamespace(
        sample_indices=sample_indices,
        action_space=action_space,
        temporal_facts=SimpleNamespace(action_space=action_space),
    )


def _training_run(*, model: object) -> TrainingRunResult:
    runtime_plan = ModelingRuntimePlan(
        resolved_device=torch.device("cpu"),
        precision="32-true",
        batch_runtime_context=BatchRuntimeContext(batch_size=1),
        deterministic=None,
        seed=0,
    )
    prepared = SimpleNamespace(
        execution_policy=SimpleNamespace(),
        store=SimpleNamespace(),
        samples=SimpleNamespace(
            validation=_sample_role([0]),
            test=_sample_role([1]),
        ),
    )
    return TrainingRunResult(
        model=cast(Any, model),
        prepared=cast(Any, prepared),
        training_result=TrainingResult(
            best_epoch=1,
            objective_metric_id="score",
            best_objective_value=1.0,
            train_history=[MetricSet({"score": 1.0})],
            validation_history=[MetricSet({"score": 1.0})],
            objective_history=[MetricSet({"score": 1.0})],
            prediction_training_state=object(),
            runtime_plan=runtime_plan,
        ),
    )


def _spec() -> SimpleNamespace:
    return SimpleNamespace(
        model=SimpleNamespace(),
        prediction_contract=SimpleNamespace(),
        training=SimpleNamespace(),
    )


def _patch_persisted_training(monkeypatch: pytest.MonkeyPatch, *, training_model, loaded_model):
    training_run = _training_run(model=training_model)
    evaluated_models: list[object] = []

    monkeypatch.setattr(
        "spice.modeling.persisted_training.run_training",
        lambda *_args, **_kwargs: training_run,
    )
    monkeypatch.setattr(
        "spice.modeling.persisted_training.build_training_artifact_manifest",
        lambda *_args, **_kwargs: SimpleNamespace(id="manifest"),
    )
    monkeypatch.setattr(
        "spice.modeling.persisted_training.persist_training_artifact",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "spice.modeling.persisted_training.load_training_artifact",
        lambda *_args, **_kwargs: SimpleNamespace(model=loaded_model),
    )
    monkeypatch.setattr(
        "spice.modeling.persisted_training.write_training_state",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "spice.modeling.persisted_training.iter_epoch_records",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(
        "spice.modeling.persisted_training.build_training_runtime_summary",
        lambda *_args, best_validation_metrics, test_metrics, **_kwargs: SimpleNamespace(
            best_validation_metrics=best_validation_metrics,
            test_metrics=test_metrics,
        ),
    )

    def fake_score_prediction_metrics(metric_spec):
        evaluated_models.append(metric_spec.model)
        assert metric_spec.runtime_plan is training_run.training_result.runtime_plan
        assert (
            metric_spec.prediction_training_state
            is training_run.training_result.prediction_training_state
        )
        return MetricSet({"score": float(len(evaluated_models))})

    monkeypatch.setattr(
        "spice.modeling.persisted_training.score_prediction_metrics",
        fake_score_prediction_metrics,
    )
    return evaluated_models


def test_persisted_training_split_metrics_use_reloaded_artifact_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    training_model = object()
    loaded_model = object()
    evaluated_models = _patch_persisted_training(
        monkeypatch,
        training_model=training_model,
        loaded_model=loaded_model,
    )

    run = run_persisted_training(
        tmp_path / "history.parquet",
        spec=cast(Any, _spec()),
        artifact_dir=tmp_path / "artifact",
    )

    assert evaluated_models == [loaded_model, loaded_model]
    assert run.artifact_dir == tmp_path / "artifact"


def test_trial_training_split_metrics_use_training_run_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    training_model = object()
    loaded_model = object()
    evaluated_models = _patch_persisted_training(
        monkeypatch,
        training_model=training_model,
        loaded_model=loaded_model,
    )

    run_trial_training(
        tmp_path / "history.parquet",
        spec=cast(Any, _spec()),
    )

    assert evaluated_models == [training_model, training_model]


def test_persisted_training_resumes_and_rewrites_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact_dir = tmp_path / "artifact"
    saved = TrainingCheckpoint(
        completed_epoch=1,
        model_state={"weight": torch.tensor(1.0)},
        optimizer_state={"epoch": 1},
        policy_state={
            "train_history": [{"score": 1.0}],
            "validation_history": [{"score": 1.0}],
            "objective_history": [{"score": 1.0}],
            "best_state": {"weight": torch.tensor(1.0)},
            "best_epoch": 1,
            "epochs_without_improvement": 0,
        },
    )
    checkpoint_path = artifact_dir / ".spice" / "training_checkpoint.pt"
    checkpoint_path.parent.mkdir(parents=True)
    torch.save(
        {
            "completed_epoch": saved.completed_epoch,
            "model_state": saved.model_state,
            "optimizer_state": saved.optimizer_state,
            "policy_state": saved.policy_state,
        },
        checkpoint_path,
    )

    training_run = _training_run(model=object())
    seen_checkpoint: list[TrainingCheckpoint | None] = []

    def fake_run_training(*_args, checkpoint=None, callbacks=None, **_kwargs):
        seen_checkpoint.append(checkpoint)
        assert callbacks is not None
        callbacks.on_checkpoint(
            TrainingCheckpoint(
                completed_epoch=2,
                model_state={"weight": torch.tensor(2.0)},
                optimizer_state={"epoch": 2},
                policy_state=saved.policy_state,
            )
        )
        return training_run

    monkeypatch.setattr("spice.modeling.persisted_training.run_training", fake_run_training)
    monkeypatch.setattr(
        "spice.modeling.persisted_training.build_training_artifact_manifest",
        lambda *_args, **_kwargs: SimpleNamespace(id="manifest"),
    )
    monkeypatch.setattr(
        "spice.modeling.persisted_training.persist_training_artifact",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "spice.modeling.persisted_training.load_training_artifact",
        lambda *_args, **_kwargs: SimpleNamespace(model=object()),
    )
    monkeypatch.setattr(
        "spice.modeling.persisted_training.score_prediction_metrics",
        lambda *_args, **_kwargs: MetricSet({"score": 1.0}),
    )
    monkeypatch.setattr(
        "spice.modeling.persisted_training.build_training_runtime_summary",
        lambda *_args, **_kwargs: SimpleNamespace(),
    )
    monkeypatch.setattr(
        "spice.modeling.persisted_training.write_training_state",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "spice.modeling.persisted_training.iter_epoch_records",
        lambda *_args, **_kwargs: [],
    )

    run_persisted_training(
        tmp_path / "history.parquet",
        spec=cast(Any, _spec()),
        artifact_dir=artifact_dir,
    )

    assert seen_checkpoint[0] is not None
    assert seen_checkpoint[0].completed_epoch == saved.completed_epoch
    assert seen_checkpoint[0].optimizer_state == saved.optimizer_state
    assert not checkpoint_path.exists()
