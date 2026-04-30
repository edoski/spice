"""Full temporal replay evaluator."""

from __future__ import annotations

import numpy as np

from ..prediction.decoded_offsets import DecodedOffsets, require_decoded_offsets
from ..prediction.decoding import DecodedPredictionResult
from ..temporal.execution_policy import CompiledExecutionPolicyContract
from ..temporal.problem_store import CompiledProblemStore
from .config import FullTemporalReplayEvaluatorConfig
from .contracts import CompiledEvaluatorContract, EvaluationSummary, IntVector, RunEvaluatorFn
from .metrics import TEMPORAL_REPLAY_METRIC_DESCRIPTORS
from .temporal_accounting import (
    summarize_selected_temporal_decisions,
    summarize_temporal_accounting_runs,
)


def run_full_temporal_replay(
    store: CompiledProblemStore,
    execution_policy: CompiledExecutionPolicyContract,
    decoded_result: DecodedPredictionResult,
    sample_indices: IntVector,
    *,
    config: FullTemporalReplayEvaluatorConfig,
) -> EvaluationSummary:
    decoded_offsets = require_decoded_offsets(decoded_result)
    if len(decoded_offsets) != int(sample_indices.shape[0]):
        raise ValueError("decoded_offsets must align with sample_indices")
    if sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")

    selected_positions = np.arange(sample_indices.shape[0], dtype=np.int64)
    run = summarize_selected_temporal_decisions(
        store,
        execution_policy,
        decoded_offsets,
        sample_indices,
        selected_positions,
        metadata={
            "mode": config.id,
            "sample_count": int(sample_indices.shape[0]),
        },
    )
    return summarize_temporal_accounting_runs([run])


def compile_full_temporal_replay_evaluator_contract(
    config: FullTemporalReplayEvaluatorConfig,
) -> CompiledEvaluatorContract:
    def run_fn(
        store,
        execution_policy,
        decoded_result,
        sample_indices,
    ):
        return run_full_temporal_replay(
            store,
            execution_policy,
            decoded_result,
            sample_indices,
            config=config,
        )

    resolved_run_fn: RunEvaluatorFn = run_fn
    return CompiledEvaluatorContract(
        evaluation_id=config.id,
        metric_descriptors=TEMPORAL_REPLAY_METRIC_DESCRIPTORS,
        primary_metric_id="profit_over_baseline",
        direction="maximize",
        config_payload=config.model_dump(mode="json", exclude_none=True),
        accepted_decoded_result_id=DecodedOffsets.decoded_result_id,
        run_fn=resolved_run_fn,
    )
