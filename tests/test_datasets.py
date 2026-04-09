import unittest

from spice_temporal.config import SplitConfig
from spice_temporal.constants import EVALUATION_END_TS, EVALUATION_START_TS
from spice_temporal.datasets import (
    build_supervised_examples,
    candidate_block_count_for_delay,
    chronological_split,
    derive_dataset_geometry,
    earliest_min_offset,
    filter_examples_by_anchor_window,
    history_context_blocks,
    lookback_steps_for_seconds,
    max_extra_wait_steps_for_delay,
    trim_history_blocks_for_target,
)
from spice_temporal.features import build_feature_rows, feature_names
from spice_temporal.records import BlockRecord


def make_block(index: int, base_fee: int) -> BlockRecord:
    return BlockRecord(
        block_number=index,
        timestamp=1_700_000_000 + 12 * index,
        base_fee_per_gas=base_fee,
        gas_used=15_000_000 + index,
        gas_limit=30_000_000,
        chain_id=1,
    )


class DatasetLogicTestCase(unittest.TestCase):
    def test_fixed_step_mappings(self) -> None:
        self.assertEqual(lookback_steps_for_seconds(600, 12.0), 50)
        self.assertEqual(max_extra_wait_steps_for_delay(12, 12.0), 1)
        self.assertEqual(candidate_block_count_for_delay(12, 12.0), 2)
        self.assertEqual(max_extra_wait_steps_for_delay(36, 12.0), 3)
        self.assertEqual(candidate_block_count_for_delay(36, 12.0), 4)
        self.assertEqual(max_extra_wait_steps_for_delay(12, 1.6), 7)
        self.assertEqual(candidate_block_count_for_delay(12, 1.6), 8)

    def test_trim_history_blocks_for_target_uses_exact_tail_length(self) -> None:
        blocks = [make_block(index, 100 + index) for index in range(500)]
        geometry = derive_dataset_geometry(
            lookback_seconds=600,
            max_delay_seconds=36,
            block_time_seconds=12.0,
        )
        trimmed = trim_history_blocks_for_target(
            blocks,
            target_anchor_count=64,
            geometry=geometry,
        )
        self.assertEqual(len(trimmed), geometry.required_training_block_count(64))
        self.assertEqual(trimmed[0].block_number, 184)
        self.assertEqual(trimmed[-1].block_number, 499)

    def test_history_context_blocks_returns_exact_context_tail(self) -> None:
        blocks = [make_block(index, 100 + index) for index in range(500)]
        geometry = derive_dataset_geometry(
            lookback_seconds=600,
            max_delay_seconds=36,
            block_time_seconds=12.0,
        )
        context = history_context_blocks(blocks, geometry=geometry)
        self.assertEqual(len(context), geometry.context_block_count)
        self.assertEqual(context[0].block_number, 252)
        self.assertEqual(context[-1].block_number, 499)

    def test_earliest_min_offset_breaks_ties_early(self) -> None:
        self.assertEqual(earliest_min_offset([4.0, 2.0, 2.0, 3.0]), 1)

    def test_build_supervised_examples(self) -> None:
        blocks = [make_block(index, 100 + (index % 5)) for index in range(260)]
        rows = build_feature_rows(blocks)
        self.assertEqual(len(rows[0].features), len(feature_names()))
        examples = build_supervised_examples(rows, lookback_steps=5, candidate_block_count=4)
        self.assertGreater(len(examples), 0)
        first = examples[0]
        self.assertEqual(len(first.inputs), 5)
        self.assertIn(first.class_label, {0, 1, 2, 3})
        self.assertEqual(len(first.candidate_log_fees), 4)
        self.assertLessEqual(first.optimal_log_fee, first.next_block_log_fee)

    def test_filter_examples_by_anchor_window(self) -> None:
        blocks = [
            BlockRecord(
                block_number=index,
                timestamp=EVALUATION_START_TS - 3_600 + 12 * index,
                base_fee_per_gas=100 + (index % 5),
                gas_used=15_000_000 + index,
                gas_limit=30_000_000,
                chain_id=1,
            )
            for index in range(1_000)
        ]
        rows = build_feature_rows(blocks)
        examples = build_supervised_examples(rows, lookback_steps=50, candidate_block_count=4)
        filtered = filter_examples_by_anchor_window(
            examples,
            start_timestamp=EVALUATION_START_TS,
            end_timestamp=EVALUATION_END_TS,
        )
        self.assertGreater(len(filtered), 0)
        self.assertGreaterEqual(filtered[0].anchor_timestamp, EVALUATION_START_TS)
        self.assertLess(filtered[-1].anchor_timestamp, EVALUATION_END_TS)

    def test_chronological_split_preserves_order(self) -> None:
        blocks = [make_block(index, 100 + index) for index in range(260)]
        rows = build_feature_rows(blocks)
        examples = build_supervised_examples(rows, lookback_steps=5, candidate_block_count=4)
        split = chronological_split(examples, SplitConfig())
        self.assertLess(split.train[0].anchor_block_number, split.validation[0].anchor_block_number)
        self.assertLess(split.validation[0].anchor_block_number, split.test[0].anchor_block_number)


if __name__ == "__main__":
    unittest.main()
