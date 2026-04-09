import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from typer.testing import CliRunner

from spice_temporal.cli import app
from spice_temporal.records import BlockRecord


def make_block(index: int) -> BlockRecord:
    return BlockRecord(
        block_number=index,
        timestamp=1_700_000_000 + 12 * index,
        base_fee_per_gas=100 + ((index // 3) % 7),
        gas_used=15_000_000 + (index % 1000),
        gas_limit=30_000_000,
        chain_id=1,
    )


class CliTrainingTestCase(unittest.TestCase):
    def test_train_writes_report_for_dataset_directory(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp_dir:
            dataset_dir = Path(tmp_dir) / "dataset"
            dataset_dir.mkdir()
            (dataset_dir / "blocks.json").write_text(
                json.dumps([asdict(make_block(index)) for index in range(420)]),
                encoding="utf-8",
            )
            report_path = Path(tmp_dir) / "report.json"
            result = runner.invoke(
                app,
                [
                    "train",
                    "configs/pilots/ethereum-36s.yaml",
                    str(dataset_dir),
                    "ethereum",
                    "lstm",
                    "36",
                    "--device",
                    "cpu",
                    "--report-path",
                    str(report_path),
                ],
            )
            self.assertEqual(result.exit_code, 0, msg=result.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["chain"], "ethereum")
        self.assertEqual(report["family"], "lstm")
        self.assertEqual(report["max_delay_seconds"], 36)
        self.assertEqual(report["block_time_seconds"], 12.0)
        self.assertEqual(report["max_extra_wait_steps"], 3)
        self.assertEqual(report["candidate_block_count"], 4)
        self.assertGreater(report["n_blocks"], 0)
        self.assertGreater(report["split_sizes"]["train_examples"], 0)


if __name__ == "__main__":
    unittest.main()
