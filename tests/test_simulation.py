import unittest

from spice_temporal.records import SupervisedExample
from spice_temporal.simulation import run_temporal_simulation


def make_example(anchor_timestamp: int, label: int) -> SupervisedExample:
    candidates = [4.0, 3.0, 2.0, 1.0]
    if label == 0:
        candidates = [1.0, 2.0, 3.0, 4.0]
    elif label == 1:
        candidates = [2.0, 1.0, 3.0, 4.0]
    elif label == 2:
        candidates = [3.0, 2.0, 1.0, 4.0]
    return SupervisedExample(
        anchor_block_number=anchor_timestamp,
        anchor_timestamp=anchor_timestamp,
        inputs=[[0.0, 1.0] for _ in range(5)],
        class_label=label,
        target_log_fee=candidates[label],
        candidate_log_fees=candidates,
        next_block_log_fee=candidates[0],
        optimal_log_fee=min(candidates),
    )


class SimulationTestCase(unittest.TestCase):
    def test_run_temporal_simulation_is_deterministic(self) -> None:
        examples = [make_example(1_700_000_000 + 12 * index, index % 4) for index in range(800)]
        predicted_offsets = [example.class_label for example in examples]
        summary = run_temporal_simulation(
            examples,
            predicted_offsets,
            window_seconds=600,
            arrival_rate_per_second=0.02,
            repetitions=3,
            seed=2026,
        )
        repeat = run_temporal_simulation(
            examples,
            predicted_offsets,
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
