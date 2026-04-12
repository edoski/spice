from __future__ import annotations

import pytest

from spice.core.console import NullReporter
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


def test_train_workflow_smoke(tmp_path) -> None:
    config = load_test_train_config(tmp_path, override=model_workflow_override())
    seed_history_dataset(config)

    run_train(config, reporter=NullReporter())

    assert (config.paths.artifact_root / "artifact.json").is_file()
    assert (config.paths.artifact_root / "model.pt").is_file()
    assert config.paths.train_report_path.is_file()


def test_tune_workflow_smoke(tmp_path) -> None:
    config = load_test_tune_config(
        tmp_path,
        override=deep_merge(model_workflow_override(), tune_override()),
    )
    seed_history_dataset(config)

    run_tune(config, reporter=NullReporter())

    assert (config.paths.tuning_root / "study.json").is_file()
    assert (config.paths.tuning_root / "trials.json").is_file()
    assert config.paths.tuning_best_params_path.is_file()


def test_simulate_workflow_smoke(tmp_path) -> None:
    train_config = load_test_train_config(tmp_path, override=model_workflow_override())
    simulate_config = load_test_simulate_config(tmp_path, override=model_workflow_override())
    seed_history_dataset(train_config)
    seed_evaluation_dataset(simulate_config)
    run_train(train_config, reporter=NullReporter())

    run_simulate(simulate_config, reporter=NullReporter())

    assert simulate_config.paths.simulation_report_path.is_file()


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
