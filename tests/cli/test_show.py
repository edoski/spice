from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from spice.cli import app
from spice.config import (
    load_simulate_config,
    load_train_config,
    load_tune_config,
)
from spice.core.reporting import NullReporter
from spice.features import compile_feature_contract
from spice.temporal.contracts import compile_problem_contract
from spice.workflows.simulate import run as run_simulate
from spice.workflows.train import run as run_train
from spice.workflows.tune import run as run_tune

runner = CliRunner()


def _model_workflow_override(
    *,
    sample_count: int = 24,
    lookback_seconds: int = 120,
    max_supported_delay_seconds: int = 36,
    requested_delay_seconds: int | None = None,
    compiler_id: str = "estimated_block",
) -> dict[str, object]:
    feature_set_name = (
        "icdcs_2026_time_native" if compiler_id == "timestamp_native" else "icdcs_2026"
    )
    return {
        "chain": "ethereum",
        "model": "lstm",
        "feature_set": feature_set_name,
        "dataset": {
            "evaluation_date": "2025-11-09",
        },
        "problem": {
            "id": "test_problem",
            "lookback_seconds": lookback_seconds,
            "sample_count": sample_count,
            "max_supported_delay_seconds": max_supported_delay_seconds,
            "compiler": {"id": compiler_id},
        },
        "execution": {
            "id": "test_execution",
            "requested_delay_seconds": (
                max_supported_delay_seconds
                if requested_delay_seconds is None
                else requested_delay_seconds
            ),
        },
        "training": {
            "device": "cpu",
            "batch_size": 8,
            "max_epochs": 1,
            "log_every_n_steps": 1,
            "precision": "fp32",
            "compile": "off",
            "early_stopping": {
                "patience": 1,
                "min_delta": 0.0,
            },
        },
        "simulation": {
            "window_seconds": 600,
            "arrival_rate_per_second": 0.02,
            "repetitions": 3,
            "seed": 2026,
        },
        "tuning": {
            "trial_count": 2,
            "enable_pruning": False,
        },
    }


def _tune_override() -> dict[str, object]:
    return {
        "tuning_space": {
            "training": {
                "learning_rate": [0.0001, 0.0003],
                "weight_decay": [0.0, 0.01],
            },
            "model": {
                "id": "lstm",
                "hidden_size": [64, 128],
                "dropout": [0.0, 0.1],
            },
        }
    }


def _write_override(tmp_path: Path, payload: dict[str, object], *, name: str) -> Path:
    import yaml

    path = tmp_path / name
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _load_test_train_config(
    tmp_path: Path,
    *,
    override: dict[str, object] | None = None,
):
    config_path = (
        None if override is None else _write_override(tmp_path, override, name="train.yaml")
    )
    return load_train_config(
        preset="icdcs_2026",
        config_path=config_path,
        storage_root=tmp_path / "outputs",
    )


def _load_test_tune_config(
    tmp_path: Path,
    *,
    override: dict[str, object] | None = None,
):
    config_path = (
        None if override is None else _write_override(tmp_path, override, name="tune.yaml")
    )
    return load_tune_config(
        preset="icdcs_2026",
        config_path=config_path,
        storage_root=tmp_path / "outputs",
    )


def _load_test_simulate_config(
    tmp_path: Path,
    *,
    override: dict[str, object] | None = None,
):
    config_path = (
        None if override is None else _write_override(tmp_path, override, name="simulate.yaml")
    )
    return load_simulate_config(
        preset="icdcs_2026",
        config_path=config_path,
        storage_root=tmp_path / "outputs",
    )


def _seed_dataset(path: Path, rows: list[dict[str, int]]) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    parquet_path = path / "blocks.parquet"
    pl.DataFrame(rows).write_parquet(parquet_path)
    return parquet_path


def _seed_history_dataset(config) -> Path:
    feature_contract = compile_feature_contract(feature_set=config.feature_set)
    contract = compile_problem_contract(
        problem=config.problem,
        feature_contract=feature_contract,
    )
    block_interval_seconds = 12
    row_count = max(
        128,
        ((contract.required_history_seconds + contract.max_supported_delay_seconds + 12) // 12)
        + contract.warmup_rows
        + contract.sample_count
        + 16,
    )
    rows = [
        {
            "block_number": index,
            "timestamp": 1_000 + index * block_interval_seconds,
            "base_fee_per_gas": 1_000_000_000,
            "gas_used": 18_000_000,
            "gas_limit": 30_000_000,
            "chain_id": config.chain.runtime.chain_id,
        }
        for index in range(1, row_count + 1)
    ]
    return _seed_dataset(config.paths.history_dir, rows)


def _seed_evaluation_dataset(config) -> Path:
    rows = [
        {
            "block_number": index,
            "timestamp": config.evaluation_window_start_timestamp + (index - 10_001) * 12,
            "base_fee_per_gas": 1_000_000_000,
            "gas_used": 18_000_000,
            "gas_limit": 30_000_000,
            "chain_id": config.chain.runtime.chain_id,
        }
        for index in range(10_001, 10_065)
    ]
    return _seed_dataset(config.paths.evaluation_dir, rows)


def test_show_command_smoke(tmp_path) -> None:
    override = _model_workflow_override()
    train_config = _load_test_train_config(tmp_path, override=override)
    simulate_config = _load_test_simulate_config(tmp_path, override=override)
    _seed_history_dataset(train_config)
    _seed_evaluation_dataset(simulate_config)
    run_train(train_config, reporter=NullReporter())
    run_simulate(simulate_config, reporter=NullReporter())

    result = runner.invoke(
        app,
        [
            "show",
            "artifact",
            "--chain",
            train_config.chain.name,
            "--dataset",
            train_config.dataset.name,
            "--feature-set",
            train_config.feature_set.id,
            "--model",
            train_config.model.id,
            "--problem",
            train_config.problem.id,
            "--variant",
            train_config.artifact.variant.value,
            "--storage-root",
            str(tmp_path / "outputs"),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "artifact summary" in result.stdout
    assert train_config.model.id in result.stdout
    assert "simulation" in result.stdout


def test_show_study_config_detail_smoke(tmp_path) -> None:
    config = _load_test_tune_config(
        tmp_path,
        override={**_model_workflow_override(), **_tune_override()},
    )
    _seed_history_dataset(config)
    run_tune(config, reporter=NullReporter())

    result = runner.invoke(
        app,
        [
            "show",
            "study",
            "--chain",
            config.chain.name,
            "--dataset",
            config.dataset.name,
            "--feature-set",
            config.feature_set.id,
            "--model",
            config.model.id,
            "--problem",
            config.problem.id,
            "--study",
            config.study.name,
            "--storage-root",
            str(tmp_path / "outputs"),
            "--detail",
            "config",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "study summary" in result.stdout
    assert "tuning space" in result.stdout
    assert "learning rate" in result.stdout


def test_delete_artifact_command_smoke(tmp_path) -> None:
    config = _load_test_train_config(tmp_path, override=_model_workflow_override())
    _seed_history_dataset(config)
    run_train(config, reporter=NullReporter())

    result = runner.invoke(
        app,
        [
            "delete",
            "artifact",
            "--chain",
            config.chain.name,
            "--dataset",
            config.dataset.name,
            "--feature-set",
            config.feature_set.id,
            "--model",
            config.model.id,
            "--problem",
            config.problem.id,
            "--variant",
            config.artifact.variant.value,
            "--storage-root",
            str(tmp_path / "outputs"),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert not config.paths.artifact_root.exists()
