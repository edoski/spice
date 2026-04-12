from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from spice.core.console import NullReporter
from spice.data.io import load_block_frame
from spice.features import FeatureSelection, build_feature_table
from spice.modeling.artifacts import load_training_artifact
from spice.modeling.pipeline import prepare_training_dataset
from spice.modeling.torch_datasets import build_class_weights
from spice.modeling.training import evaluate_model
from spice.state.artifact import load_training_summary
from spice.workflows._shared import build_training_spec
from spice.workflows.train import run as run_train
from tests.support import load_test_train_config, model_workflow_override, seed_history_dataset


def test_elapsed_blocks_stays_anchored_to_dataset_origin() -> None:
    selection = FeatureSelection(
        feature_set_id="test_elapsed",
        feature_names=("elapsed_blocks",),
    )
    blocks = pl.DataFrame(
        {
            "block_number": np.arange(100, 111, dtype=np.int64),
            "timestamp": np.arange(1_700_000_000, 1_700_000_011, dtype=np.int64),
            "base_fee_per_gas": np.full(11, 1_000_000_000, dtype=np.int64),
            "gas_used": np.full(11, 18_000_000, dtype=np.int64),
            "gas_limit": np.full(11, 30_000_000, dtype=np.int64),
            "chain_id": np.ones(11, dtype=np.int64),
        }
    )

    origin_block_number = 100
    training_table = build_feature_table(
        blocks.slice(5, 5),
        dataset_origin_block_number=origin_block_number,
        selection=selection,
    )
    inference_table = build_feature_table(
        blocks.slice(3, 7),
        dataset_origin_block_number=origin_block_number,
        selection=selection,
    )

    np.testing.assert_array_equal(training_table.block_numbers, np.arange(105, 110, dtype=np.int64))
    np.testing.assert_allclose(training_table.feature_matrix[:, 0], np.arange(5.0, 10.0))
    np.testing.assert_array_equal(inference_table.block_numbers[-5:], training_table.block_numbers)
    np.testing.assert_allclose(inference_table.feature_matrix[-5:, 0], training_table.feature_matrix[:, 0])


def test_training_summary_metrics_match_replayed_saved_artifact(tmp_path) -> None:
    config = load_test_train_config(tmp_path, override=model_workflow_override())
    seed_history_dataset(config)

    run_train(config, reporter=NullReporter())

    summary = load_training_summary(config.paths.artifact_state_db)
    assert summary is not None

    loaded_artifact = load_training_artifact(config.paths.artifact_root)
    spec = build_training_spec(config)
    prepared = prepare_training_dataset(load_block_frame(config.paths.history_dir), spec=spec)
    class_weights = build_class_weights(
        prepared.store.class_labels,
        prepared.split_indices.train,
        prepared.action_count,
    )

    validation_metrics = evaluate_model(
        loaded_artifact.model,
        store=prepared.store,
        sample_indices=prepared.split_indices.validation,
        lookback_steps=prepared.geometry.lookback_steps,
        training_config=config.training,
        class_weights=class_weights,
        reporter=NullReporter(),
    )
    test_metrics = evaluate_model(
        loaded_artifact.model,
        store=prepared.store,
        sample_indices=prepared.split_indices.test,
        lookback_steps=prepared.geometry.lookback_steps,
        training_config=config.training,
        class_weights=class_weights,
        reporter=NullReporter(),
    )

    assert summary.best_validation_metrics.total_loss == pytest.approx(
        validation_metrics.total_loss
    )
    assert summary.best_validation_metrics.accuracy == pytest.approx(validation_metrics.accuracy)
    assert summary.best_validation_metrics.mean_profit_over_baseline == pytest.approx(
        validation_metrics.mean_profit_over_baseline
    )
    assert summary.test_metrics.total_loss == pytest.approx(test_metrics.total_loss)
    assert summary.test_metrics.accuracy == pytest.approx(test_metrics.accuracy)
    assert summary.test_metrics.mean_profit_over_baseline == pytest.approx(
        test_metrics.mean_profit_over_baseline
    )
