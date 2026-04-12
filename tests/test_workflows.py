from __future__ import annotations

import pytest
from typer.testing import CliRunner

from spice.cli import app
from spice.core.console import NullReporter
from spice.state.artifact import list_simulation_runs, load_training_summary
from spice.state.study import load_study
from spice.workflows.simulate import run as run_simulate
from spice.workflows.train import run as run_train
from spice.workflows.tune import run as run_tune
from tests.support import (
    deep_merge,
    load_test_simulate_config,
    load_test_train_config,
    load_test_tune_config,
    model_workflow_override,
    seed_evaluation_dataset,
    seed_history_dataset,
    tune_override,
)

runner = CliRunner()


def test_train_workflow_smoke(tmp_path) -> None:
    config = load_test_train_config(tmp_path, override=model_workflow_override())
    seed_history_dataset(config)

    run_train(config, reporter=NullReporter())

    assert config.paths.artifact_state_db.is_file()
    assert (config.paths.artifact_root / "model.pt").is_file()
    assert load_training_summary(config.paths.artifact_state_db) is not None


def test_tune_workflow_smoke(tmp_path) -> None:
    config = load_test_tune_config(
        tmp_path,
        override=deep_merge(model_workflow_override(), tune_override()),
    )
    seed_history_dataset(config)

    run_tune(config, reporter=NullReporter())

    assert config.paths.study_state_db.is_file()
    study = load_study(config.paths.study_state_db, study_name=config.study.id)
    assert len(study.trials) == config.tuning.trial_count

    tuned_train_config = load_test_train_config(
        tmp_path,
        override=deep_merge(
            model_workflow_override(),
            {
                "artifact": {"variant": "tuned"},
                "study": config.study.id,
            },
        ),
    )
    run_train(tuned_train_config, reporter=NullReporter())
    assert tuned_train_config.paths.artifact_state_db.is_file()
    assert (tuned_train_config.paths.artifact_root / "model.pt").is_file()


def test_simulate_workflow_smoke(tmp_path) -> None:
    train_config = load_test_train_config(tmp_path, override=model_workflow_override())
    simulate_config = load_test_simulate_config(tmp_path, override=model_workflow_override())
    seed_history_dataset(train_config)
    seed_evaluation_dataset(simulate_config)
    run_train(train_config, reporter=NullReporter())

    run_simulate(simulate_config, reporter=NullReporter())

    assert simulate_config.paths.artifact_state_db.is_file()
    assert list_simulation_runs(simulate_config.paths.artifact_state_db)


def test_simulate_rejects_dataset_contract_mismatch(tmp_path) -> None:
    base_override = model_workflow_override()
    train_config = load_test_train_config(tmp_path, override=base_override)
    simulate_config = load_test_simulate_config(
        tmp_path,
        override=deep_merge(base_override, {"dataset": {"history_context_blocks": 120}}),
    )
    seed_history_dataset(train_config)
    seed_evaluation_dataset(simulate_config)
    run_train(train_config, reporter=NullReporter())

    with pytest.raises(
        ValueError,
        match="Configured dataset.history_context_blocks is too small",
    ):
        run_simulate(simulate_config, reporter=NullReporter())


def test_show_command_smoke(tmp_path) -> None:
    config = load_test_train_config(tmp_path, override=model_workflow_override())
    seed_history_dataset(config)
    run_train(config, reporter=NullReporter())

    result = runner.invoke(app, ["show", str(config.paths.artifact_root)])

    assert result.exit_code == 0, result.stdout
    assert "artifact summary" in result.stdout
    assert config.model.id in result.stdout
