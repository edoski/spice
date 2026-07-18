"""Internal PyTorch runtime helpers shared by training and inference."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Protocol, TypeVar, cast

import numpy as np
import torch
from numpy.typing import NDArray

from .batch_plan import BatchSource
from .models import ModelOutputs, TemporalModel

if TYPE_CHECKING:
    from .runtime_planning import ModelingRuntimePlan

IntVector = NDArray[np.int64]
ForwardBatchT = TypeVar("ForwardBatchT", bound="ForwardBatch")

class ForwardBatch(Protocol):
    def to_device(self, device: torch.device) -> ForwardBatch: ...

    def model_kwargs(self) -> Mapping[str, torch.Tensor]: ...

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
