from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from spice.acquisition.rpc import BlockPullPlan, BlockRange, TimestampRange
from spice.core.console import NullReporter, create_reporter
from spice.workflows.acquire import run as run_acquire
from spice.workflows.simulate import run as run_simulate
from spice.workflows.train import run as run_train
from spice.workflows.tune import run as run_tune
from tests.support import (
    base_overrides,
    compute_required_history_blocks,
    compose_experiment,
    make_block_rows,
    make_evaluation_rows,
    make_history_rows,
    write_dataset_dir,
)


def _reporter(stream: StringIO):
    return create_reporter(Console(file=stream, force_terminal=False, width=120))


def _seed_train_history(config) -> Path:
    history_dir = config.paths.history_dir
    write_dataset_dir(history_dir, make_history_rows())
    return history_dir


def _seed_simulation_inputs(train_config, simulate_config) -> tuple[Path, Path]:
    history_dir = _seed_train_history(train_config)
    evaluation_dir = simulate_config.paths.evaluation_dir
    write_dataset_dir(evaluation_dir, make_evaluation_rows())
    return history_dir, evaluation_dir


def test_train_workflow_smoke(tmp_path) -> None:
    config = compose_experiment("train", overrides=base_overrides(tmp_path))
    _seed_train_history(config)
    stream = StringIO()
    reporter = _reporter(stream)

    run_train(config, reporter=reporter)
    reporter.close()

    assert (config.paths.artifact_root / "artifact.json").is_file()
    assert (config.paths.artifact_root / "model.pt").is_file()
    assert config.paths.train_report_path.is_file()
    assert "training summary" in stream.getvalue()


def test_tune_workflow_smoke(tmp_path) -> None:
    config = compose_experiment(
        "tune",
        overrides=base_overrides(tmp_path) + ["tuning_space=lstm_default"],
    )
    config.tuning.trial_count = 2
    config.tuning.enable_pruning = False
    assert config.tuning_space is not None
    config.tuning_space.training.learning_rate = [1e-4, 3e-4]
    config.tuning_space.model.hidden_size = [64, 128]
    _seed_train_history(config)

    run_tune(config, reporter=NullReporter())

    assert (config.paths.tuning_root / "study.json").is_file()
    assert (config.paths.tuning_root / "trials.json").is_file()
    assert config.paths.tuning_best_params_path.is_file()


def test_acquire_workflow_smoke(tmp_path, monkeypatch) -> None:
    config = compose_experiment(
        "acquire",
        overrides=base_overrides(tmp_path)
        + [
            "dataset.temporal.lookback_seconds=24",
            "dataset.temporal.max_delay_seconds=12",
            "dataset.sampling.sample_count=4",
            "acquisition.history_sample_budget=4",
        ],
    )
    required_history_blocks = compute_required_history_blocks(config)
    block_time_seconds = int(config.chain.block_time_seconds)
    expected_history_start = (
        config.evaluation_window_start_timestamp - required_history_blocks * block_time_seconds
    )

    class FakeSummaryBlockClient:
        def __init__(self, provider, chain) -> None:
            del provider
            self.chain = chain

        async def close(self) -> None:
            return None

        async def plan_history_window(
            self,
            *,
            end_timestamp: int,
            required_history_blocks: int,
            chunk_size: int,
        ) -> BlockPullPlan:
            del chunk_size
            return BlockPullPlan(
                window=TimestampRange(start=expected_history_start, end=end_timestamp),
                block_range=BlockRange(start=100, end=100 + required_history_blocks),
                expected_rows=required_history_blocks,
                expected_files=1,
            )

        async def plan_window(self, window: TimestampRange, *, chunk_size: int) -> BlockPullPlan:
            del chunk_size
            if window.end == config.evaluation_window_start_timestamp:
                return BlockPullPlan(
                    window=window,
                    block_range=BlockRange(start=100, end=100 + required_history_blocks),
                    expected_rows=required_history_blocks,
                    expected_files=1,
                )
            return BlockPullPlan(
                window=window,
                block_range=BlockRange(start=10_001, end=10_033),
                expected_rows=32,
                expected_files=1,
            )

        def plan_block_range(
            self,
            block_range: BlockRange,
            *,
            window: TimestampRange,
            chunk_size: int,
        ) -> BlockPullPlan:
            return BlockPullPlan(
                window=window,
                block_range=block_range,
                expected_rows=block_range.count,
                expected_files=max(1, (block_range.count + chunk_size - 1) // chunk_size),
            )

        async def pull_block_range(
            self,
            output_dir: Path,
            *,
            plan: BlockPullPlan,
            chunk_size: int,
            rpc_controller,
            reporter,
        ) -> BlockPullPlan:
            del chunk_size, rpc_controller, reporter
            rows = make_block_rows(
                plan.expected_rows,
                start_block=plan.block_range.start,
                start_timestamp=plan.window.start,
                block_time_seconds=block_time_seconds,
                include_gas_limit=True,
            )
            write_dataset_dir(output_dir, rows)
            return plan

    monkeypatch.setattr("spice.workflows.acquire.Web3BlockClient", FakeSummaryBlockClient)
    stream = StringIO()
    reporter = _reporter(stream)

    run_acquire(config, reporter=reporter)
    reporter.close()

    output = stream.getvalue()
    assert config.paths.dataset_metadata_path.is_file()
    assert "acquisition summary" in output
    assert "Ethereum" in output


def test_simulate_workflow_smoke(tmp_path) -> None:
    train_config = compose_experiment("train", overrides=base_overrides(tmp_path))
    simulate_config = compose_experiment("simulate", overrides=base_overrides(tmp_path))
    _seed_simulation_inputs(train_config, simulate_config)
    run_train(train_config, reporter=NullReporter())
    stream = StringIO()
    reporter = _reporter(stream)

    run_simulate(simulate_config, reporter=reporter)
    reporter.close()

    output = stream.getvalue()
    assert simulate_config.paths.simulation_report_path.is_file()
    assert "simulation summary" in output
    assert "variant: baseline" in output


def test_simulate_rejects_feature_set_mismatch(tmp_path) -> None:
    train_config = compose_experiment("train", overrides=base_overrides(tmp_path))
    simulate_config = compose_experiment("simulate", overrides=base_overrides(tmp_path))
    _seed_simulation_inputs(train_config, simulate_config)
    run_train(train_config, reporter=NullReporter())
    simulate_config.feature_set.id = "wrong_feature_set"

    with pytest.raises(
        ValueError,
        match="Configured feature_set.id does not match the trained artifact",
    ):
        run_simulate(simulate_config, reporter=NullReporter())
