from __future__ import annotations

from contextlib import nullcontext
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from spice.config.models import TrainingConfig
from spice.modeling._runtime import CudaModelingRuntime
from spice.modeling.representations import RepresentationRuntimeContext
from spice.modeling.training import train_model
from spice.objectives import CompiledObjectiveContract
from spice.prediction import MetricSet


def test_training_checkpoint_state_and_best_epoch_ignore_sub_delta_best(
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
    monkeypatch.setattr("spice.modeling.training.build_cuda_modeling_runtime", lambda **_: runtime)
    monkeypatch.setattr(
        "spice.modeling.training.resolve_model_training_precision",
        lambda **_: "fp32",
    )
    monkeypatch.setattr("spice.modeling.training.resolve_model_compile_enabled", lambda **_: False)
    monkeypatch.setattr(
        "spice.modeling.training.configure_torch_backends",
        lambda **_: nullcontext(),
    )
    monkeypatch.setattr(
        "spice.modeling.training._planned_training_runtime_context",
        lambda *_, base_runtime_context, **__: base_runtime_context,
    )
    monkeypatch.setattr(
        "spice.modeling.training.build_prediction_batch_source",
        lambda *_, **__: [0],
    )
    monkeypatch.setattr("spice.modeling.training._run_epoch", fake_run_epoch)

    prediction_contract = SimpleNamespace(fit_training_state=lambda *_, **__: None)
    objective_contract = CompiledObjectiveContract(
        objective_id="validation",
        metric_id="score",
        direction="maximize",
        benchmark_id=None,
        config_payload={},
        evaluate_metrics_fn=lambda validation_metrics, context: validation_metrics,
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
    result = train_model(
        model,
        model_config=SimpleNamespace(),
        prediction_contract=prediction_contract,
        representation_contract=SimpleNamespace(),
        objective_contract=objective_contract,
        execution_policy=SimpleNamespace(),
        store=SimpleNamespace(),
        train_sample_indices=np.array([0], dtype=np.int64),
        validation_sample_indices=np.array([0], dtype=np.int64),
        training_config=training_config,
        artifact_dir=tmp_path,
    )

    assert result.best_epoch == 1
    assert result.best_objective_value == 1.0
    assert model.weight.item() == 1.0
