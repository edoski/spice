"""Modeling runtime planning."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass

import torch

from ..config.models import TrainingConfig
from ._runtime import build_cuda_modeling_runtime, configure_torch_backends, set_global_seed
from .batch_plan import BatchRuntimeContext
from .models import TemporalModel


@dataclass(frozen=True, slots=True)
class ModelingRuntimePlan:
    resolved_device: torch.device
    precision: str
    batch_runtime_context: BatchRuntimeContext
    deterministic: bool | None
    seed: int


def with_batch_runtime_context(
    plan: ModelingRuntimePlan,
    runtime_context: BatchRuntimeContext,
) -> ModelingRuntimePlan:
    return ModelingRuntimePlan(
        resolved_device=plan.resolved_device,
        precision=plan.precision,
        batch_runtime_context=runtime_context,
        deterministic=plan.deterministic,
        seed=plan.seed,
    )


def build_cuda_modeling_runtime_plan(
    *,
    batch_size: int,
    deterministic: bool | None = None,
    seed: int = 0,
) -> ModelingRuntimePlan:
    runtime = build_cuda_modeling_runtime(batch_size=batch_size)
    return ModelingRuntimePlan(
        resolved_device=runtime.resolved_device,
        precision="32-true",
        batch_runtime_context=runtime.batch_runtime_context,
        deterministic=deterministic,
        seed=seed,
    )


def build_cpu_modeling_runtime_plan(
    *,
    batch_size: int,
    deterministic: bool | None = None,
    seed: int = 0,
) -> ModelingRuntimePlan:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    return ModelingRuntimePlan(
        resolved_device=torch.device("cpu"),
        precision="32-true",
        batch_runtime_context=BatchRuntimeContext(
            batch_size=batch_size,
        ),
        deterministic=deterministic,
        seed=seed,
    )


def build_training_modeling_runtime_plan(
    *,
    training_config: TrainingConfig,
) -> ModelingRuntimePlan:
    set_global_seed(training_config.seed)
    return build_cuda_modeling_runtime_plan(
        batch_size=training_config.batch_size,
        deterministic=training_config.deterministic,
        seed=training_config.seed,
    )


def prepare_model_for_runtime(
    model: TemporalModel,
    plan: ModelingRuntimePlan,
) -> TemporalModel:
    model.to(plan.resolved_device)
    return model


def modeling_backend_scope(plan: ModelingRuntimePlan) -> AbstractContextManager[None]:
    return configure_torch_backends(
        resolved_device=plan.resolved_device,
        deterministic=plan.deterministic,
    )
