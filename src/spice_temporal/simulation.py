"""Economic simulation helpers for temporal evaluation."""

from __future__ import annotations

import bisect
import math
import random
import statistics
from dataclasses import dataclass

from spice_temporal.records import SupervisedExample


@dataclass(slots=True)
class SimulationRunSummary:
    window_start_timestamp: float
    window_end_timestamp: float
    n_arrivals: int
    n_events: int
    mean_profit_over_baseline: float
    mean_cost_over_optimum: float
    baseline_mean_cost_over_optimum: float


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


def select_example_indices_for_arrivals(
    examples: list[SupervisedExample],
    arrivals: list[float],
) -> list[int]:
    timestamps = [example.anchor_timestamp for example in examples]
    selected_indices: list[int] = []
    for arrival in arrivals:
        index = bisect.bisect_right(timestamps, arrival) - 1
        if index >= 0:
            selected_indices.append(index)
    return selected_indices


def summarize_realized_costs(
    examples: list[SupervisedExample],
    predicted_offsets: list[int],
    selected_indices: list[int],
    *,
    window_start_timestamp: float,
    window_end_timestamp: float,
    n_arrivals: int,
) -> SimulationRunSummary:
    if len(examples) != len(predicted_offsets):
        raise ValueError("examples and predicted_offsets must have the same length")
    if not selected_indices:
        raise ValueError("selected_indices must be non-empty")

    profits: list[float] = []
    model_costs: list[float] = []
    baseline_costs: list[float] = []
    for index in selected_indices:
        example = examples[index]
        predicted_offset = predicted_offsets[index]
        realized = math.exp(example.candidate_log_fees[predicted_offset])
        baseline = math.exp(example.next_block_log_fee)
        optimum = math.exp(example.optimal_log_fee)
        profits.append((baseline - realized) / baseline)
        model_costs.append((realized - optimum) / optimum)
        baseline_costs.append((baseline - optimum) / optimum)

    return SimulationRunSummary(
        window_start_timestamp=window_start_timestamp,
        window_end_timestamp=window_end_timestamp,
        n_arrivals=n_arrivals,
        n_events=len(selected_indices),
        mean_profit_over_baseline=statistics.fmean(profits),
        mean_cost_over_optimum=statistics.fmean(model_costs),
        baseline_mean_cost_over_optimum=statistics.fmean(baseline_costs),
    )


def run_temporal_simulation(
    examples: list[SupervisedExample],
    predicted_offsets: list[int],
    *,
    window_seconds: int,
    arrival_rate_per_second: float,
    repetitions: int,
    seed: int,
) -> SimulationSummary:
    if len(examples) != len(predicted_offsets):
        raise ValueError("examples and predicted_offsets must have the same length")
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")
    if not examples:
        raise ValueError("examples must be non-empty")

    first_timestamp = examples[0].anchor_timestamp
    last_timestamp = examples[-1].anchor_timestamp
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
        selected_indices = select_example_indices_for_arrivals(examples, arrivals)
        if not selected_indices:
            continue
        runs.append(
            summarize_realized_costs(
                examples,
                predicted_offsets,
                selected_indices,
                window_start_timestamp=window_start,
                window_end_timestamp=window_end,
                n_arrivals=len(arrivals),
            )
        )

    if not runs:
        raise ValueError("Simulation produced no valid runs")

    profits = [run.mean_profit_over_baseline for run in runs]
    model_costs = [run.mean_cost_over_optimum for run in runs]
    baseline_costs = [run.baseline_mean_cost_over_optimum for run in runs]
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
