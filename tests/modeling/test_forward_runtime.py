from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import torch

from spice.modeling.forward_runtime import (
    run_planned_model_input_forward,
    run_planned_prediction_forward,
)
from spice.modeling.representations import RepresentationRuntimeContext


def test_planned_model_input_forward_uses_host_warmup_then_measured_budget(
    monkeypatch,
) -> None:
    runtime_context = RepresentationRuntimeContext(
        batch_size=2,
        available_host_memory_bytes=1024,
        available_device_memory_bytes=999,
    )
    sources = [object(), object()]
    budgets: list[int | None] = []

    def fake_build_model_input_batch_plan(*_args, runtime_context, **_kwargs):
        budgets.append(runtime_context.available_device_memory_bytes)
        return SimpleNamespace(source=sources[len(budgets) - 1])

    measured_sources = []
    forward_sources = []

    monkeypatch.setattr(
        "spice.modeling.forward_runtime.build_model_input_batch_plan",
        fake_build_model_input_batch_plan,
    )
    monkeypatch.setattr(
        "spice.modeling.forward_runtime.measure_forward_device_resident_budget",
        lambda _model, *, loader, **_kwargs: measured_sources.append(loader) or 77,
    )
    monkeypatch.setattr(
        "spice.modeling.forward_runtime.run_model_forward_pass",
        lambda _model, *, loader, **_kwargs: forward_sources.append(loader),
    )

    run_planned_model_input_forward(
        SimpleNamespace(),
        store=SimpleNamespace(),
        sample_indices=np.array([0], dtype=np.int64),
        representation_contract=SimpleNamespace(),
        base_runtime_context=runtime_context,
        resolved_device=torch.device("cpu"),
        precision="32-true",
        seed=3,
        on_outputs=lambda _batch, _outputs: None,
    )

    assert budgets == [0, 77]
    assert measured_sources == [sources[0]]
    assert forward_sources == [sources[1]]


def test_planned_prediction_forward_preserves_callback_and_final_source(
    monkeypatch,
) -> None:
    runtime_context = RepresentationRuntimeContext(
        batch_size=2,
        available_host_memory_bytes=1024,
        available_device_memory_bytes=999,
    )
    sources = [[SimpleNamespace(name="warmup")], [SimpleNamespace(name="final")]]
    budgets: list[int | None] = []

    def fake_build_prediction_batch_plan(*_args, runtime_context, **_kwargs):
        budgets.append(runtime_context.available_device_memory_bytes)
        return SimpleNamespace(source=sources[len(budgets) - 1])

    seen_batches = []

    def fake_forward(_model, *, loader, on_outputs, **_kwargs):
        for batch in loader:
            on_outputs(batch, SimpleNamespace())

    monkeypatch.setattr(
        "spice.modeling.forward_runtime.build_prediction_batch_plan",
        fake_build_prediction_batch_plan,
    )
    monkeypatch.setattr(
        "spice.modeling.forward_runtime.measure_forward_device_resident_budget",
        lambda _model, *, loader, **_kwargs: 55 if loader == sources[0] else 0,
    )
    monkeypatch.setattr(
        "spice.modeling.forward_runtime.run_model_forward_pass",
        fake_forward,
    )

    run_planned_prediction_forward(
        SimpleNamespace(),
        store=SimpleNamespace(),
        sample_indices=np.array([0], dtype=np.int64),
        representation_contract=SimpleNamespace(),
        prediction_contract=SimpleNamespace(),
        execution_policy=SimpleNamespace(),
        base_runtime_context=runtime_context,
        resolved_device=torch.device("cpu"),
        precision="32-true",
        seed=3,
        on_outputs=lambda batch, _outputs: seen_batches.append(batch),
    )

    assert budgets == [0, 55]
    assert seen_batches == sources[1]
