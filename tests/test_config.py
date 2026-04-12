from __future__ import annotations

import pytest

from spice.core.config import ArtifactVariant, WorkflowTask
from tests.support import (
    TEST_WINDOW_END_TIMESTAMP,
    TEST_WINDOW_START_TIMESTAMP,
    base_overrides,
    compose_experiment,
)


def test_experiment_defaults_load_and_paths_include_feature_set(tmp_path) -> None:
    config = compose_experiment("train", overrides=base_overrides(tmp_path))

    assert config.task is WorkflowTask.TRAIN
    assert config.dataset.id == "icdcs_2025_11_09"
    assert config.feature_set.id == "icdcs_2026"
    assert config.artifact.variant is ArtifactVariant.BASELINE
    assert config.paths.artifact_root.as_posix().endswith(
        "/ethereum/icdcs_2025_11_09/icdcs_2026/lstm/36s/baseline/default"
    )
    assert config.paths.history_dir.as_posix().endswith(
        "/datasets/ethereum/icdcs_2025_11_09/history"
    )
    assert config.paths.dataset_metadata_path.as_posix().endswith(
        "/datasets/ethereum/icdcs_2025_11_09/.spice/metadata.json"
    )


def test_cli_overrides_win_over_experiment_defaults(tmp_path) -> None:
    config = compose_experiment(
        "train",
        overrides=base_overrides(tmp_path)
        + [
            "model=transformer",
            "dataset.temporal.max_delay_seconds=24",
        ],
    )

    assert config.model.id == "transformer"
    assert config.dataset.temporal.max_delay_seconds == 24
    assert config.paths.artifact_root.as_posix().endswith(
        "/ethereum/icdcs_2025_11_09/icdcs_2026/transformer/24s/baseline/default"
    )


def test_direct_provider_reads_env_interpolation(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ETHEREUM_RPC_URL", "https://eth.example.test")
    config = compose_experiment(
        "acquire",
        overrides=base_overrides(tmp_path) + ["provider=direct"],
    )

    assert config.provider.endpoint_for(config.chain.name) == "https://eth.example.test"
    assert config.provider.reference_for(config.chain.name) == "$ETHEREUM_RPC_URL"
    assert config.acquisition.rpc_batch_size == 256
    assert config.acquisition.chunk_size == 8192


def test_acquire_requires_direct_provider_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("ETHEREUM_RPC_URL", raising=False)

    with pytest.raises(ValueError, match="Missing RPC endpoint for chain: ethereum"):
        compose_experiment(
            "acquire",
            overrides=base_overrides(tmp_path) + ["provider=direct"],
        )


def test_evaluation_date_resolves_to_derived_windows(tmp_path) -> None:
    config = compose_experiment("simulate", overrides=base_overrides(tmp_path))

    assert config.evaluation_window_start_timestamp == TEST_WINDOW_START_TIMESTAMP
    assert config.evaluation_window_end_timestamp == TEST_WINDOW_END_TIMESTAMP
    assert config.history_window_end_timestamp == TEST_WINDOW_START_TIMESTAMP


def test_invalid_rpc_concurrency_config_fails_early(tmp_path) -> None:
    with pytest.raises(
        ValueError,
        match="rpc_concurrency must be present in rpc_concurrency_rungs",
    ):
        compose_experiment(
            "acquire",
            overrides=base_overrides(tmp_path) + ["acquisition.rpc_concurrency=12"],
        )


def test_invalid_transformer_config_fails_early(tmp_path) -> None:
    with pytest.raises(ValueError, match="d_model must be divisible by nhead"):
        compose_experiment(
            "train",
            overrides=base_overrides(tmp_path)
            + ["model=transformer", "model.d_model=126", "model.nhead=8"],
        )


def test_tuning_space_model_id_mismatch_fails_early(tmp_path) -> None:
    with pytest.raises(ValueError, match="tuning_space.model.id must match model.id"):
        compose_experiment(
            "tune",
            overrides=base_overrides(tmp_path)
            + ["model=transformer", "tuning_space=lstm_default"],
        )


def test_history_sample_budget_cannot_be_smaller_than_sample_count(tmp_path) -> None:
    with pytest.raises(
        ValueError,
        match="acquisition.history_sample_budget must be at least dataset.sampling.sample_count",
    ):
        compose_experiment(
            "acquire",
            overrides=base_overrides(tmp_path)
            + ["acquisition.history_sample_budget=32"],
        )
