"""Generic Representation Seam."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol, TypeVar

import numpy as np
import torch
from numpy.typing import NDArray

from ...prediction import ModelInputBatch
from ...semantics import RepresentationSemantics
from ...temporal.execution_policy import (
    CompiledExecutionPolicyContract,
    PreparedActionSpace,
)
from ...temporal.problem_store import CompiledProblemStore

IntVector = NDArray[np.int64]
BatchT = TypeVar("BatchT", bound=ModelInputBatch, covariant=True)
HostStorageMode = Literal["host_streaming", "host_materialized"]


@dataclass(frozen=True, slots=True)
class RepresentationRuntimeContext:
    batch_size: int
    available_host_memory_bytes: int


class PreparedRepresentation(Protocol[BatchT]):
    @property
    def sample_count(self) -> int: ...

    @property
    def batch_signatures(self) -> IntVector: ...

    @property
    def estimated_storage_bytes(self) -> int: ...

    @property
    def host_storage_mode(self) -> HostStorageMode: ...

    def build_batch(self, sample_positions: torch.Tensor) -> BatchT: ...

    def to_device_storage(
        self,
        device: torch.device,
    ) -> PreparedRepresentation[BatchT]: ...


@dataclass(frozen=True, slots=True)
class CompiledRepresentationContract:
    """Compiled model-input representation seam used by training and inference."""

    representation_id: str
    prepare_impl: Callable[..., PreparedRepresentation[ModelInputBatch]]

    @property
    def semantics(self) -> RepresentationSemantics:
        return RepresentationSemantics(representation_id=self.representation_id)

    def prepare(
        self,
        store: CompiledProblemStore,
        *,
        execution_policy: CompiledExecutionPolicyContract,
        action_space: PreparedActionSpace,
        runtime_context: RepresentationRuntimeContext,
    ) -> PreparedRepresentation[ModelInputBatch]:
        return self.prepare_impl(
            store,
            execution_policy=execution_policy,
            action_space=action_space,
            runtime_context=runtime_context,
        )
