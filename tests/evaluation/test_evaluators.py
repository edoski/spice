from __future__ import annotations

import numpy as np
import pytest
import torch

from spice.core.errors import ConfigResolutionError
from spice.evaluation import (
    CompiledEvaluatorContract,
    EvaluationRun,
    EvaluationSummary,
    EvaluatorConfig,
    coerce_evaluator_config,
    compile_evaluator_contract,
)
from spice.evaluation.sampling import (
    chronological_sample_view,
    sample_poisson_arrivals,
    select_sample_positions_for_arrivals,
)
from spice.prediction import MetricDescriptor, MetricSet
from spice.prediction.decoded_offsets import DecodedOffsets
from spice.temporal import (
    coerce_execution_policy_config,
    compile_execution_policy_contract,
)
from spice.temporal.problem_store import CompiledProblemStore


class _OtherDecodedResult:
    decoded_result_id = "other"

    def __len__(self) -> int:
        return 4


def _store() -> CompiledProblemStore:
    return CompiledProblemStore(
        feature_matrix=np.zeros((16, 1), dtype=np.float32),
        log_base_fees=np.log(
            np.array(
                [100, 95, 90, 80, 75, 70, 60, 55, 50, 40, 35, 30, 25, 20, 18, 16],
                dtype=np.float32,
            )
        ).astype(np.float32, copy=False),
        timestamps=(np.arange(16, dtype=np.int64) * 1800).astype(np.int64, copy=False),
        anchor_rows=np.array([1, 4, 7, 10], dtype=np.int64),
        context_start_rows=np.array([0, 3, 6, 9], dtype=np.int64),
        candidate_start_rows=np.array([2, 5, 8, 11], dtype=np.int64),
        candidate_end_rows=np.array([4, 7, 10, 13], dtype=np.int64),
        max_candidate_slots=2,
    )


def _poisson_config() -> dict[str, object]:
    return {
        "id": "poisson_replay_2h",
        "window_seconds": 7200,
        "arrival_rate_per_second": 0.01,
        "repetitions": 3,
        "seed": 2026,
    }


def _execution_policy():
    return compile_execution_policy_contract(
        coerce_execution_policy_config({"id": "strict_deadline_miss"})
    )


def test_evaluator_config_is_poisson_only_without_engine_sampler_or_aggregation() -> None:
    config = coerce_evaluator_config(_poisson_config())
    contract = compile_evaluator_contract(config)

    assert config.id == "poisson_replay_2h"
    assert contract.evaluation_id == "poisson_replay_2h"
    assert contract.config_payload == _poisson_config()

    with pytest.raises(ConfigResolutionError, match="Extra inputs"):
        coerce_evaluator_config({**_poisson_config(), "engine": "replay"})

    with pytest.raises(ConfigResolutionError, match="poisson_replay_2h"):
        coerce_evaluator_config({**_poisson_config(), "id": "other_evaluation"})


def test_evaluator_compile_requires_concrete_poisson_config() -> None:
    with pytest.raises(ConfigResolutionError, match="poisson_replay_2h"):
        compile_evaluator_contract(EvaluatorConfig(id="base"))


def test_metric_descriptors_and_evaluator_contract_validate_primary_metric() -> None:
    def unused_run_fn(
        _store: object,
        _execution_policy: object,
        _decoded_result: object,
        _sample_indices: object,
    ) -> EvaluationSummary:
        return EvaluationSummary(
            metrics=MetricSet(values={"profit": 0.0}),
            window_metrics={},
            total_events=0,
            runs=[EvaluationRun(n_events=0, metrics={"profit": 0.0}, metadata={})],
        )

    with pytest.raises(ValueError, match="metric.label must be non-empty"):
        MetricDescriptor(id="profit", label="", role="primary")

    with pytest.raises(ValueError, match="exactly one primary"):
        CompiledEvaluatorContract(
            evaluation_id="bad",
            metric_descriptors=(
                MetricDescriptor(id="profit", label="Profit", role="secondary"),
            ),
            primary_metric_id="profit",
            direction="maximize",
            config_payload={"id": "bad"},
            accepted_decoded_result_id="offsets",
            run_fn=unused_run_fn,
        )


def test_evaluator_rejects_incompatible_decoded_result_semantics() -> None:
    store = _store()
    evaluator = compile_evaluator_contract(coerce_evaluator_config(_poisson_config()))

    with pytest.raises(TypeError, match="decoded-result requirement"):
        evaluator.run(
            store,
            _execution_policy(),
            _OtherDecodedResult(),
            np.arange(store.n_samples, dtype=np.int64),
        )


def test_poisson_arrival_sampling_selects_previous_chronological_sample() -> None:
    rng = np.random.default_rng(7)

    arrivals = sample_poisson_arrivals(
        rng,
        rate_per_second=0.01,
        start_timestamp=100.0,
        end_timestamp=500.0,
    )

    assert arrivals.size > 0
    assert np.all(arrivals >= 100.0)
    assert np.all(arrivals < 500.0)
    assert select_sample_positions_for_arrivals(
        np.array([100, 200, 400], dtype=np.int64),
        np.array([50.0, 100.0, 199.9, 200.0, 450.0]),
    ).tolist() == [0, 0, 1, 2]


def test_poisson_replay_uses_event_mean_economic_metrics() -> None:
    store = _store()
    sample_indices = np.arange(store.n_samples, dtype=np.int64)
    offsets = DecodedOffsets(torch.tensor([0, 1, 0, 1], dtype=torch.int64))
    evaluator = compile_evaluator_contract(coerce_evaluator_config(_poisson_config()))

    summary = evaluator.run(store, _execution_policy(), offsets, sample_indices)
    expected = _expected_poisson_metrics(store, offsets, sample_indices)

    assert summary.total_events == expected.pop("total_events")
    assert summary.metrics.values == pytest.approx(expected)


def test_poisson_replay_handles_non_chronological_sample_indices() -> None:
    store = _store()
    forward_indices = np.arange(store.n_samples, dtype=np.int64)
    reversed_indices = forward_indices[::-1].copy()
    forward_offsets = torch.tensor([0, 1, 0, 1], dtype=torch.int64)
    reversed_offsets = DecodedOffsets(forward_offsets.flip(0))
    evaluator = compile_evaluator_contract(coerce_evaluator_config(_poisson_config()))

    summary = evaluator.run(
        store,
        _execution_policy(),
        DecodedOffsets(forward_offsets),
        forward_indices,
    )
    reversed_summary = evaluator.run(
        store,
        _execution_policy(),
        reversed_offsets,
        reversed_indices,
    )

    assert reversed_summary.metrics.values == pytest.approx(summary.metrics.values)
    assert reversed_summary.total_events == summary.total_events
    assert [run.n_events for run in reversed_summary.runs] == [
        run.n_events for run in summary.runs
    ]


def _expected_poisson_metrics(
    store: CompiledProblemStore,
    offsets: DecodedOffsets,
    sample_indices: np.ndarray,
) -> dict[str, float | int]:
    config = _poisson_config()
    chronological_samples = chronological_sample_view(store, sample_indices)
    first_timestamp = int(chronological_samples.sample_timestamps[0])
    last_timestamp = int(chronological_samples.sample_timestamps[-1])
    latest_start = last_timestamp - int(config["window_seconds"])
    rng = np.random.default_rng(int(config["seed"]))

    total_events = 0
    realized_fee_sum = 0.0
    baseline_fee_sum = 0.0
    optimum_fee_sum = 0.0
    profit_sum = 0.0
    cost_sum = 0.0
    baseline_cost_sum = 0.0

    for _ in range(int(config["repetitions"])):
        window_start = float(rng.uniform(first_timestamp, latest_start))
        arrivals = sample_poisson_arrivals(
            rng,
            rate_per_second=float(config["arrival_rate_per_second"]),
            start_timestamp=window_start,
            end_timestamp=window_start + int(config["window_seconds"]),
        )
        selected_positions = chronological_samples.sample_positions[
            select_sample_positions_for_arrivals(
                chronological_samples.sample_timestamps,
                arrivals,
            )
        ]
        if selected_positions.size == 0:
            continue
        selected_samples = sample_indices[selected_positions]
        windows = store.candidate_windows(selected_samples)
        selected_offsets = offsets.select(selected_positions).astype(np.int64, copy=False)
        realized_rows = windows.baseline_rows + selected_offsets
        realized_fees = np.exp(store.log_base_fees[realized_rows].astype(np.float64))
        baseline_fees = np.exp(store.log_base_fees[windows.baseline_rows].astype(np.float64))
        optimum_fees = np.exp(store.log_base_fees[windows.optimum_rows].astype(np.float64))

        total_events += int(selected_positions.shape[0])
        realized_fee_sum += float(realized_fees.sum())
        baseline_fee_sum += float(baseline_fees.sum())
        optimum_fee_sum += float(optimum_fees.sum())
        profit_sum += float(((baseline_fees - realized_fees) / baseline_fees).sum())
        cost_sum += float(((realized_fees - optimum_fees) / optimum_fees).sum())
        baseline_cost_sum += float(((baseline_fees - optimum_fees) / optimum_fees).sum())

    return {
        "profit_over_baseline": profit_sum / total_events,
        "cost_over_optimum": cost_sum / total_events,
        "baseline_cost_over_optimum": baseline_cost_sum / total_events,
        "realized_fee_sum": realized_fee_sum,
        "baseline_fee_sum": baseline_fee_sum,
        "optimum_fee_sum": optimum_fee_sum,
        "total_events": total_events,
    }
