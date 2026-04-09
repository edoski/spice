import tempfile
import unittest
from pathlib import Path

from spice_temporal.io import write_rows
from spice_temporal.raw_validation import validate_raw_pull


def make_raw_row(block_number: int, timestamp: int, *, chain_id: int = 1) -> dict[str, int]:
    return {
        "block_number": block_number,
        "timestamp": timestamp,
        "base_fee_per_gas": 100 + block_number,
        "gas_used": 15_000_000 + block_number,
        "chain_id": chain_id,
    }


def write_raw_file(path: Path, rows: list[dict[str, int]]) -> None:
    write_rows(path, rows)


class RawPullValidationTestCase(unittest.TestCase):
    def test_validate_raw_pull_passes_clean_contiguous_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dataset_dir = Path(tmp_dir)
            write_raw_file(
                dataset_dir / "ethereum__blocks__1_to_3.parquet",
                [make_raw_row(1, 1_000), make_raw_row(2, 1_012), make_raw_row(3, 1_024)],
            )
            nested_hidden = dataset_dir / ".cryo" / "reports"
            nested_hidden.mkdir(parents=True)
            (nested_hidden / "ignored.json").write_text("{}", encoding="utf-8")

            report = validate_raw_pull(
                dataset_dir,
                expected_chain_name="ethereum",
                expected_chain_id=1,
                expected_start_timestamp=999,
                expected_end_timestamp=2_000,
            )

        self.assertEqual(report.status, "clean")
        self.assertEqual(report.file_count, 1)
        self.assertEqual(report.row_count, 3)
        self.assertEqual(report.gap_count, 0)
        self.assertEqual(report.overlap_count, 0)

    def test_validate_raw_pull_rejects_malformed_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dataset_dir = Path(tmp_dir)
            write_raw_file(
                dataset_dir / "bad.parquet",
                [make_raw_row(1, 1_000)],
            )

            report = validate_raw_pull(
                dataset_dir,
                expected_chain_name="ethereum",
                expected_chain_id=1,
                expected_start_timestamp=999,
                expected_end_timestamp=2_000,
            )

        self.assertEqual(report.status, "error")
        self.assertTrue(any("Malformed raw block filename" in error for error in report.errors))

    def test_validate_raw_pull_detects_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dataset_dir = Path(tmp_dir)
            write_raw_file(
                dataset_dir / "ethereum__blocks__1_to_2.parquet",
                [make_raw_row(1, 1_000), make_raw_row(2, 1_012)],
            )
            write_raw_file(
                dataset_dir / "ethereum__blocks__4_to_5.parquet",
                [make_raw_row(4, 1_024), make_raw_row(5, 1_036)],
            )

            report = validate_raw_pull(
                dataset_dir,
                expected_chain_name="ethereum",
                expected_chain_id=1,
                expected_start_timestamp=999,
                expected_end_timestamp=2_000,
            )

        self.assertEqual(report.status, "error")
        self.assertEqual(report.gap_count, 1)

    def test_validate_raw_pull_detects_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dataset_dir = Path(tmp_dir)
            write_raw_file(
                dataset_dir / "ethereum__blocks__1_to_3.parquet",
                [make_raw_row(1, 1_000), make_raw_row(2, 1_012), make_raw_row(3, 1_024)],
            )
            write_raw_file(
                dataset_dir / "ethereum__blocks__3_to_5.parquet",
                [make_raw_row(3, 1_024), make_raw_row(4, 1_036), make_raw_row(5, 1_048)],
            )

            report = validate_raw_pull(
                dataset_dir,
                expected_chain_name="ethereum",
                expected_chain_id=1,
                expected_start_timestamp=999,
                expected_end_timestamp=2_000,
            )

        self.assertEqual(report.status, "error")
        self.assertEqual(report.overlap_count, 1)
        self.assertEqual(report.duplicate_count, 1)

    def test_validate_raw_pull_rejects_mixed_chain_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dataset_dir = Path(tmp_dir)
            write_raw_file(
                dataset_dir / "ethereum__blocks__1_to_2.parquet",
                [make_raw_row(1, 1_000), make_raw_row(2, 1_012, chain_id=137)],
            )

            report = validate_raw_pull(
                dataset_dir,
                expected_chain_name="ethereum",
                expected_chain_id=1,
                expected_start_timestamp=999,
                expected_end_timestamp=2_000,
            )

        self.assertEqual(report.status, "error")
        self.assertEqual(report.chain_id_mismatch_count, 1)

    def test_validate_raw_pull_warns_for_single_pre_start_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dataset_dir = Path(tmp_dir)
            write_raw_file(
                dataset_dir / "ethereum__blocks__1_to_3.parquet",
                [make_raw_row(1, 999), make_raw_row(2, 1_011), make_raw_row(3, 1_023)],
            )

            report = validate_raw_pull(
                dataset_dir,
                expected_chain_name="ethereum",
                expected_chain_id=1,
                expected_start_timestamp=1_000,
                expected_end_timestamp=2_000,
            )

        self.assertEqual(report.status, "warning")
        self.assertEqual(report.below_start_count, 1)

    def test_validate_raw_pull_rejects_broad_timestamp_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dataset_dir = Path(tmp_dir)
            write_raw_file(
                dataset_dir / "ethereum__blocks__1_to_3.parquet",
                [make_raw_row(1, 998), make_raw_row(2, 999), make_raw_row(3, 1_023)],
            )

            report = validate_raw_pull(
                dataset_dir,
                expected_chain_name="ethereum",
                expected_chain_id=1,
                expected_start_timestamp=1_000,
                expected_end_timestamp=2_000,
            )

        self.assertEqual(report.status, "error")
        self.assertEqual(report.below_start_count, 2)


if __name__ == "__main__":
    unittest.main()
