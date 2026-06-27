from __future__ import annotations

import pytest
import torch

from spice.core.errors import SpiceOperatorError
from spice.modeling._runtime import (
    CudaModelingRuntime,
    build_batch_runtime_context,
    ensure_cuda_runtime_ready,
)
from spice.modeling.runtime_planning import (
    build_cpu_modeling_runtime_plan,
    build_cuda_modeling_runtime_plan,
)


def test_ensure_cuda_runtime_ready_raises_clear_error_for_broken_cuda_runtime(
    monkeypatch,
) -> None:
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(
        torch.cuda,
        "current_device",
        lambda: (_ for _ in ()).throw(RuntimeError("driver mismatch")),
    )

    with pytest.raises(SpiceOperatorError, match="CUDA runtime initialization failed"):
        ensure_cuda_runtime_ready(torch.device("cuda"))


def test_ensure_cuda_runtime_ready_rejects_non_cuda_resolutions() -> None:
    with pytest.raises(SpiceOperatorError, match="Modeling runtime requires CUDA devices"):
        ensure_cuda_runtime_ready(torch.device("cpu"))


def test_ensure_cuda_runtime_ready_rejects_rocm(monkeypatch) -> None:
    monkeypatch.setattr(torch.version, "hip", "6.0", raising=False)

    with pytest.raises(SpiceOperatorError, match="ROCm/HIP is unsupported"):
        ensure_cuda_runtime_ready(torch.device("cuda"))


def test_batch_runtime_context_only_owns_batch_size_and_loader_policy() -> None:
    context = build_batch_runtime_context(
        device=torch.device("cuda"),
        batch_size=8,
    )

    assert context.batch_size == 8
    assert context.host_loader_policy == "automatic"
    assert context.with_host_loader_policy("single_process_unpinned").host_loader_policy == (
        "single_process_unpinned"
    )


def test_cuda_modeling_runtime_plan_owns_precision_and_backend_facts(monkeypatch) -> None:
    runtime_context = build_batch_runtime_context(
        device=torch.device("cuda"),
        batch_size=8,
    )
    monkeypatch.setattr(
        "spice.modeling.runtime_planning.build_cuda_modeling_runtime",
        lambda **_: CudaModelingRuntime(
            resolved_device=torch.device("cuda"),
            batch_runtime_context=runtime_context,
        ),
    )

    plan = build_cuda_modeling_runtime_plan(
        batch_size=8,
        deterministic=True,
        seed=17,
    )

    assert plan.resolved_device == torch.device("cuda")
    assert plan.precision == "32-true"
    assert plan.batch_runtime_context is runtime_context
    assert plan.deterministic is True
    assert plan.seed == 17


def test_cpu_modeling_runtime_plan_is_available_for_serving_forward_paths() -> None:
    plan = build_cpu_modeling_runtime_plan(
        batch_size=4,
        deterministic=False,
        seed=9,
    )

    assert plan.resolved_device == torch.device("cpu")
    assert plan.precision == "32-true"
    assert plan.batch_runtime_context.batch_size == 4
    assert plan.batch_runtime_context.host_loader_policy == "automatic"
    assert plan.deterministic is False
    assert plan.seed == 9


def test_batch_runtime_context_rejects_invalid_batch_size() -> None:
    with pytest.raises(ValueError, match="batch_size must be positive"):
        build_batch_runtime_context(device=torch.device("cuda"), batch_size=0)
