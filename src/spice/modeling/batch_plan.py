"""Batch planning for training and inference."""

from __future__ import annotations

import math
import os
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, Literal, Protocol, TypeVar, cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch.utils.data import DataLoader, Sampler

from ..prediction import CompiledPredictionContract
from ..prediction.contracts import ModelInputBatch, PredictionBatch, PreparedPredictionTargets
from ..temporal.execution_policy import (
    PreparedActionSpace,
    PreparedTemporalFacts,
)
from ..temporal.problem_store import CompiledProblemStore
from .representations import PreparedSequenceInputBatches, prepare_sequence_input

if TYPE_CHECKING:
    from .runtime_planning import ModelingRuntimePlan

IntVector = NDArray[np.int64]
BatchT = TypeVar("BatchT", covariant=True)
HostLoaderPolicy = Literal["automatic", "single_process_unpinned"]


class BatchSource(Protocol[BatchT]):
    def __len__(self) -> int: ...

    def __iter__(self) -> Iterator[BatchT]: ...


@dataclass(frozen=True, slots=True)
class BatchPlan(Generic[BatchT]):
    source: BatchSource[BatchT]
    sample_count: int
    batch_count: int


@dataclass(frozen=True, slots=True)
class BatchRuntimeContext:
    batch_size: int
    host_loader_policy: HostLoaderPolicy = "automatic"

    def with_host_loader_policy(
        self,
        host_loader_policy: HostLoaderPolicy,
    ) -> BatchRuntimeContext:
        return BatchRuntimeContext(
            batch_size=self.batch_size,
            host_loader_policy=host_loader_policy,
        )


class PreparedBatchPayload(Protocol[BatchT]):
    @property
    def sample_count(self) -> int: ...

    @property
    def batch_signatures(self) -> IntVector: ...

    def build_batch(self, sample_positions: torch.Tensor) -> BatchT: ...


class _PositionBatchSampler(Sampler[list[int]]):
    def __init__(
        self,
        *,
        batch_signatures: IntVector,
        batch_size: int,
        seed: int,
        shuffle: bool,
    ) -> None:
        self._batch_signatures = batch_signatures.astype(np.int64, copy=False)
        self._batch_size = batch_size
        self._seed = seed
        self._shuffle = shuffle
        self._epoch = 0

    def __len__(self) -> int:
        return math.ceil(int(self._batch_signatures.shape[0]) / self._batch_size)

    def __iter__(self) -> Iterator[list[int]]:
        order = _ordered_sample_positions(
            self._batch_signatures,
            batch_size=self._batch_size,
            epoch=self._epoch if self._shuffle else 0,
            seed=self._seed,
            shuffle=self._shuffle,
        )
        if self._shuffle:
            self._epoch += 1
        for offset in range(0, int(order.shape[0]), self._batch_size):
            yield order[offset : offset + self._batch_size].tolist()


def _ordered_sample_positions(
    batch_signatures: IntVector,
    *,
    batch_size: int,
    epoch: int,
    seed: int,
    shuffle: bool,
) -> IntVector:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    signatures = batch_signatures.astype(np.int64, copy=False)
    order = np.argsort(signatures, kind="stable").astype(np.int64, copy=False)
    if not shuffle or order.size == 0:
        return order

    rng = np.random.default_rng(np.random.SeedSequence([seed, epoch]))
    batches = [
        order[offset : offset + batch_size].copy()
        for offset in range(0, int(order.shape[0]), batch_size)
    ]
    shuffled_batches = [rng.permutation(batches[index]) for index in rng.permutation(len(batches))]
    return np.concatenate(shuffled_batches).astype(np.int64, copy=False)


@dataclass(frozen=True, slots=True)
class _HostBatchCollator(Generic[BatchT]):
    prepared: PreparedBatchPayload[BatchT]

    def __call__(self, sample_positions: Sequence[int]) -> BatchT:
        index = torch.as_tensor(sample_positions, dtype=torch.int64)
        return self.prepared.build_batch(index)


@dataclass(frozen=True, slots=True)
class _HostLoaderWorkerSettings:
    num_workers: int
    persistent_workers: bool
    prefetch_factor: int | None


@dataclass(slots=True)
class _PreparedPredictionBatches:
    prepared: PreparedSequenceInputBatches
    targets: PreparedPredictionTargets

    @property
    def sample_count(self) -> int:
        return self.prepared.sample_count

    @property
    def batch_signatures(self) -> IntVector:
        return self.prepared.batch_signatures

    def build_batch(self, sample_positions: torch.Tensor) -> PredictionBatch:
        input_batch = self.prepared.build_batch(sample_positions)
        return PredictionBatch(
            inputs=input_batch,
            targets=self.targets.build_batch(input_batch.sample_positions),
        )


def _build_plan(
    prepared: PreparedBatchPayload[BatchT],
    *,
    runtime_plan: ModelingRuntimePlan,
    shuffle: bool,
) -> BatchPlan[BatchT]:
    source = _build_batch_source(
        prepared,
        runtime_plan=runtime_plan,
        shuffle=shuffle,
    )
    return BatchPlan(
        source=cast(BatchSource[BatchT], source),
        sample_count=prepared.sample_count,
        batch_count=len(source),
    )


def _prepare_model_inputs(
    store: CompiledProblemStore,
    *,
    action_space: PreparedActionSpace,
    runtime_plan: ModelingRuntimePlan,
) -> PreparedSequenceInputBatches:
    if runtime_plan.batch_runtime_context.batch_size <= 0:
        raise ValueError("batch_size must be positive")
    return prepare_sequence_input(
        store,
        action_space=action_space,
    )


def build_prediction_batch_plan(
    store: CompiledProblemStore,
    *,
    temporal_facts: PreparedTemporalFacts,
    prediction_contract: CompiledPredictionContract,
    runtime_plan: ModelingRuntimePlan,
    shuffle: bool = False,
) -> BatchPlan[PredictionBatch]:
    prepared = _prepare_model_inputs(
        store,
        action_space=temporal_facts.action_space,
        runtime_plan=runtime_plan,
    )
    targets = prediction_contract.prepare_targets(
        temporal_facts=temporal_facts,
    )
    return _build_plan(
        _PreparedPredictionBatches(prepared=prepared, targets=targets),
        runtime_plan=runtime_plan,
        shuffle=shuffle,
    )


def build_model_input_batch_plan(
    store: CompiledProblemStore,
    *,
    action_space: PreparedActionSpace,
    runtime_plan: ModelingRuntimePlan,
) -> BatchPlan[ModelInputBatch]:
    prepared = _prepare_model_inputs(
        store,
        action_space=action_space,
        runtime_plan=runtime_plan,
    )
    return _build_plan(
        prepared,
        runtime_plan=runtime_plan,
        shuffle=False,
    )


def _build_batch_source(
    prepared: PreparedBatchPayload[BatchT],
    *,
    runtime_plan: ModelingRuntimePlan,
    shuffle: bool,
) -> DataLoader[BatchT]:
    batch_sampler = _PositionBatchSampler(
        batch_signatures=prepared.batch_signatures,
        batch_size=runtime_plan.batch_runtime_context.batch_size,
        seed=runtime_plan.seed,
        shuffle=shuffle,
    )
    return _build_host_dataloader_source(
        prepared,
        batch_sampler=batch_sampler,
        runtime_context=runtime_plan.batch_runtime_context,
        resolved_device=runtime_plan.resolved_device,
    )


def _build_host_dataloader_source(
    prepared: PreparedBatchPayload[BatchT],
    *,
    batch_sampler: _PositionBatchSampler,
    runtime_context: BatchRuntimeContext,
    resolved_device: torch.device,
) -> DataLoader[BatchT]:
    worker_settings = _resolve_host_loader_worker_settings(runtime_context)
    loader = DataLoader(
        cast(Any, range(prepared.sample_count)),
        batch_sampler=batch_sampler,
        collate_fn=_HostBatchCollator(prepared),
        num_workers=worker_settings.num_workers,
        persistent_workers=worker_settings.persistent_workers,
        prefetch_factor=worker_settings.prefetch_factor,
        pin_memory=_should_pin_host_memory(runtime_context, resolved_device),
    )
    return cast(DataLoader[BatchT], loader)


def _resolve_host_loader_worker_settings(
    runtime_context: BatchRuntimeContext,
) -> _HostLoaderWorkerSettings:
    if runtime_context.host_loader_policy == "single_process_unpinned":
        return _build_host_loader_worker_settings(num_workers=0)

    requested_workers = os.environ.get("SPICE_DATALOADER_WORKERS")
    if requested_workers is not None:
        return _build_host_loader_worker_settings(
            num_workers=_parse_worker_override(requested_workers)
        )

    cpu_budget = _slurm_cpu_budget()
    if cpu_budget is None or cpu_budget <= 2:
        return _build_host_loader_worker_settings(num_workers=0)
    return _build_host_loader_worker_settings(num_workers=min(8, cpu_budget - 2))


def _parse_worker_override(raw_value: str) -> int:
    try:
        parsed = int(raw_value)
    except ValueError as exc:
        raise ValueError("SPICE_DATALOADER_WORKERS must be an integer") from exc
    if parsed < 0:
        raise ValueError("SPICE_DATALOADER_WORKERS must be non-negative")
    return parsed


def _slurm_cpu_budget() -> int | None:
    raw_value = os.environ.get("SLURM_CPUS_PER_TASK")
    if raw_value is None:
        return None
    try:
        parsed = int(raw_value)
    except ValueError:
        return None
    if parsed <= 0:
        return None
    return parsed


def _build_host_loader_worker_settings(*, num_workers: int) -> _HostLoaderWorkerSettings:
    if num_workers <= 0:
        return _HostLoaderWorkerSettings(
            num_workers=0,
            persistent_workers=False,
            prefetch_factor=None,
        )
    return _HostLoaderWorkerSettings(
        num_workers=num_workers,
        persistent_workers=True,
        prefetch_factor=4 if num_workers >= 4 else 2,
    )


def _should_pin_host_memory(
    runtime_context: BatchRuntimeContext,
    resolved_device: torch.device,
) -> bool:
    if runtime_context.host_loader_policy == "single_process_unpinned":
        return False
    return resolved_device.type == "cuda" and torch.cuda.is_available()
