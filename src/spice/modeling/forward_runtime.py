"""Planned forward-only runtime execution."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from ..prediction import CompiledPredictionContract
from ..prediction.contracts import ModelInputBatch, PredictionBatch
from ..temporal.execution_policy import (
    PreparedActionSpace,
    PreparedTemporalFacts,
)
from ..temporal.problem_store import CompiledProblemStore, IntVector
from ._runtime import run_model_forward_pass
from .batch_plan import (
    BatchPlan,
    build_model_input_batch_plan,
    build_prediction_batch_plan,
)
from .models import ModelOutputs, TemporalModel
from .runtime_planning import ModelingRuntimePlan

ForwardBatchT = TypeVar("ForwardBatchT", ModelInputBatch, PredictionBatch)


def _require_non_empty_samples(sample_indices: IntVector) -> None:
    if sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")


def _run_planned_forward(
    model: TemporalModel,
    *,
    build_plan: Callable[[ModelingRuntimePlan], BatchPlan[ForwardBatchT]],
    runtime_plan: ModelingRuntimePlan,
    on_outputs: Callable[[ForwardBatchT, ModelOutputs], None],
) -> None:
    batch_plan = build_plan(runtime_plan)
    run_model_forward_pass(
        model,
        loader=batch_plan.source,
        runtime_plan=runtime_plan,
        on_outputs=on_outputs,
    )


def run_planned_model_input_forward(
    model: TemporalModel,
    *,
    store: CompiledProblemStore,
    action_space: PreparedActionSpace,
    runtime_plan: ModelingRuntimePlan,
    on_outputs: Callable[[ModelInputBatch, ModelOutputs], None],
) -> None:
    _require_non_empty_samples(action_space.sample_indices)

    def _build_plan(plan: ModelingRuntimePlan) -> BatchPlan[ModelInputBatch]:
        return build_model_input_batch_plan(
            store,
            action_space=action_space,
            runtime_plan=plan,
        )

    _run_planned_forward(
        model,
        build_plan=_build_plan,
        runtime_plan=runtime_plan,
        on_outputs=on_outputs,
    )


def run_planned_prediction_forward(
    model: TemporalModel,
    *,
    store: CompiledProblemStore,
    temporal_facts: PreparedTemporalFacts,
    prediction_contract: CompiledPredictionContract,
    runtime_plan: ModelingRuntimePlan,
    on_outputs: Callable[[PredictionBatch, ModelOutputs], None],
) -> None:
    _require_non_empty_samples(temporal_facts.action_space.sample_indices)

    def _build_plan(plan: ModelingRuntimePlan) -> BatchPlan[PredictionBatch]:
        return build_prediction_batch_plan(
            store,
            temporal_facts=temporal_facts,
            prediction_contract=prediction_contract,
            runtime_plan=plan,
            shuffle=False,
        )

    _run_planned_forward(
        model,
        build_plan=_build_plan,
        runtime_plan=runtime_plan,
        on_outputs=on_outputs,
    )
