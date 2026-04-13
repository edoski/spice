from __future__ import annotations

from types import SimpleNamespace

import torch

from spice.config import CompileMode
from spice.modeling._runtime import resolve_compile_enabled


def test_resolve_compile_enabled_skips_auto_compile_on_small_cuda_gpu(
    tmp_path,
    monkeypatch,
    load_test_train_config,
    model_workflow_override,
) -> None:
    config = load_test_train_config(tmp_path, override=model_workflow_override())

    monkeypatch.setattr("spice.modeling._runtime.resolve_auto_compile", lambda *args: True)
    monkeypatch.setattr(torch.cuda, "current_device", lambda: 0)
    monkeypatch.setattr(
        torch.cuda,
        "get_device_properties",
        lambda index: SimpleNamespace(multi_processor_count=32),
    )

    training = config.training.model_copy(update={"compile": CompileMode.AUTO})
    enabled = resolve_compile_enabled(
        training,
        device=torch.device("cuda"),
        precision="bf16-mixed",
        model_config=config.model,
    )

    assert enabled is False


def test_resolve_compile_enabled_keeps_explicit_compile_on_for_small_cuda_gpu(
    tmp_path,
    monkeypatch,
    load_test_train_config,
    model_workflow_override,
) -> None:
    config = load_test_train_config(tmp_path, override=model_workflow_override())

    monkeypatch.setattr("spice.modeling._runtime.resolve_auto_compile", lambda *args: True)
    monkeypatch.setattr(torch.cuda, "current_device", lambda: 0)
    monkeypatch.setattr(
        torch.cuda,
        "get_device_properties",
        lambda index: SimpleNamespace(multi_processor_count=32),
    )

    training = config.training.model_copy(update={"compile": CompileMode.ON})
    enabled = resolve_compile_enabled(
        training,
        device=torch.device("cuda"),
        precision="bf16-mixed",
        model_config=config.model,
    )

    assert enabled is True
