from __future__ import annotations

import json
import sys

import polars as pl

from spice.acquisition.cryo import CryoRunResult, TimestampRange, run_cryo
from spice.acquisition.enrich import enrich_frame_with_gas_limit, enrich_path
from spice.core.config import ChainConfig, ChainName, ProviderConfig, PullConfig, RpcProviderName
from spice.core.console import NullReporter
from spice.data.block_schema import ENRICHED_BLOCK_SCHEMA
from spice.data.io import load_enriched_block_frame
from spice.workflows.acquire import run as run_acquire
from tests.support import (
    base_overrides,
    compose_experiment,
    make_block_rows,
    write_dataset_dir,
    write_raw_chunk,
)


def test_enrich_frame_with_gas_limit_fills_missing_blocks() -> None:
    def fetch_gas_limits(block_numbers: list[int]) -> dict[int, int]:
        return {block: 30_000_000 + block for block in block_numbers}

    frame = pl.DataFrame(
        make_block_rows(
            4,
            start_block=1,
            start_timestamp=1_700_000_000,
            include_gas_limit=True,
            missing_gas_limit_blocks={2, 4},
        )
    )

    enriched, fetched = enrich_frame_with_gas_limit(
        frame,
        fetch_gas_limits=fetch_gas_limits,
        batch_size=2,
        max_methods_per_second=1_000.0,
    )

    assert fetched == 2
    assert enriched.schema == ENRICHED_BLOCK_SCHEMA
    assert enriched["gas_limit"].to_list() == [30_000_000, 30_000_002, 30_000_000, 30_000_004]


def test_enrich_path_writes_parquet_outputs(tmp_path) -> None:
    def fetch_gas_limits(block_numbers: list[int]) -> dict[int, int]:
        return {block: 31_000_000 + block for block in block_numbers}

    input_dir = tmp_path / "raw"
    output_dir = tmp_path / "enriched"
    write_dataset_dir(
        input_dir,
        make_block_rows(
            5,
            start_block=1,
            start_timestamp=1_700_000_000,
            include_gas_limit=True,
            missing_gas_limit_blocks={1, 3},
        ),
    )

    written = enrich_path(
        input_dir,
        output_dir,
        fetch_gas_limits=fetch_gas_limits,
        batch_size=2,
        max_methods_per_second=1_000.0,
    )

    assert len(written) == 1
    assert written[0].is_file()
    written_frame = pl.read_parquet(written[0])
    assert written_frame.schema == ENRICHED_BLOCK_SCHEMA
    assert written_frame["gas_limit"].null_count() == 0


def test_run_cryo_polls_progress_before_stdout_lines(tmp_path, monkeypatch) -> None:
    class RecordingReporter(NullReporter):
        def __init__(self) -> None:
            self.pull_updates: list[tuple[int, int | None, str | None]] = []

        def update_pull(
            self,
            *,
            completed_chunks: int,
            total_chunks: int | None,
            latest_output: str | None = None,
        ) -> None:
            self.pull_updates.append((completed_chunks, total_chunks, latest_output))

    output_dir = tmp_path / "raw"
    reporter = RecordingReporter()
    provider = ProviderConfig(
        name=RpcProviderName.PUBLICNODE,
        endpoints={"ethereum": "https://rpc.example.test"},
        references={"ethereum": "https://rpc.example.test"},
    )
    script = "\n".join(
        [
            "from pathlib import Path",
            "import sys",
            "import time",
            "output_dir = Path(sys.argv[1])",
            "output_dir.mkdir(parents=True, exist_ok=True)",
            "time.sleep(0.05)",
            "(output_dir / 'ethereum__blocks__1_to_1.parquet').write_text('ok', encoding='utf-8')",
            "time.sleep(0.15)",
            "print('done', flush=True)",
        ]
    )

    monkeypatch.setattr(
        "spice.acquisition.cryo.build_cryo_args",
        lambda *_args, **_kwargs: [sys.executable, "-c", script, str(output_dir)],
    )
    monkeypatch.setattr(
        "spice.acquisition.cryo.build_cryo_command",
        lambda *_args, **_kwargs: "python fake_cryo.py",
    )

    result = run_cryo(
        ChainConfig(name=ChainName.ETHEREUM, chain_id=1, block_time_seconds=12.0, history_days=1),
        PullConfig(chunk_size=1),
        output_dir,
        TimestampRange(start=1, end=13),
        provider=provider,
        reporter=reporter,
    )

    assert result.completed_chunks == 1
    assert reporter.pull_updates
    assert reporter.pull_updates[0][0] == 1
    assert any(update[2] == "done" for update in reporter.pull_updates)


def test_acquire_workflow_writes_validation_reports(tmp_path, monkeypatch) -> None:
    config = compose_experiment(
        "acquire",
        overrides=base_overrides(tmp_path) + ["provider=publicnode", "pull.dry_run=false"],
    )

    def fake_run_cryo(chain, _pull, output_dir, timestamps, **_kwargs):
        segment = output_dir.name
        rows = make_block_rows(
            4,
            start_block=1 if segment == "history" else 10_001,
            start_timestamp=timestamps.start,
            include_gas_limit=False,
        )
        write_raw_chunk(output_dir, chain_name=chain.name.value, rows=rows)
        return CryoRunResult(command=f"cryo {segment}", completed_chunks=1, expected_chunks=1)

    class FakeBlockClient:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def get_block_gas_limits(self, block_numbers: list[int]) -> dict[int, int]:
            return {block_number: 30_000_000 for block_number in block_numbers}

    monkeypatch.setattr("spice.workflows.acquire.run_cryo", fake_run_cryo)
    monkeypatch.setattr("spice.workflows.acquire.Web3BlockClient", FakeBlockClient)

    run_acquire(config, reporter=NullReporter())

    validation_dir = tmp_path / "artifacts" / "validation" / "ethereum"
    assert (validation_dir / "history_raw.json").is_file()
    assert (validation_dir / "evaluation_raw.json").is_file()
    assert (validation_dir / "history_enriched.json").is_file()
    assert (validation_dir / "evaluation_enriched.json").is_file()
    payload = json.loads((validation_dir / "history_raw.json").read_text(encoding="utf-8"))
    assert payload["status"] == "clean"
    history_dir = tmp_path / "artifacts" / "datasets" / "ethereum" / "enriched" / "history"
    assert load_enriched_block_frame(history_dir).height > 0
