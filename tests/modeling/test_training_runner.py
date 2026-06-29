from __future__ import annotations

from contextlib import nullcontext
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest
import torch

from spice.config.models import TrainingConfig
from spice.metrics import MetricSet
from spice.modeling._fit_policy import CompletedEpoch
from spice.modeling.batch_plan import BatchRuntimeContext
from spice.modeling.runtime_planning import ModelingRuntimePlan
from spice.modeling.training_runner import (
    TrainingFitSpec,
    run_training_fit,
)
from spice.modeling.training_runner_types import (
    TrainingCallbacks,
    TrainingCheckpoint,
)
from spice.modeling.training_runtime import PreparedTrainingRuntime, TrainingRuntimePlan
from spice.temporal.execution_policy import PreparedActionSpace


class _TinyModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.weight = torch.nn.Parameter(torch.tensor(0.0))


def _training_config(*, max_epochs: int = 2, patience: int = 2) -> TrainingConfig:
    return TrainingConfig.model_validate(
        {
            "learning_rate": 0.01,
            "weight_decay": 0.0,
            "batch_size": 1,
            "max_epochs": max_epochs,
            "early_stopping": {"patience": patience, "min_delta": 0.01},
            "gradient_clip_norm": 1.0,
            "seed": 1,
            "deterministic": True,
            "sequence": {"min_length": 4, "max_length": 64},
        }
    )


def _runtime_plan() -> ModelingRuntimePlan:
    return ModelingRuntimePlan(
        resolved_device=torch.device("cpu"),
        precision="32-true",
        batch_runtime_context=BatchRuntimeContext(batch_size=1),
        deterministic=None,
        seed=0,
    )


def _patch_training_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_plan = _runtime_plan()

    def fake_prepare_training_runtime(model, **_kwargs):
        return PreparedTrainingRuntime(
            fit_model=model,
            batch_plan=TrainingRuntimePlan(
                runtime_plan=runtime_plan,
                train_batch_plan=cast(Any, SimpleNamespace(source=["train"])),
                validation_batch_plan=cast(Any, SimpleNamespace(source=["validation"])),
                prediction_training_state=None,
            ),
        )

    monkeypatch.setattr(
        "spice.modeling.training_runner.prepare_training_runtime",
        fake_prepare_training_runtime,
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.modeling_backend_scope",
        lambda _plan: nullcontext(),
    )


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


def _prepared(*, train: list[int] | None = None, validation: list[int] | None = None):
    return SimpleNamespace(
        execution_policy=SimpleNamespace(name="policy"),
        store=SimpleNamespace(name="store"),
        samples=SimpleNamespace(
            train=_sample_role([0] if train is None else train),
            validation=_sample_role([1] if validation is None else validation),
            test=_sample_role([2]),
        ),
    )


def _fit_spec(
    *,
    model,
    training_config,
) -> TrainingFitSpec:
    return TrainingFitSpec(
        model=model,
        prediction_contract=cast(Any, SimpleNamespace()),
        prepared=cast(Any, _prepared(train=[0], validation=[0])),
        training_config=training_config,
    )


class _FakeLightningModule:
    instances: list[_FakeLightningModule] = []
    model: Any
    policy: Any
    start_epoch: int
    optimizer_state: dict[str, object] | None
    training_config: TrainingConfig

    def __init__(self, **kwargs: Any) -> None:
        self.__dict__.update(kwargs)
        self.fit_calls: list[tuple[object, object]] = []
        type(self).instances.append(self)

    def finalized_best(self):
        best_epoch, best_state, best_value = self.policy.finalized_best()
        return SimpleNamespace(
            best_epoch=best_epoch,
            best_state=best_state,
            best_validation_loss=best_value,
        )


class _FakeTrainer:
    instances: list[_FakeTrainer] = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        type(self).instances.append(self)

    def fit(self, module: Any, *, train_dataloaders, val_dataloaders) -> None:
        module.fit_calls.append((train_dataloaders, val_dataloaders))
        first_loss = 0.8 if module.start_epoch > 1 else 1.0
        module.model.weight.data.fill_(first_loss)
        validation_metrics = MetricSet({"total_loss": first_loss})
        module.policy.record_completed_epoch(
            CompletedEpoch(
                epoch=module.start_epoch,
                train_metrics=MetricSet({"total_loss": first_loss}),
                validation_metrics=validation_metrics,
            ),
            model=module.model,
        )
        if module.training_config.max_epochs > module.start_epoch:
            module.model.weight.data.fill_(2.0)
            validation_metrics = MetricSet({"total_loss": 1.005})
            module.policy.record_completed_epoch(
                CompletedEpoch(
                    epoch=module.start_epoch + 1,
                    train_metrics=MetricSet({"total_loss": 1.005}),
                    validation_metrics=validation_metrics,
                ),
                model=module.model,
            )


def _patch_lightning(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeLightningModule.instances.clear()
    _FakeTrainer.instances.clear()
    monkeypatch.setattr("spice.modeling.training_runner.SpiceLightningModule", _FakeLightningModule)
    monkeypatch.setattr("spice.modeling.training_runner.pl.Trainer", _FakeTrainer)


def test_training_fit_uses_lightning_trainer_and_restores_best_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_training_runtime(monkeypatch)
    _patch_lightning(monkeypatch)
    model = _TinyModel()

    result = run_training_fit(
        _fit_spec(
            model=cast(Any, model),
            training_config=_training_config(max_epochs=2, patience=1),
        )
    )

    assert _FakeTrainer.instances[0].kwargs == {
        "accelerator": "gpu",
        "devices": 1,
        "precision": "32-true",
        "max_epochs": 2,
        "num_sanity_val_steps": 0,
        "use_distributed_sampler": False,
        "logger": False,
        "enable_checkpointing": False,
        "enable_progress_bar": False,
        "deterministic": True,
    }
    assert _FakeLightningModule.instances[0].fit_calls == [(["train"], ["validation"])]
    assert result.best_epoch == 1
    assert result.best_validation_loss == 1.0
    assert len(result.train_history) == 2
    assert len(result.validation_history) == 2
    assert model.weight.item() == 1.0
    assert result.runtime_plan.seed == 0


def test_training_fit_resumes_from_checkpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_training_runtime(monkeypatch)
    _patch_lightning(monkeypatch)
    model = _TinyModel()
    checkpoint = TrainingCheckpoint(
        completed_epoch=1,
        model_state={"weight": torch.tensor(1.0)},
        optimizer_state={"epoch": 1},
        policy_state={
            "train_history": [{"total_loss": 1.0}],
            "validation_history": [{"total_loss": 1.0}],
            "best_state": {"weight": torch.tensor(1.0)},
            "best_epoch": 1,
            "epochs_without_improvement": 0,
        },
    )
    spec = _fit_spec(
        model=model,
        training_config=_training_config(max_epochs=2, patience=2),
    )
    spec.checkpoint = checkpoint

    result = run_training_fit(
        spec,
        callbacks=TrainingCallbacks(),
    )

    module = _FakeLightningModule.instances[0]
    assert module.start_epoch == 2
    assert module.optimizer_state == {"epoch": 1}
    assert _FakeTrainer.instances[0].kwargs["max_epochs"] == 1
    assert result.best_epoch == 2
    assert len(result.train_history) == 2
    assert model.weight.item() == pytest.approx(0.8)


def test_training_fit_rejects_empty_train_or_validation_samples() -> None:
    with pytest.raises(ValueError, match="Train and validation sample selections"):
        run_training_fit(
            TrainingFitSpec(
                model=cast(Any, _TinyModel()),
                prediction_contract=cast(Any, SimpleNamespace()),
                prepared=cast(Any, _prepared(train=[], validation=[0])),
                training_config=_training_config(max_epochs=1),
            )
        )
