import unittest

import numpy as np
import torch

from spice_temporal.config import ModelConfig, TrainingConfig
from spice_temporal.datasets import TemporalDatasetStore
from spice_temporal.evaluation import BatchMetrics
from spice_temporal.models import build_model
from spice_temporal.normalization import fit_standard_scaler, transform_feature_matrix
from spice_temporal.torch_datasets import build_class_weights
from spice_temporal.training import _mean_metrics, train_model


def make_store() -> TemporalDatasetStore:
    n_rows = 40
    feature_matrix = np.asarray(
        [[float(index % 3), float(index)] for index in range(n_rows)],
        dtype=np.float32,
    )
    anchor_row_indices = np.arange(4, 34, dtype=np.int64)
    n_samples = int(anchor_row_indices.shape[0])
    class_labels = np.asarray([index % 3 for index in range(n_samples)], dtype=np.int64)
    action_pattern = [[1.0, 2.0, 3.0], [3.0, 1.0, 2.0], [3.0, 2.0, 1.0]]
    action_log_fees = np.asarray(
        action_pattern * (n_samples // 3) + [action_pattern[0]] * (n_samples % 3),
        dtype=np.float32,
    )[:n_samples]
    target_log_fee = action_log_fees[np.arange(n_samples), class_labels]
    return TemporalDatasetStore(
        feature_matrix=feature_matrix,
        block_numbers=np.arange(n_rows, dtype=np.int64),
        timestamps=np.arange(1_700_000_000, 1_700_000_000 + n_rows, dtype=np.int64),
        anchor_row_indices=anchor_row_indices,
        class_labels=class_labels,
        action_log_fees=action_log_fees,
        target_log_fee=target_log_fee.astype(np.float32),
        next_block_log_fee=action_log_fees[:, 0].copy(),
        optimal_log_fee=action_log_fees.min(axis=1).astype(np.float32),
    )


class TrainingSmokeTestCase(unittest.TestCase):
    def test_epoch_metrics_are_ratio_of_sums(self) -> None:
        summary = _mean_metrics(
            [
                BatchMetrics(
                    count=4,
                    total_loss_sum=4.0,
                    correct_count=2,
                    realized_fee_sum=20.0,
                    baseline_fee_sum=24.0,
                    optimal_fee_sum=16.0,
                ),
                BatchMetrics(
                    count=1,
                    total_loss_sum=3.0,
                    correct_count=1,
                    realized_fee_sum=2.0,
                    baseline_fee_sum=4.0,
                    optimal_fee_sum=1.0,
                ),
            ]
        )
        self.assertAlmostEqual(summary.total_loss, 1.4)
        self.assertAlmostEqual(summary.accuracy, 0.6)
        self.assertAlmostEqual(summary.mean_cost_over_optimum, 5.0 / 17.0)
        self.assertAlmostEqual(summary.mean_profit_over_baseline, 6.0 / 28.0)

    def test_build_class_weights_uses_inverse_frequency(self) -> None:
        class_labels = np.asarray([0, 0, 1, 2, 2, 2], dtype=np.int64)
        sample_indices = np.arange(class_labels.shape[0], dtype=np.int64)
        weights = build_class_weights(class_labels, sample_indices, 3)
        expected = torch.tensor([0.5, 1.0, 1.0 / 3.0], dtype=torch.float32)
        self.assertTrue(torch.allclose(weights, expected))

    def test_build_class_weights_requires_all_classes(self) -> None:
        class_labels = np.asarray([0, 0, 0, 1], dtype=np.int64)
        sample_indices = np.arange(class_labels.shape[0], dtype=np.int64)
        with self.assertRaises(ValueError):
            build_class_weights(class_labels, sample_indices, 3)

    def test_lstm_smoke_train(self) -> None:
        store = make_store()
        train_indices = np.arange(0, 24, dtype=np.int64)
        validation_indices = np.arange(24, 30, dtype=np.int64)
        scaler = fit_standard_scaler(
            store.feature_matrix,
            anchor_row_indices=store.anchor_row_indices,
            sample_indices=train_indices,
            lookback_steps=5,
        )
        scaled_store = TemporalDatasetStore(
            feature_matrix=transform_feature_matrix(store.feature_matrix, scaler),
            block_numbers=store.block_numbers,
            timestamps=store.timestamps,
            anchor_row_indices=store.anchor_row_indices,
            class_labels=store.class_labels,
            action_log_fees=store.action_log_fees,
            target_log_fee=store.target_log_fee,
            next_block_log_fee=store.next_block_log_fee,
            optimal_log_fee=store.optimal_log_fee,
        )
        model = build_model(
            n_features=2,
            action_count=3,
            config=ModelConfig(family="lstm"),
        )
        result = train_model(
            model,
            store=scaled_store,
            train_sample_indices=train_indices,
            validation_sample_indices=validation_indices,
            lookback_steps=5,
            training_config=TrainingConfig(max_epochs=2, effective_batch_size=8, device="cpu"),
        )
        self.assertGreaterEqual(result.best_epoch, 0)
        self.assertGreater(len(result.train_history), 0)
        with torch.no_grad():
            inputs = torch.from_numpy(scaled_store.feature_matrix[:5]).unsqueeze(0)
            outputs = model(inputs)
        self.assertEqual(outputs.logits.shape[-1], 3)


if __name__ == "__main__":
    unittest.main()
