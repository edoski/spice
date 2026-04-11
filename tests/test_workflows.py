from __future__ import annotations

import json

from spice.core.console import NullReporter
from spice.workflows.simulate import run as run_simulate
from spice.workflows.train import run as run_train
from spice.workflows.tune import run as run_tune
from tests.support import (
    base_overrides,
    compose_experiment,
    make_evaluation_rows,
    make_history_rows,
    write_dataset_dir,
)


def test_train_and_simulate_workflows_write_reports(tmp_path) -> None:
    train_config = compose_experiment("train", overrides=base_overrides(tmp_path))
    simulate_config = compose_experiment("simulate", overrides=base_overrides(tmp_path))

    history_dir = tmp_path / "artifacts" / "datasets" / "ethereum" / "enriched" / "history"
    evaluation_dir = tmp_path / "artifacts" / "datasets" / "ethereum" / "enriched" / "evaluation"
    write_dataset_dir(history_dir, make_history_rows())
    write_dataset_dir(evaluation_dir, make_evaluation_rows())

    run_train(train_config, reporter=NullReporter())
    run_simulate(simulate_config, reporter=NullReporter())

    train_report = (
        tmp_path
        / "artifacts"
        / "models"
        / "ethereum"
        / "lstm"
        / "36s"
        / "train_report.json"
    )
    simulation_report = (
        tmp_path
        / "artifacts"
        / "simulations"
        / "ethereum"
        / "lstm"
        / "36s"
        / "simulation_report.json"
    )
    assert train_report.is_file()
    assert simulation_report.is_file()


def test_train_workflow_creates_local_mlflow_run(tmp_path) -> None:
    config = compose_experiment(
        "train",
        overrides=base_overrides(tmp_path) + ["tracking.enabled=true"],
    )
    history_dir = tmp_path / "artifacts" / "datasets" / "ethereum" / "enriched" / "history"
    write_dataset_dir(history_dir, make_history_rows())

    run_train(config, reporter=NullReporter())

    mlruns_dir = tmp_path / "artifacts" / "mlruns"
    assert mlruns_dir.is_dir()
    assert (mlruns_dir / "mlflow.db").is_file()
    assert (mlruns_dir / "artifacts").is_dir()


def test_tune_workflow_writes_optuna_summary(tmp_path) -> None:
    config = compose_experiment("tune", overrides=base_overrides(tmp_path))
    config.tuning.n_trials = 2
    config.tuning.prune = False
    config.training.max_epochs = 1
    config.tracking.enabled = False
    config.tuning.search_space = {
        "training.learning_rate": [1e-4, 3e-4],
        "model.hidden_size": [64, 128],
    }

    history_dir = tmp_path / "artifacts" / "datasets" / "ethereum" / "enriched" / "history"
    write_dataset_dir(history_dir, make_history_rows())

    run_tune(config)

    summary_path = (
        tmp_path
        / "artifacts"
        / "tuning"
        / "ethereum"
        / "lstm"
        / "36s"
        / "best_params.json"
    )
    assert summary_path.is_file()
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert len(payload) == 2
