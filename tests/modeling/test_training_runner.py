from __future__ import annotations

from contextlib import nullcontext
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from spice.config.models import TrainingConfig
from spice.core.errors import SpiceOperatorError
from spice.modeling._runtime import CudaModelingRuntime
from spice.modeling.objective_metrics import CompiledObjectiveMetricSource
from spice.modeling.representations import RepresentationRuntimeContext
from spice.modeling.training_runner import (
    TrainingCallbacks,
    TrainingFitSpec,
    TrainingMetricEvaluationSpec,
    evaluate_training_metrics,
    run_training_fit,
)
from spice.modeling.training_runtime import TrainingRuntimePlan
from spice.objectives import CompiledObjectiveContract
from spice.prediction import MetricSet


class _TinyModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.weight = torch.nn.Parameter(torch.tensor(0.0))


def _training_config(*, max_epochs: int = 2) -> TrainingConfig:
    return TrainingConfig.model_validate(
        {
            "learning_rate": 0.01,
            "weight_decay": 0.0,
            "batch_size": 1,
            "max_epochs": max_epochs,
            "early_stopping": {"patience": 2, "min_delta": 0.01},
            "gradient_clip_norm": 1.0,
            "seed": 1,
            "deterministic": True,
            "log_every_n_steps": 1,
        }
    )


def _objective_contract() -> CompiledObjectiveContract:
    return CompiledObjectiveContract(
        objective_id="validation",
        metric_id="score",
        direction="maximize",
        benchmark_id=None,
        config_payload={},
    )


def _objective_metric_source(evaluate_metrics_fn=None) -> CompiledObjectiveMetricSource:
    return CompiledObjectiveMetricSource(
        evaluate_metrics_fn=evaluate_metrics_fn
        or (lambda validation_metrics, context: validation_metrics),
    )


def _patch_training_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = CudaModelingRuntime(
        resolved_device=torch.device("cpu"),
        representation_runtime_context=RepresentationRuntimeContext(
            batch_size=1,
            available_host_memory_bytes=1024,
        ),
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.build_cuda_modeling_runtime",
        lambda **_: runtime,
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.resolve_model_training_precision",
        lambda **_: "fp32",
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.resolve_model_compile_enabled",
        lambda **_: False,
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.configure_torch_backends",
        lambda **_: nullcontext(),
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.plan_training_runtime",
        lambda *_, base_runtime_context, **__: TrainingRuntimePlan(
            runtime_context=base_runtime_context,
            prediction_training_state=None,
        ),
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.build_prediction_batch_plan",
        lambda *_, **__: SimpleNamespace(source=[0]),
    )


def _fit_spec(
    tmp_path,
    *,
    model,
    objective_contract,
    training_config,
    objective_metric_source=None,
) -> TrainingFitSpec:
    return TrainingFitSpec(
        model=model,
        model_config=SimpleNamespace(),
        prediction_contract=SimpleNamespace(fit_training_state=lambda *_, **__: None),
        representation_contract=SimpleNamespace(),
        objective_contract=objective_contract,
        objective_metric_source=objective_metric_source or _objective_metric_source(),
        execution_policy=SimpleNamespace(),
        store=SimpleNamespace(),
        train_sample_indices=np.array([0], dtype=np.int64),
        validation_sample_indices=np.array([0], dtype=np.int64),
        training_config=training_config,
    )


def test_training_best_state_and_best_epoch_ignore_sub_delta_best(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class TinyModel(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.weight = torch.nn.Parameter(torch.tensor(0.0))

    objective_values = [1.0, 1.005]
    epoch_state = {"epoch": 0}

    def fake_run_epoch(model, *, training, **_kwargs):
        if training:
            epoch_state["epoch"] += 1
            model.weight.data.fill_(float(epoch_state["epoch"]))
            return MetricSet({"score": objective_values[epoch_state["epoch"] - 1]})
        return MetricSet({"score": objective_values[epoch_state["epoch"] - 1]})

    runtime = CudaModelingRuntime(
        resolved_device=torch.device("cpu"),
        representation_runtime_context=RepresentationRuntimeContext(
            batch_size=1,
            available_host_memory_bytes=1024,
        ),
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.build_cuda_modeling_runtime",
        lambda **_: runtime,
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.resolve_model_training_precision",
        lambda **_: "fp32",
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.resolve_model_compile_enabled",
        lambda **_: False,
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.configure_torch_backends",
        lambda **_: nullcontext(),
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.plan_training_runtime",
        lambda *_, base_runtime_context, **__: TrainingRuntimePlan(
            runtime_context=base_runtime_context,
            prediction_training_state=None,
        ),
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.build_prediction_batch_plan",
        lambda *_, **__: SimpleNamespace(source=[0]),
    )
    monkeypatch.setattr("spice.modeling.training_runner.run_epoch", fake_run_epoch)

    prediction_contract = SimpleNamespace(fit_training_state=lambda *_, **__: None)
    objective_contract = CompiledObjectiveContract(
        objective_id="validation",
        metric_id="score",
        direction="maximize",
        benchmark_id=None,
        config_payload={},
    )
    training_config = TrainingConfig.model_validate(
        {
            "learning_rate": 0.01,
            "weight_decay": 0.0,
            "batch_size": 1,
            "max_epochs": 2,
            "early_stopping": {"patience": 2, "min_delta": 0.01},
            "gradient_clip_norm": 1.0,
            "seed": 1,
            "deterministic": True,
            "log_every_n_steps": 1,
        }
    )

    model = TinyModel()
    result = run_training_fit(
        TrainingFitSpec(
            model=model,
            model_config=SimpleNamespace(),
            prediction_contract=prediction_contract,
            representation_contract=SimpleNamespace(),
            objective_contract=objective_contract,
            objective_metric_source=_objective_metric_source(),
            execution_policy=SimpleNamespace(),
            store=SimpleNamespace(),
            train_sample_indices=np.array([0], dtype=np.int64),
            validation_sample_indices=np.array([0], dtype=np.int64),
            training_config=training_config,
        )
    )

    assert result.best_epoch == 1
    assert result.best_objective_value == 1.0
    assert model.weight.item() == 1.0


def test_training_stops_on_nonfinite_validation_metrics_and_preserves_best_state(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class TinyModel(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.weight = torch.nn.Parameter(torch.tensor(0.0))

    epoch_state = {"epoch": 0}
    early_stop_calls: list[tuple[int, int]] = []

    def fake_run_epoch(model, *, training, **_kwargs):
        if training:
            epoch_state["epoch"] += 1
            model.weight.data.fill_(float(epoch_state["epoch"]))
            return MetricSet({"score": 1.0})
        if epoch_state["epoch"] == 2:
            return MetricSet({"score": float("nan")})
        return MetricSet({"score": 1.0})

    runtime = CudaModelingRuntime(
        resolved_device=torch.device("cpu"),
        representation_runtime_context=RepresentationRuntimeContext(
            batch_size=1,
            available_host_memory_bytes=1024,
        ),
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.build_cuda_modeling_runtime",
        lambda **_: runtime,
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.resolve_model_training_precision",
        lambda **_: "fp32",
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.resolve_model_compile_enabled",
        lambda **_: False,
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.configure_torch_backends",
        lambda **_: nullcontext(),
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.plan_training_runtime",
        lambda *_, base_runtime_context, **__: TrainingRuntimePlan(
            runtime_context=base_runtime_context,
            prediction_training_state=None,
        ),
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.build_prediction_batch_plan",
        lambda *_, **__: SimpleNamespace(source=[0]),
    )
    monkeypatch.setattr("spice.modeling.training_runner.run_epoch", fake_run_epoch)

    prediction_contract = SimpleNamespace(fit_training_state=lambda *_, **__: None)
    objective_contract = CompiledObjectiveContract(
        objective_id="validation",
        metric_id="score",
        direction="maximize",
        benchmark_id=None,
        config_payload={},
    )
    training_config = TrainingConfig.model_validate(
        {
            "learning_rate": 0.01,
            "weight_decay": 0.0,
            "batch_size": 1,
            "max_epochs": 2,
            "early_stopping": {"patience": 2, "min_delta": 0.01},
            "gradient_clip_norm": 1.0,
            "seed": 1,
            "deterministic": True,
            "log_every_n_steps": 1,
        }
    )

    model = TinyModel()
    result = run_training_fit(
        TrainingFitSpec(
            model=model,
            model_config=SimpleNamespace(),
            prediction_contract=prediction_contract,
            representation_contract=SimpleNamespace(),
            objective_contract=objective_contract,
            objective_metric_source=_objective_metric_source(),
            execution_policy=SimpleNamespace(),
            store=SimpleNamespace(),
            train_sample_indices=np.array([0], dtype=np.int64),
            validation_sample_indices=np.array([0], dtype=np.int64),
            training_config=training_config,
        ),
        callbacks=TrainingCallbacks(
            on_early_stop=lambda epoch, best_epoch: early_stop_calls.append(
                (epoch, best_epoch)
            ),
        ),
    )

    assert result.best_epoch == 1
    assert result.best_objective_value == 1.0
    assert len(result.train_history) == 1
    assert len(result.validation_history) == 1
    assert len(result.objective_history) == 1
    assert model.weight.item() == 1.0
    assert early_stop_calls == [(2, 1)]


@pytest.mark.parametrize("phase", ["train", "validation", "objective"])
def test_training_raises_on_nonfinite_metrics_before_first_best_state(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    phase: str,
) -> None:
    epoch_state = {"epoch": 0}

    def fake_run_epoch(model, *, training, **_kwargs):
        if training:
            epoch_state["epoch"] += 1
            model.weight.data.fill_(float(epoch_state["epoch"]))
            value = float("nan") if phase == "train" else 1.0
        else:
            value = float("nan") if phase == "validation" else 1.0
        return MetricSet({"score": value})

    _patch_training_runtime(monkeypatch)
    monkeypatch.setattr("spice.modeling.training_runner.run_epoch", fake_run_epoch)

    def evaluate_objective(validation_metrics, context):
        if phase == "objective":
            return MetricSet({"score": float("nan")})
        return validation_metrics

    with pytest.raises(
        SpiceOperatorError,
        match="before any valid best state",
    ):
        run_training_fit(
            _fit_spec(
                tmp_path,
                model=_TinyModel(),
                objective_contract=_objective_contract(),
                objective_metric_source=_objective_metric_source(evaluate_objective),
                training_config=_training_config(),
            )
        )


@pytest.mark.parametrize("phase", ["train", "objective"])
def test_training_stops_on_nonfinite_metrics_after_best_state(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    phase: str,
) -> None:
    epoch_state = {"epoch": 0}
    early_stop_calls: list[tuple[int, int]] = []

    def fake_run_epoch(model, *, training, **_kwargs):
        if training:
            epoch_state["epoch"] += 1
            model.weight.data.fill_(float(epoch_state["epoch"]))
            value = float("nan") if phase == "train" and epoch_state["epoch"] == 2 else 1.0
        else:
            value = 1.0
        return MetricSet({"score": value})

    _patch_training_runtime(monkeypatch)
    monkeypatch.setattr("spice.modeling.training_runner.run_epoch", fake_run_epoch)

    def evaluate_objective(validation_metrics, context):
        if phase == "objective" and epoch_state["epoch"] == 2:
            return MetricSet({"score": float("nan")})
        return validation_metrics

    model = _TinyModel()
    result = run_training_fit(
        _fit_spec(
            tmp_path,
            model=model,
            objective_contract=_objective_contract(),
            objective_metric_source=_objective_metric_source(evaluate_objective),
            training_config=_training_config(),
        ),
        callbacks=TrainingCallbacks(
            on_early_stop=lambda epoch, best_epoch: early_stop_calls.append(
                (epoch, best_epoch)
            ),
        ),
    )

    assert result.best_epoch == 1
    assert result.best_objective_value == 1.0
    assert len(result.train_history) == 1
    assert len(result.validation_history) == 1
    assert len(result.objective_history) == 1
    assert model.weight.item() == 1.0
    assert early_stop_calls == [(2, 1)]


def test_evaluate_training_metrics_uses_batch_plan_and_prediction_training_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = CudaModelingRuntime(
        resolved_device=torch.device("cpu"),
        representation_runtime_context=RepresentationRuntimeContext(
            batch_size=1,
            available_host_memory_bytes=1024,
        ),
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.build_cuda_modeling_runtime",
        lambda **_: runtime,
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.resolve_model_training_precision",
        lambda **_: "fp32",
    )
    monkeypatch.setattr(
        "spice.modeling.training_runner.configure_torch_backends",
        lambda **_: nullcontext(),
    )

    seen_training_states: list[object | None] = []

    class Accumulator:
        def __init__(self) -> None:
            self.values: list[float] = []

        def update(self, batch_state) -> None:
            self.values.append(batch_state["score"])

        def finalize(self) -> MetricSet:
            return MetricSet({"score": sum(self.values)})

    prediction_state = object()
    prediction_contract = SimpleNamespace(
        create_epoch_accumulator=Accumulator,
        compute_batch_loss_and_state=lambda outputs, targets, training_state: (
            seen_training_states.append(training_state) or torch.tensor(0.0),
            {"score": 2.5},
        ),
    )

    forward_calls = []

    def fake_run_planned_prediction_forward(_model, *, on_outputs, **kwargs):
        forward_calls.append(kwargs)
        on_outputs(SimpleNamespace(targets="metrics"), outputs=SimpleNamespace())

    monkeypatch.setattr(
        "spice.modeling.training_runner.run_planned_prediction_forward",
        fake_run_planned_prediction_forward,
    )

    metrics = evaluate_training_metrics(
        TrainingMetricEvaluationSpec(
            model=_TinyModel(),
            model_config=SimpleNamespace(),
            prediction_contract=prediction_contract,
            execution_policy=SimpleNamespace(),
            representation_contract=SimpleNamespace(),
            store=SimpleNamespace(),
            sample_indices=np.array([0], dtype=np.int64),
            prediction_training_state=prediction_state,
            training_config=_training_config(),
        )
    )

    assert forward_calls[0]["base_runtime_context"] is runtime.representation_runtime_context
    assert forward_calls[0]["seed"] == 1
    assert seen_training_states == [prediction_state]
    assert metrics.require("score") == 2.5
