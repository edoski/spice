import json
import unittest
from dataclasses import asdict
from pathlib import Path

from spice_temporal.config import ChainConfig, ModelConfig, SplitConfig, TrainingConfig
from spice_temporal.constants import EVALUATION_START_TS
from spice_temporal.datasets import derive_dataset_geometry, lookback_steps_for_seconds
from spice_temporal.pipeline import (
    prepare_inference_dataset,
    prepare_training_dataset,
    run_training,
)
from spice_temporal.records import BlockRecord


def make_history_block(index: int) -> BlockRecord:
    return BlockRecord(
        block_number=index,
        timestamp=EVALUATION_START_TS - 12 * (420 - index),
        base_fee_per_gas=100 + ((index // 3) % 7),
        gas_used=15_000_000 + (index % 1000),
        gas_limit=30_000_000,
        chain_id=1,
    )


def make_evaluation_block(index: int) -> BlockRecord:
    return BlockRecord(
        block_number=1_000 + index,
        timestamp=EVALUATION_START_TS + 12 * index,
        base_fee_per_gas=120 + ((index // 5) % 9),
        gas_used=15_100_000 + (index % 1000),
        gas_limit=30_000_000,
        chain_id=1,
    )


class PipelineTestCase(unittest.TestCase):
    def test_derive_lookback_steps(self) -> None:
        self.assertEqual(lookback_steps_for_seconds(600, 12.0), 50)

    def test_prepare_training_dataset_enforces_target_anchor_count(self) -> None:
        blocks = [make_history_block(index) for index in range(420)]
        prepared = prepare_training_dataset(
            blocks,
            chain=ChainConfig(
                name="ethereum",
                chain_id=1,
                block_time_seconds=12.0,
                history_days=70,
            ),
            max_delay_seconds=12,
            lookback_seconds=600,
            target_anchor_count=64,
            split_config=SplitConfig(),
        )
        self.assertEqual(prepared.n_blocks_available, 420)
        self.assertEqual(prepared.n_examples_total, 64)
        self.assertEqual(prepared.geometry.lookback_steps, 50)
        self.assertEqual(prepared.geometry.max_extra_wait_steps, 1)
        self.assertEqual(prepared.geometry.candidate_block_count, 2)
        self.assertGreater(len(prepared.train_examples), 0)
        self.assertEqual(prepared.n_features, len(prepared.train_examples[0].inputs[0]))

    def test_prepare_inference_dataset_uses_history_context(self) -> None:
        history_blocks = [make_history_block(index) for index in range(420)]
        evaluation_blocks = [make_evaluation_block(index) for index in range(720)]
        training = prepare_training_dataset(
            history_blocks,
            chain=ChainConfig(
                name="ethereum",
                chain_id=1,
                block_time_seconds=12.0,
                history_days=70,
            ),
            max_delay_seconds=36,
            lookback_seconds=600,
            target_anchor_count=64,
            split_config=SplitConfig(),
        )
        geometry = derive_dataset_geometry(
            lookback_seconds=600,
            max_delay_seconds=36,
            block_time_seconds=12.0,
        )
        prepared = prepare_inference_dataset(
            history_blocks,
            evaluation_blocks,
            geometry=geometry,
            scaler=training.scaler,
        )
        self.assertEqual(prepared.n_history_context_blocks, geometry.context_block_count)
        self.assertEqual(prepared.n_evaluation_blocks, 720)
        self.assertGreater(prepared.n_examples_total, 0)
        self.assertGreaterEqual(prepared.examples[0].anchor_timestamp, EVALUATION_START_TS)

    def test_run_training_on_json(self) -> None:
        blocks = [asdict(make_history_block(index)) for index in range(420)]
        fixture = Path("tests/fixtures_blocks.json")
        fixture.write_text(json.dumps(blocks), encoding="utf-8")
        try:
            result = run_training(
                history_block_path=fixture,
                chain=ChainConfig(
                    name="ethereum",
                    chain_id=1,
                    block_time_seconds=12.0,
                    history_days=70,
                ),
                max_delay_seconds=12,
                lookback_seconds=600,
                target_anchor_count=64,
                model_config=ModelConfig(family="lstm"),
                training_config=TrainingConfig(max_epochs=2, effective_batch_size=8, device="cpu"),
                split_config=SplitConfig(),
            )
        finally:
            fixture.unlink(missing_ok=True)
        self.assertEqual(result.prepared.n_blocks_available, 420)
        self.assertEqual(result.prepared.n_examples_total, 64)
        self.assertGreaterEqual(result.training_result.best_epoch, 0)
        self.assertGreaterEqual(result.test_metrics.accuracy, 0.0)


if __name__ == "__main__":
    unittest.main()
