"""Evaluator sample-selection helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ..temporal.problem_store import CompiledProblemStore
from .contracts import IntVector


@dataclass(frozen=True, slots=True)
class ChronologicalSampleView:
    sample_positions: IntVector
    sample_timestamps: IntVector


def sample_poisson_arrivals(
    rng: np.random.Generator,
    *,
    rate_per_second: float,
    start_timestamp: float,
    end_timestamp: float,
) -> NDArray[np.float64]:
    if rate_per_second <= 0:
        raise ValueError("rate_per_second must be positive")
    arrivals: list[float] = []
    cursor = start_timestamp
    while cursor < end_timestamp:
        cursor += rng.exponential(1.0 / rate_per_second)
        if cursor < end_timestamp:
            arrivals.append(cursor)
    return np.asarray(arrivals, dtype=np.float64)


def chronological_sample_view(
    store: CompiledProblemStore,
    sample_indices: IntVector,
) -> ChronologicalSampleView:
    resolved_sample_indices = sample_indices.astype(np.int64, copy=False)
    sample_timestamps = store.sample_timestamps(resolved_sample_indices)
    order = np.argsort(sample_timestamps, kind="stable").astype(np.int64, copy=False)
    return ChronologicalSampleView(
        sample_positions=order,
        sample_timestamps=sample_timestamps[order],
    )


def select_sample_positions_for_arrivals(
    sample_timestamps: NDArray[np.int64],
    arrivals: NDArray[np.float64],
) -> NDArray[np.int64]:
    if arrivals.size == 0:
        return np.empty(0, dtype=np.int64)
    selected_positions = np.searchsorted(sample_timestamps, arrivals, side="right") - 1
    return selected_positions[selected_positions >= 0].astype(np.int64, copy=False)
