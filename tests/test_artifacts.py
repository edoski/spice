import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

import torch

from spice_temporal.artifacts import (
    ARTIFACT_MANIFEST_FILENAME,
    MODEL_STATE_FILENAME,
    build_training_artifact_manifest,
    load_training_artifact,
    write_training_artifact,
)
from spice_temporal.config import ChainConfig, ModelConfig, SplitConfig, TrainingConfig
from spice_temporal.constants import EVALUATION_START_TS
from spice_temporal.pipeline import run_training
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


class ArtifactRoundTripTestCase(unittest.TestCase):
    def test_write_and_load_training_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            history_blocks_path = tmp_path / "history.json"
            history_blocks_path.write_text(
                json.dumps([asdict(make_history_block(index)) for index in range(420)]),
                encoding="utf-8",
            )
            result = run_training(
                history_block_path=history_blocks_path,
                chain=ChainConfig(
                    name="ethereum",
                    chain_id=1,
                    block_time_seconds=12.0,
                    history_days=1,
                ),
                max_delay_seconds=36,
                lookback_seconds=600,
                target_anchor_count=64,
                model_config=ModelConfig(family="lstm"),
                training_config=TrainingConfig(max_epochs=2, effective_batch_size=8, device="cpu"),
                split_config=SplitConfig(),
            )
            manifest = build_training_artifact_manifest(
                result.prepared,
                chain=ChainConfig(
                    name="ethereum",
                    chain_id=1,
                    block_time_seconds=12.0,
                    history_days=1,
                ),
                max_delay_seconds=36,
                lookback_seconds=600,
                target_anchor_count=64,
                model_config=ModelConfig(family="lstm"),
            )
            artifact_dir = tmp_path / "artifact"
            write_training_artifact(artifact_dir, manifest=manifest, model=result.model)
            loaded = load_training_artifact(artifact_dir)

            self.assertTrue((artifact_dir / ARTIFACT_MANIFEST_FILENAME).exists())
            self.assertTrue((artifact_dir / MODEL_STATE_FILENAME).exists())
            self.assertEqual(loaded.manifest.max_delay_seconds, 36)
            self.assertEqual(loaded.manifest.n_classes, result.prepared.n_classes)
            with torch.no_grad():
                sample = torch.tensor(
                    result.prepared.train_examples[0].inputs,
                    dtype=torch.float32,
                ).unsqueeze(0)
                outputs = loaded.model(sample)
            self.assertEqual(outputs.logits.shape[-1], result.prepared.n_classes)


if __name__ == "__main__":
    unittest.main()
