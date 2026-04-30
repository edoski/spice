"""Planned forward-only runtime execution."""

from __future__ import annotations

from collections.abc import Callable

import torch

from ..prediction import CompiledPredictionContract
from ..prediction.contracts import ModelInputBatch, PredictionBatch
from ..temporal.execution_policy import CompiledExecutionPolicyContract
from ..temporal.problem_store import CompiledProblemStore, IntVector
from ._runtime import measure_forward_device_resident_budget, run_model_forward_pass
from .batch_plan import build_model_input_batch_plan, build_prediction_batch_plan
from .models import ModelOutputs, TemporalModel
from .representations import CompiledRepresentationContract, RepresentationRuntimeContext


def _host_warmup_context(
    runtime_context: RepresentationRuntimeContext,
) -> RepresentationRuntimeContext:
    return runtime_context.with_device_memory_budget(0)


def run_planned_model_input_forward(
    model: TemporalModel,
    *,
    store: CompiledProblemStore,
    sample_indices: IntVector,
    representation_contract: CompiledRepresentationContract,
    base_runtime_context: RepresentationRuntimeContext,
    resolved_device: torch.device,
    precision: str,
    seed: int,
    on_outputs: Callable[[ModelInputBatch, ModelOutputs], None],
) -> None:
    warmup_plan = build_model_input_batch_plan(
        store,
        sample_indices,
        representation_contract=representation_contract,
        runtime_context=_host_warmup_context(base_runtime_context),
        resolved_device=resolved_device,
        seed=seed,
    )
    budget = measure_forward_device_resident_budget(
        model,
        loader=warmup_plan.source,
        resolved_device=resolved_device,
        precision=precision,
    )
    planned_runtime_context = base_runtime_context.with_device_memory_budget(budget)
    del warmup_plan
    batch_plan = build_model_input_batch_plan(
        store,
        sample_indices,
        representation_contract=representation_contract,
        runtime_context=planned_runtime_context,
        resolved_device=resolved_device,
        seed=seed,
    )
    run_model_forward_pass(
        model,
        loader=batch_plan.source,
        resolved_device=resolved_device,
        precision=precision,
        on_outputs=on_outputs,
    )


def run_planned_prediction_forward(
    model: TemporalModel,
    *,
    store: CompiledProblemStore,
    sample_indices: IntVector,
    representation_contract: CompiledRepresentationContract,
    prediction_contract: CompiledPredictionContract,
    execution_policy: CompiledExecutionPolicyContract,
    base_runtime_context: RepresentationRuntimeContext,
    resolved_device: torch.device,
    precision: str,
    seed: int,
    on_outputs: Callable[[PredictionBatch, ModelOutputs], None],
) -> None:
    warmup_plan = build_prediction_batch_plan(
        store,
        sample_indices,
        representation_contract=representation_contract,
        prediction_contract=prediction_contract,
        execution_policy=execution_policy,
        runtime_context=_host_warmup_context(base_runtime_context),
        resolved_device=resolved_device,
        seed=seed,
    )
    budget = measure_forward_device_resident_budget(
        model,
        loader=warmup_plan.source,
        resolved_device=resolved_device,
        precision=precision,
    )
    planned_runtime_context = base_runtime_context.with_device_memory_budget(budget)
    del warmup_plan
    batch_plan = build_prediction_batch_plan(
        store,
        sample_indices,
        representation_contract=representation_contract,
        prediction_contract=prediction_contract,
        execution_policy=execution_policy,
        runtime_context=planned_runtime_context,
        resolved_device=resolved_device,
        seed=seed,
    )
    run_model_forward_pass(
        model,
        loader=batch_plan.source,
        resolved_device=resolved_device,
        precision=precision,
        on_outputs=on_outputs,
    )
