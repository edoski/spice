from __future__ import annotations

import math

import numpy as np
import polars as pl
import pytest
import torch

from spice.core.console import NullReporter
from spice.data.datasets import build_temporal_store
from spice.data.io import load_block_frame
from spice.features import FeatureSelection, build_feature_table
from spice.modeling.artifacts import load_training_artifact
from spice.modeling.objective import (
    EpochMetrics,
    best_epoch,
    compute_objective_loss,
    optuna_direction,
    primary_validation_metric_name,
)
from spice.modeling.pipeline import prepare_training_dataset
from spice.modeling.simulation import run_temporal_simulation
from spice.modeling.training import evaluate_model
from spice.planning.geometry import DelayWindow
from spice.state.artifact import (
    list_training_epochs,
    load_training_summary,
)
from spice.workflows._shared import build_training_spec
from spice.workflows.train import run as run_train
from tests.support import load_test_train_config, model_workflow_override, seed_history_dataset


def _build_test_store() -> object:
    selection = FeatureSelection(
        feature_set_id="test_timestamp_native",
        feature_names=("seconds_since_previous_block", "elapsed_seconds"),
    )
    blocks = pl.DataFrame(
        {
            "block_number": np.arange(100, 107, dtype=np.int64),
            "timestamp": np.array([0, 5, 11, 18, 27, 29, 40], dtype=np.int64),
            "base_fee_per_gas": np.full(7, 1_000_000_000, dtype=np.int64),
            "gas_used": np.full(7, 18_000_000, dtype=np.int64),
            "gas_limit": np.full(7, 30_000_000, dtype=np.int64),
            "chain_id": np.ones(7, dtype=np.int64),
        }
    )
    feature_table = build_feature_table(blocks, selection=selection)
    return build_temporal_store(
        feature_table,
        window=DelayWindow(
            lookback_seconds=10,
            delay_seconds=12,
            feature_history_seconds=feature_table.feature_history_seconds,
        ),
    )


def test_temporal_store_uses_real_timestamps_for_context_and_candidates() -> None:
    store = _build_test_store()
    np.testing.assert_array_equal(store.anchor_rows, np.array([2, 3, 4, 5], dtype=np.int64))
    np.testing.assert_array_equal(store.context_start_rows, np.array([1, 2, 3, 4], dtype=np.int64))
    np.testing.assert_array_equal(
        store.candidate_end_rows - store.candidate_start_rows,
        np.array([1, 2, 1, 1], dtype=np.int64),
    )
    assert store.max_candidate_slots == 2


def test_objective_loss_prefers_cheaper_candidates_and_ignores_masked_slots() -> None:
    candidate_log_fees = torch.tensor(
        [[math.log(10.0), math.log(5.0), math.log(1000.0)]],
        dtype=torch.float32,
    )
    candidate_mask = torch.tensor([[True, True, False]])
    logits_bad = torch.tensor([[4.0, -4.0, 100.0]], dtype=torch.float32)
    logits_good = torch.tensor([[-4.0, 4.0, 100.0]], dtype=torch.float32)

    bad_loss = compute_objective_loss(logits_bad, candidate_log_fees, candidate_mask)
    good_loss = compute_objective_loss(logits_good, candidate_log_fees, candidate_mask)

    assert good_loss.item() < bad_loss.item()


def test_objective_selection_follows_validation_profit() -> None:
    history = [
        EpochMetrics(
            objective_loss=0.90,
            exact_optimum_hit_rate=0.30,
            cost_over_optimum=0.25,
            profit_over_baseline=0.04,
        ),
        EpochMetrics(
            objective_loss=1.20,
            exact_optimum_hit_rate=0.20,
            cost_over_optimum=0.18,
            profit_over_baseline=0.11,
        ),
        EpochMetrics(
            objective_loss=0.70,
            exact_optimum_hit_rate=0.40,
            cost_over_optimum=0.20,
            profit_over_baseline=0.08,
        ),
    ]

    assert best_epoch(history) == 2
    assert primary_validation_metric_name() == "validation_profit_over_baseline"
    assert optuna_direction() == "maximize"


def test_simulation_summary_uses_event_weighted_totals() -> None:
    store = _build_test_store()
    sample_indices = np.arange(store.n_samples, dtype=np.int64)
    predictions = [0] * store.n_samples

    summary = run_temporal_simulation(
        store,
        predictions,
        sample_indices=sample_indices,
        window_seconds=8,
        arrival_rate_per_second=0.3,
        repetitions=4,
        seed=2026,
        reporter=NullReporter(),
    )

    realized_fee_sum = sum(run.realized_fee_sum for run in summary.runs)
    baseline_fee_sum = sum(run.baseline_fee_sum for run in summary.runs)
    optimum_fee_sum = sum(run.optimum_fee_sum for run in summary.runs)

    assert summary.profit_over_baseline == pytest.approx(
        (baseline_fee_sum - realized_fee_sum) / baseline_fee_sum
    )
    assert summary.cost_over_optimum == pytest.approx(
        (realized_fee_sum - optimum_fee_sum) / optimum_fee_sum
    )
    assert summary.window_profit_over_baseline.mean == pytest.approx(
        np.mean([run.profit_over_baseline for run in summary.runs])
    )


def test_training_summary_metrics_match_replayed_saved_artifact(tmp_path) -> None:
    config = load_test_train_config(tmp_path, override=model_workflow_override())
    seed_history_dataset(config)

    run_train(config, reporter=NullReporter())

    summary = load_training_summary(config.paths.artifact_state_db)
    assert summary is not None

    loaded_artifact = load_training_artifact(config.paths.artifact_root)
    spec = build_training_spec(config)
    prepared = prepare_training_dataset(load_block_frame(config.paths.history_dir), spec=spec)

    validation_metrics = evaluate_model(
        loaded_artifact.model,
        model_id=config.model.id,
        store=prepared.store,
        sample_indices=prepared.split_indices.validation,
        training_config=config.training,
        reporter=NullReporter(),
    )
    test_metrics = evaluate_model(
        loaded_artifact.model,
        model_id=config.model.id,
        store=prepared.store,
        sample_indices=prepared.split_indices.test,
        training_config=config.training,
        reporter=NullReporter(),
    )

    assert summary.objective_id == "profit_over_baseline"
    assert summary.best_validation_metrics.objective_loss == pytest.approx(
        validation_metrics.objective_loss
    )
    assert summary.best_validation_metrics.exact_optimum_hit_rate == pytest.approx(
        validation_metrics.exact_optimum_hit_rate
    )
    assert summary.best_validation_metrics.profit_over_baseline == pytest.approx(
        validation_metrics.profit_over_baseline
    )
    assert summary.test_metrics.objective_loss == pytest.approx(test_metrics.objective_loss)
    assert summary.test_metrics.exact_optimum_hit_rate == pytest.approx(
        test_metrics.exact_optimum_hit_rate
    )
    assert summary.test_metrics.profit_over_baseline == pytest.approx(
        test_metrics.profit_over_baseline
    )

    epochs = list_training_epochs(config.paths.artifact_state_db)
    assert epochs
    assert epochs[summary.best_epoch - 1].epoch == summary.best_epoch
    assert epochs[summary.best_epoch - 1].validation_metrics.profit_over_baseline == pytest.approx(
        summary.best_validation_metrics.profit_over_baseline
    )
