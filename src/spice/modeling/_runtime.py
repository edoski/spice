"""Internal PyTorch runtime helpers shared by training and inference."""

from __future__ import annotations

import random
from collections.abc import Callable, Mapping
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, TypeVar, cast

import numpy as np
import torch
from numpy.typing import NDArray

from ..core.errors import SpiceOperatorError
from .batch_plan import BatchRuntimeContext, BatchSource
from .models import ModelOutputs, TemporalModel

if TYPE_CHECKING:
    from .runtime_planning import ModelingRuntimePlan

IntVector = NDArray[np.int64]
ForwardBatchT = TypeVar("ForwardBatchT", bound="ForwardBatch")


@dataclass(frozen=True, slots=True)
class CudaModelingRuntime:
    resolved_device: torch.device
    batch_runtime_context: BatchRuntimeContext

class ForwardBatch(Protocol):
    def to_device(self, device: torch.device) -> ForwardBatch: ...

    def model_kwargs(self) -> Mapping[str, torch.Tensor]: ...


def resolve_cuda_device() -> torch.device:
    resolved_device = torch.device("cuda")
    require_cuda_device(resolved_device, requested_device="cuda")
    return resolved_device


def ensure_cuda_runtime_ready(device: torch.device) -> None:
    require_cuda_device(device, requested_device="cuda")
    _ensure_cuda_runtime_ready(device)


def build_cuda_modeling_runtime(*, batch_size: int) -> CudaModelingRuntime:
    resolved_device = resolve_cuda_device()
    ensure_cuda_runtime_ready(resolved_device)
    return CudaModelingRuntime(
        resolved_device=resolved_device,
        batch_runtime_context=build_batch_runtime_context(
            device=resolved_device,
            batch_size=batch_size,
        ),
    )


def set_global_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


@contextmanager
def configure_torch_backends(
    *,
    resolved_device: torch.device,
    deterministic: bool | None,
):
    previous_matmul_precision = torch.get_float32_matmul_precision()
    previous_cudnn_deterministic = torch.backends.cudnn.deterministic
    previous_cudnn_benchmark = torch.backends.cudnn.benchmark
    previous_cuda_matmul_allow_tf32 = (
        torch.backends.cuda.matmul.allow_tf32 if hasattr(torch.backends, "cuda") else None
    )
    previous_cudnn_allow_tf32 = torch.backends.cudnn.allow_tf32
    try:
        if resolved_device.type == "cuda":
            torch.set_float32_matmul_precision("high")
            if previous_cuda_matmul_allow_tf32 is not None:
                torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
        if deterministic is not None:
            torch.backends.cudnn.deterministic = deterministic
            torch.backends.cudnn.benchmark = not deterministic
        yield
    finally:
        torch.set_float32_matmul_precision(previous_matmul_precision)
        torch.backends.cudnn.deterministic = previous_cudnn_deterministic
        torch.backends.cudnn.benchmark = previous_cudnn_benchmark
        torch.backends.cudnn.allow_tf32 = previous_cudnn_allow_tf32
        if previous_cuda_matmul_allow_tf32 is not None:
            torch.backends.cuda.matmul.allow_tf32 = previous_cuda_matmul_allow_tf32


def precision_context(
    *,
    precision: str,
):
    if precision == "32-true":
        return nullcontext()
    raise ValueError(f"Unsupported modeling precision: {precision}. Only 32-true is supported.")


def require_cuda_device(
    device: torch.device,
    *,
    requested_device: str | None = None,
) -> None:
    if device.type != "cuda":
        resolved_label = requested_device if requested_device is not None else str(device)
        raise SpiceOperatorError(
            f"Modeling runtime requires CUDA devices. Received {resolved_label!r}."
        )
    if torch.version.hip is not None:
        raise SpiceOperatorError("Modeling runtime requires NVIDIA CUDA. ROCm/HIP is unsupported.")


def build_batch_runtime_context(
    *,
    device: torch.device,
    batch_size: int,
) -> BatchRuntimeContext:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    return BatchRuntimeContext(
        batch_size=batch_size,
    )


def run_model_forward_pass(
    model: TemporalModel,
    *,
    loader: BatchSource[ForwardBatchT],
    runtime_plan: ModelingRuntimePlan,
    on_outputs: Callable[[ForwardBatchT, ModelOutputs], None],
) -> None:
    model.eval()
    with torch.no_grad():
        for batch in loader:
            device_batch = cast(ForwardBatchT, batch.to_device(runtime_plan.resolved_device))
            with precision_context(precision=runtime_plan.precision):
                outputs = model(**device_batch.model_kwargs())
            on_outputs(device_batch, outputs)


def _cuda_device_index(device: torch.device) -> int:
    require_cuda_device(device)
    return torch.cuda.current_device() if device.index is None else device.index


def _ensure_cuda_runtime_ready(device: torch.device) -> None:
    try:
        if not torch.cuda.is_available():
            raise SpiceOperatorError(
                "Resolved CUDA device, but torch.cuda.is_available() is False. "
                + _cuda_runtime_details()
            )
        device_index = torch.cuda.current_device() if device.index is None else device.index
        torch.cuda.get_device_properties(device_index)
    except SpiceOperatorError:
        raise
    except Exception as exc:
        raise _cuda_runtime_error(exc) from exc


def _cuda_runtime_error(exc: Exception) -> SpiceOperatorError:
    return SpiceOperatorError(
        "CUDA runtime initialization failed. " + _cuda_runtime_details() + f" Root cause: {exc}"
    )


def _cuda_runtime_details() -> str:
    try:
        cuda_device_count = str(torch.cuda.device_count())
    except Exception as exc:  # pragma: no cover - defensive fallback
        cuda_device_count = f"error:{exc}"
    return (
        f"torch={torch.__version__}; "
        f"torch.version.cuda={torch.version.cuda}; "
        f"cuda_device_count={cuda_device_count}"
    )
