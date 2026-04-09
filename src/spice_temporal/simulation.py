"""Economic simulation helpers for temporal evaluation."""

from __future__ import annotations

import bisect
import random
import statistics
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from spice_temporal.datasets import TemporalDatasetStore

IntVector = NDArray[np.int64]


@dataclass(slots=True)
class SimulationRunSummary:
    window_start_timestamp: float
    window_end_timestamp: float
    n_arrivals: int
    n_events: int
    profit_over_baseline: float
    cost_over_optimum: float
    baseline_cost_over_optimum: float


@dataclass(slots=True)
class SimulationSummary:
    mean_profit_over_baseline: float
    std_profit_over_baseline: float
    mean_cost_over_optimum: float
    std_cost_over_optimum: float
    mean_baseline_cost_over_optimum: float
    std_baseline_cost_over_optimum: float
    total_events: int
    runs: list[SimulationRunSummary]


def sample_poisson_arrivals(
    rng: random.Random,
    *,
    rate_per_second: float,
    start_timestamp: float,
    end_timestamp: float,
) -> list[float]:
    if rate_per_second <= 0:
        raise ValueError("rate_per_second must be positive")
    arrivals: list[float] = []
    cursor = start_timestamp
    while cursor < end_timestamp:
        cursor += rng.expovariate(rate_per_second)
        if cursor < end_timestamp:
            arrivals.append(cursor)
    return arrivals


def select_sample_positions_for_arrivals(
    anchor_timestamps: list[int],
    arrivals: list[float],
) -> list[int]:
    selected_positions: list[int] = []
    for arrival in arrivals:
        position = bisect.bisect_right(anchor_timestamps, arrival) - 1
        if position >= 0:
            selected_positions.append(position)
    return selected_positions


def summarize_realized_costs(
    store: TemporalDatasetStore,
    predicted_offsets: list[int],
    sample_indices: IntVector,
    selected_positions: list[int],
    *,
    window_start_timestamp: float,
    window_end_timestamp: float,
    n_arrivals: int,
) -> SimulationRunSummary:
    if len(predicted_offsets) != int(sample_indices.shape[0]):
        raise ValueError("predicted_offsets must align with sample_indices")
    if not selected_positions:
        raise ValueError("selected_positions must be non-empty")

    selected_sample_indices = sample_indices[np.asarray(selected_positions, dtype=np.int64)]
    selected_offsets = np.asarray(
        [predicted_offsets[position] for position in selected_positions],
        dtype=np.int64,
    )
    selected_action_log_fees = store.action_log_fees[selected_sample_indices]
    realized_logs = selected_action_log_fees[np.arange(selected_offsets.shape[0]), selected_offsets]
    realized_total = float(np.exp(realized_logs.astype(np.float64, copy=False)).sum())
    baseline_total = float(
        np.exp(
            store.next_block_log_fee[selected_sample_indices].astype(np.float64, copy=False)
        ).sum()
    )
    optimum_total = float(
        np.exp(
            store.optimal_log_fee[selected_sample_indices].astype(np.float64, copy=False)
        ).sum()
    )

    return SimulationRunSummary(
        window_start_timestamp=window_start_timestamp,
        window_end_timestamp=window_end_timestamp,
        n_arrivals=n_arrivals,
        n_events=len(selected_positions),
        profit_over_baseline=(baseline_total - realized_total) / baseline_total,
        cost_over_optimum=(realized_total - optimum_total) / optimum_total,
        baseline_cost_over_optimum=(baseline_total - optimum_total) / optimum_total,
    )


def run_temporal_simulation(
    store: TemporalDatasetStore,
    predicted_offsets: list[int],
    *,
    sample_indices: IntVector,
    window_seconds: int,
    arrival_rate_per_second: float,
    repetitions: int,
    seed: int,
) -> SimulationSummary:
    if len(predicted_offsets) != int(sample_indices.shape[0]):
        raise ValueError("predicted_offsets must align with sample_indices")
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")
    if sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")

    anchor_timestamps_array = store.timestamps[store.anchor_row_indices[sample_indices]]
    anchor_timestamps = anchor_timestamps_array.tolist()
    first_timestamp = anchor_timestamps[0]
    last_timestamp = anchor_timestamps[-1]
    latest_start = last_timestamp - window_seconds
    if latest_start < first_timestamp:
        raise ValueError("Evaluation examples do not cover the requested simulation window")

    rng = random.Random(seed)
    runs: list[SimulationRunSummary] = []
    for _ in range(repetitions):
        window_start = rng.uniform(first_timestamp, latest_start)
        window_end = window_start + window_seconds
        arrivals = sample_poisson_arrivals(
            rng,
            rate_per_second=arrival_rate_per_second,
            start_timestamp=window_start,
            end_timestamp=window_end,
        )
        selected_positions = select_sample_positions_for_arrivals(anchor_timestamps, arrivals)
        if not selected_positions:
            continue
        runs.append(
            summarize_realized_costs(
                store,
                predicted_offsets,
                sample_indices,
                selected_positions,
                window_start_timestamp=window_start,
                window_end_timestamp=window_end,
                n_arrivals=len(arrivals),
            )
        )

    if not runs:
        raise ValueError("Simulation produced no valid runs")

    profits = [run.profit_over_baseline for run in runs]
    model_costs = [run.cost_over_optimum for run in runs]
    baseline_costs = [run.baseline_cost_over_optimum for run in runs]
    return SimulationSummary(
        mean_profit_over_baseline=statistics.fmean(profits),
        std_profit_over_baseline=statistics.pstdev(profits),
        mean_cost_over_optimum=statistics.fmean(model_costs),
        std_cost_over_optimum=statistics.pstdev(model_costs),
        mean_baseline_cost_over_optimum=statistics.fmean(baseline_costs),
        std_baseline_cost_over_optimum=statistics.pstdev(baseline_costs),
        total_events=sum(run.n_events for run in runs),
        runs=runs,
    )
