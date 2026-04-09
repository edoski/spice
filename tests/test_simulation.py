import unittest

import numpy as np

from spice_temporal.datasets import TemporalDatasetStore
from spice_temporal.simulation import run_temporal_simulation, summarize_realized_costs


def make_store() -> TemporalDatasetStore:
    action_log_fees = np.asarray(
        [
            [1.0, 2.0, 3.0, 4.0],
            [2.0, 1.0, 3.0, 4.0],
            [3.0, 2.0, 1.0, 4.0],
            [4.0, 3.0, 2.0, 1.0],
        ]
        * 200,
        dtype=np.float32,
    )
    n_samples = action_log_fees.shape[0]
    n_rows = n_samples + 5
    class_labels = np.asarray([index % 4 for index in range(n_samples)], dtype=np.int64)
    return TemporalDatasetStore(
        feature_matrix=np.zeros((n_rows, 2), dtype=np.float32),
        block_numbers=np.arange(n_rows, dtype=np.int64),
        timestamps=np.arange(1_700_000_000, 1_700_000_000 + n_rows * 12, 12, dtype=np.int64),
        anchor_row_indices=np.arange(4, 4 + n_samples, dtype=np.int64),
        class_labels=class_labels,
        action_log_fees=action_log_fees,
        target_log_fee=action_log_fees[np.arange(n_samples), class_labels],
        next_block_log_fee=action_log_fees[:, 0].copy(),
        optimal_log_fee=action_log_fees.min(axis=1).astype(np.float32),
    )


class SimulationTestCase(unittest.TestCase):
    def test_summarize_realized_costs_aggregates_total_costs(self) -> None:
        store = make_store()
        sample_indices = np.asarray([0, 1, 2], dtype=np.int64)
        predicted_offsets = [1, 0, 2]
        summary = summarize_realized_costs(
            store,
            predicted_offsets,
            sample_indices,
            [0, 1, 2],
            window_start_timestamp=0.0,
            window_end_timestamp=1.0,
            n_arrivals=3,
        )
        realized = np.exp(np.asarray([2.0, 2.0, 1.0], dtype=np.float64)).sum()
        baseline = np.exp(np.asarray([1.0, 2.0, 3.0], dtype=np.float64)).sum()
        optimum = np.exp(np.asarray([1.0, 1.0, 1.0], dtype=np.float64)).sum()
        self.assertAlmostEqual(summary.profit_over_baseline, (baseline - realized) / baseline)
        self.assertAlmostEqual(summary.cost_over_optimum, (realized - optimum) / optimum)
        self.assertAlmostEqual(
            summary.baseline_cost_over_optimum,
            (baseline - optimum) / optimum,
        )

    def test_run_temporal_simulation_is_deterministic(self) -> None:
        store = make_store()
        sample_indices = np.arange(store.anchor_row_indices.shape[0], dtype=np.int64)
        predicted_offsets = store.class_labels.tolist()
        summary = run_temporal_simulation(
            store,
            predicted_offsets,
            sample_indices=sample_indices,
            window_seconds=600,
            arrival_rate_per_second=0.02,
            repetitions=3,
            seed=2026,
        )
        repeat = run_temporal_simulation(
            store,
            predicted_offsets,
            sample_indices=sample_indices,
            window_seconds=600,
            arrival_rate_per_second=0.02,
            repetitions=3,
            seed=2026,
        )
        self.assertAlmostEqual(
            summary.mean_profit_over_baseline,
            repeat.mean_profit_over_baseline,
        )
        self.assertAlmostEqual(
            summary.mean_cost_over_optimum,
            repeat.mean_cost_over_optimum,
        )
        self.assertGreater(summary.total_events, 0)
        self.assertEqual(len(summary.runs), 3)


if __name__ == "__main__":
    unittest.main()
