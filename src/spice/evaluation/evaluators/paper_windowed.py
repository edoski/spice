"""Random-window paper evaluator."""

from __future__ import annotations

import numpy as np
from pydantic import Field

from ...core.reporting import NullReporter, Reporter
from ...prediction.contracts import DecodedOffsets
from ...temporal.problem_store import CompiledProblemStore
from ..base import CompiledEvaluatorContract, EvaluationSummary, EvaluatorConfig
from .shared import (
    EVALUATION_METRIC_DESCRIPTORS,
    chronological_sample_view,
    summarize_runs,
    summarize_selected_costs,
)


class PaperWindowedEvaluatorConfig(EvaluatorConfig):
    id: str = "paper_windowed"
    window_seconds: int = Field(default=7200, gt=0)
    repetitions: int = Field(default=50, gt=0)
    seed: int = Field(default=2026, ge=0)


def _run(
    store: CompiledProblemStore,
    realization_policy,
    decoded_offsets: DecodedOffsets,
    sample_indices: np.ndarray,
    reporter: Reporter | None,
    *,
    config: PaperWindowedEvaluatorConfig,
) -> EvaluationSummary:
    reporter = reporter or NullReporter()
    if sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")
    chronological_samples = chronological_sample_view(store, sample_indices)
    first_timestamp = int(chronological_samples.sample_timestamps[0])
    last_timestamp = int(chronological_samples.sample_timestamps[-1])
    rng = np.random.default_rng(config.seed)
    task_id = reporter.start_task("evaluate random paper windows", total=config.repetitions)
    runs = []
    if last_timestamp - first_timestamp <= config.window_seconds:
        runs.append(
            summarize_selected_costs(
                store,
                realization_policy,
                decoded_offsets,
                sample_indices,
                np.arange(sample_indices.shape[0], dtype=np.int64),
                metadata={"mode": "fullset_fallback"},
            )
        )
        reporter.finish_task(task_id, message="fallback=fullset")
        return summarize_runs(runs)
    max_start = last_timestamp - config.window_seconds
    start_intervals = _non_empty_start_intervals(
        chronological_samples.sample_timestamps,
        first_timestamp=first_timestamp,
        max_start=max_start,
        window_seconds=config.window_seconds,
    )
    if not start_intervals:
        raise ValueError("paper_windowed evaluator produced no non-empty windows")
    interval_sizes = np.array(
        [end - start + 1 for start, end in start_intervals],
        dtype=np.int64,
    )
    cumulative_sizes = np.cumsum(interval_sizes, dtype=np.int64)
    total_starts = int(cumulative_sizes[-1])
    for repetition in range(1, config.repetitions + 1):
        start_timestamp = _sample_start_timestamp(
            rng,
            start_intervals=start_intervals,
            cumulative_sizes=cumulative_sizes,
            total_starts=total_starts,
        )
        end_timestamp = start_timestamp + config.window_seconds
        selected_positions = chronological_samples.sample_positions[
            np.flatnonzero(
                (chronological_samples.sample_timestamps >= start_timestamp)
                & (chronological_samples.sample_timestamps < end_timestamp)
            )
        ].astype(np.int64, copy=False)
        runs.append(
            summarize_selected_costs(
                store,
                realization_policy,
                decoded_offsets,
                sample_indices,
                selected_positions,
                metadata={
                    "mode": "windowed",
                    "window_start_timestamp": start_timestamp,
                    "window_end_timestamp": end_timestamp,
                    "repetition": repetition,
                },
            )
        )
        reporter.update_task(
            task_id,
            completed=repetition,
            message=f"runs={repetition}",
        )
    reporter.finish_task(task_id, message=f"runs={len(runs)}")
    return summarize_runs(runs)


def _non_empty_start_intervals(
    sample_timestamps: np.ndarray,
    *,
    first_timestamp: int,
    max_start: int,
    window_seconds: int,
) -> list[tuple[int, int]]:
    intervals: list[tuple[int, int]] = []
    for timestamp in sample_timestamps:
        start = max(first_timestamp, int(timestamp) - window_seconds + 1)
        end = min(max_start, int(timestamp))
        if start > end:
            continue
        if intervals and start <= intervals[-1][1] + 1:
            intervals[-1] = (intervals[-1][0], max(intervals[-1][1], end))
        else:
            intervals.append((start, end))
    return intervals


def _sample_start_timestamp(
    rng: np.random.Generator,
    *,
    start_intervals: list[tuple[int, int]],
    cumulative_sizes: np.ndarray,
    total_starts: int,
) -> int:
    draw = int(rng.integers(total_starts))
    interval_index = int(np.searchsorted(cumulative_sizes, draw, side="right"))
    interval_start, _ = start_intervals[interval_index]
    interval_offset = draw - int(cumulative_sizes[interval_index - 1]) if interval_index else draw
    return interval_start + interval_offset


def compile_evaluator(config: PaperWindowedEvaluatorConfig) -> CompiledEvaluatorContract:
    return CompiledEvaluatorContract(
        evaluator_id="paper_windowed",
        metric_descriptors=EVALUATION_METRIC_DESCRIPTORS,
        primary_metric_id="profit_over_baseline",
        direction="maximize",
        config_payload=config.model_dump(mode="json", exclude_none=True),
        run_fn=lambda store, realization_policy, decoded_offsets, sample_indices, reporter: _run(
            store,
            realization_policy,
            decoded_offsets,
            sample_indices,
            reporter,
            config=config,
        ),
    )
