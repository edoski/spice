"""Poisson replay evaluator."""

from __future__ import annotations

import numpy as np

from ..core.errors import SpiceOperatorError
from ..prediction.decoded_offsets import DecodedOffsets, require_decoded_offsets
from ..prediction.decoding import DecodedPredictionResult
from ..temporal.execution_policy import CompiledExecutionPolicyContract
from ..temporal.problem_store import CompiledProblemStore
from .config import PoissonReplayEvaluatorConfig
from .contracts import CompiledEvaluatorContract, EvaluationSummary, IntVector, RunEvaluatorFn
from .metrics import REPLAY_METRIC_DESCRIPTORS
from .replay_summary import summarize_runs, summarize_selected_costs
from .sampling import (
    chronological_sample_view,
    sample_poisson_arrivals,
    select_sample_positions_for_arrivals,
)


def run_poisson_replay(
    store: CompiledProblemStore,
    execution_policy: CompiledExecutionPolicyContract,
    decoded_result: DecodedPredictionResult,
    sample_indices: IntVector,
    *,
    config: PoissonReplayEvaluatorConfig,
) -> EvaluationSummary:
    decoded_offsets = require_decoded_offsets(decoded_result)
    if len(decoded_offsets) != int(sample_indices.shape[0]):
        raise ValueError("decoded_offsets must align with sample_indices")
    if sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")

    chronological_samples = chronological_sample_view(store, sample_indices)
    first_timestamp = int(chronological_samples.sample_timestamps[0])
    last_timestamp = int(chronological_samples.sample_timestamps[-1])
    latest_start = last_timestamp - config.window_seconds
    if latest_start < first_timestamp:
        raise ValueError("Evaluation examples do not cover the requested replay window")

    rng = np.random.default_rng(config.seed)
    runs = []
    for _ in range(config.repetitions):
        window_start = float(rng.uniform(first_timestamp, latest_start))
        window_end = window_start + config.window_seconds
        arrivals = sample_poisson_arrivals(
            rng,
            rate_per_second=config.arrival_rate_per_second,
            start_timestamp=window_start,
            end_timestamp=window_end,
        )
        selected_positions = chronological_samples.sample_positions[
            select_sample_positions_for_arrivals(
                chronological_samples.sample_timestamps,
                arrivals,
            )
        ].astype(np.int64, copy=False)
        if selected_positions.size == 0:
            continue
        runs.append(
            summarize_selected_costs(
                store,
                execution_policy,
                decoded_offsets,
                sample_indices,
                selected_positions,
                metadata={
                    "window_start_timestamp": window_start,
                    "window_end_timestamp": window_end,
                    "n_arrivals": int(arrivals.shape[0]),
                },
            )
        )

    if not runs:
        raise SpiceOperatorError(
            "poisson_arrivals evaluation produced no valid arrivals; "
            "adjust the benchmark rate or window"
        )
    return summarize_runs(runs)


def compile_poisson_replay_evaluator_contract(
    config: PoissonReplayEvaluatorConfig,
) -> CompiledEvaluatorContract:
    def run_fn(
        store,
        execution_policy,
        decoded_result,
        sample_indices,
    ):
        return run_poisson_replay(
            store,
            execution_policy,
            decoded_result,
            sample_indices,
            config=config,
        )

    resolved_run_fn: RunEvaluatorFn = run_fn
    return CompiledEvaluatorContract(
        evaluation_id=config.id,
        metric_descriptors=REPLAY_METRIC_DESCRIPTORS,
        primary_metric_id="profit_over_baseline",
        direction="maximize",
        config_payload=config.model_dump(mode="json", exclude_none=True),
        accepted_decoded_result_id=DecodedOffsets.decoded_result_id,
        run_fn=resolved_run_fn,
    )
