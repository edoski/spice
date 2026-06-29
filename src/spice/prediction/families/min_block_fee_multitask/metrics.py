"""Paper-family training metrics."""

from __future__ import annotations

from dataclasses import dataclass

import torch

from ....metrics import MetricDescriptor, MetricSet
from .batch import MinBlockFeeTargetBatch, MinBlockFeeTrainingState
from .loss import compute_multitask_loss
from .outputs import masked_offset_argmax


@dataclass(frozen=True, slots=True)
class OffsetClassificationCounts:
    correct_count: int
    true_positive_by_class: tuple[int, ...]
    predicted_by_class: tuple[int, ...]
    target_by_class: tuple[int, ...]


def offset_classification_counts(
    predicted_offsets: torch.Tensor,
    target_offsets: torch.Tensor,
    *,
    n_classes: int,
) -> OffsetClassificationCounts:
    if n_classes <= 0:
        raise ValueError("n_classes must be positive")
    predicted = predicted_offsets.detach().to(device="cpu", dtype=torch.int64).reshape(-1)
    target = target_offsets.detach().to(device="cpu", dtype=torch.int64).reshape(-1)
    if predicted.shape != target.shape:
        raise ValueError("predicted_offsets and target_offsets must have matching shape")
    if predicted.numel() == 0:
        raise ValueError("offset classification metrics require at least one sample")
    if bool(((predicted < 0) | (predicted >= n_classes)).any()):
        raise ValueError("predicted_offsets contain values outside the action width")
    if bool(((target < 0) | (target >= n_classes)).any()):
        raise ValueError("target_offsets contain values outside the action width")

    correct_mask = predicted == target
    true_positive = torch.bincount(
        target[correct_mask],
        minlength=n_classes,
    )
    predicted_count = torch.bincount(predicted, minlength=n_classes)
    target_count = torch.bincount(target, minlength=n_classes)
    return OffsetClassificationCounts(
        correct_count=int(correct_mask.sum().item()),
        true_positive_by_class=_count_tuple(true_positive, n_classes=n_classes),
        predicted_by_class=_count_tuple(predicted_count, n_classes=n_classes),
        target_by_class=_count_tuple(target_count, n_classes=n_classes),
    )


def add_offset_classification_counts(
    left: OffsetClassificationCounts | None,
    right: OffsetClassificationCounts,
) -> OffsetClassificationCounts:
    if left is None:
        return right
    if len(left.true_positive_by_class) != len(right.true_positive_by_class):
        raise ValueError("offset classification count widths do not match")
    return OffsetClassificationCounts(
        correct_count=left.correct_count + right.correct_count,
        true_positive_by_class=_add_count_tuples(
            left.true_positive_by_class,
            right.true_positive_by_class,
        ),
        predicted_by_class=_add_count_tuples(left.predicted_by_class, right.predicted_by_class),
        target_by_class=_add_count_tuples(left.target_by_class, right.target_by_class),
    )


def macro_f1_from_counts(counts: OffsetClassificationCounts) -> float:
    values: list[float] = []
    for true_positive, predicted_count, target_count in zip(
        counts.true_positive_by_class,
        counts.predicted_by_class,
        counts.target_by_class,
        strict=True,
    ):
        if target_count <= 0:
            continue
        precision = true_positive / predicted_count if predicted_count > 0 else 0.0
        recall = true_positive / target_count
        if precision <= 0.0 or recall <= 0.0:
            values.append(0.0)
            continue
        values.append(2.0 * precision * recall / (precision + recall))
    if not values:
        raise ValueError("macro_f1 requires at least one supported target class")
    return sum(values) / len(values)


def _count_tuple(values: torch.Tensor, *, n_classes: int) -> tuple[int, ...]:
    return tuple(int(value) for value in values[:n_classes].tolist())


def _add_count_tuples(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(
        left_value + right_value
        for left_value, right_value in zip(left, right, strict=True)
    )


@dataclass(frozen=True, slots=True)
class _MinBlockFeeMetricTotals:
    total_loss_sum: float
    classification_loss_sum: float
    regression_loss_sum: float
    log_fee_absolute_error_sum: float
    log_fee_squared_error_sum: float
    offset_counts: OffsetClassificationCounts


@dataclass(slots=True)
class MinBlockFeeEpochAccumulator:
    totals: _MinBlockFeeMetricTotals | None = None

    def update(self, batch_state: object) -> None:
        if not isinstance(batch_state, _MinBlockFeeMetricTotals):
            raise TypeError("min_block_fee_multitask expects metric totals")
        self.totals = _add_metric_totals(self.totals, batch_state)

    def finalize(self) -> MetricSet:
        if self.totals is None:
            raise ValueError("Cannot summarize an empty accumulator")
        return _metric_set_from_totals(self.totals)


TRAINING_METRIC_DESCRIPTORS: tuple[MetricDescriptor, ...] = (
    MetricDescriptor(id="total_loss", label="total loss", role="primary"),
    MetricDescriptor(
        id="offset_accuracy",
        label="offset accuracy",
        role="secondary",
    ),
    MetricDescriptor(
        id="classification_loss",
        label="classification loss",
        role="diagnostic",
    ),
    MetricDescriptor(
        id="regression_loss",
        label="regression loss",
        role="diagnostic",
    ),
    MetricDescriptor(
        id="macro_f1",
        label="macro F1",
        role="diagnostic",
    ),
    MetricDescriptor(
        id="log_fee_mae",
        label="log fee MAE",
        role="diagnostic",
    ),
    MetricDescriptor(
        id="log_fee_mse",
        label="log fee MSE",
        role="diagnostic",
    ),
)


def compute_batch_loss_and_state(
    offset_logits: torch.Tensor,
    fee_predictions: torch.Tensor,
    targets: MinBlockFeeTargetBatch,
    *,
    training_state: MinBlockFeeTrainingState,
) -> tuple[torch.Tensor, _MinBlockFeeMetricTotals]:
    total_loss, classification_loss, regression_loss = compute_multitask_loss(
        offset_logits,
        fee_predictions,
        targets,
        training_state=training_state,
    )
    decoded_offsets = masked_offset_argmax(
        offset_logits.detach(),
        targets.action_mask,
    )
    resolved_state = training_state.resolve(
        device=fee_predictions.device,
        dtype=fee_predictions.dtype,
    )
    predicted_log_fees = fee_predictions.detach() * resolved_state.fee_std + resolved_state.fee_mean
    log_fee_errors = predicted_log_fees - targets.min_block_log_fees.to(
        device=predicted_log_fees.device,
        dtype=predicted_log_fees.dtype,
    )
    count = int(targets.min_block_offsets.shape[0])
    offset_counts = offset_classification_counts(
        decoded_offsets,
        targets.min_block_offsets,
        n_classes=int(targets.action_mask.shape[1]),
    )
    return total_loss, _MinBlockFeeMetricTotals(
        total_loss_sum=float(total_loss.detach().item()) * count,
        classification_loss_sum=float(classification_loss.detach().item()) * count,
        regression_loss_sum=float(regression_loss.detach().item()) * count,
        log_fee_absolute_error_sum=float(log_fee_errors.abs().sum().detach().item()),
        log_fee_squared_error_sum=float(log_fee_errors.square().sum().detach().item()),
        offset_counts=offset_counts,
    )


def create_epoch_accumulator() -> MinBlockFeeEpochAccumulator:
    return MinBlockFeeEpochAccumulator()


def inverse_frequency_class_weights(
    offsets: torch.Tensor,
    *,
    n_classes: int,
) -> torch.Tensor:
    if offsets.ndim != 1:
        raise ValueError("offsets must be one-dimensional")
    if offsets.numel() == 0:
        raise ValueError("offsets must be non-empty")
    counts = torch.bincount(
        offsets.detach().to(device="cpu", dtype=torch.int64),
        minlength=n_classes,
    ).to(dtype=torch.float32)
    weights = torch.zeros(n_classes, dtype=torch.float32)
    present = counts > 0
    weights[present] = 1.0 / counts[present]
    if bool(present.any()):
        weights[present] *= float(present.sum().item()) / float(weights[present].sum().item())
    return weights


def _metric_set_from_totals(totals: _MinBlockFeeMetricTotals) -> MetricSet:
    count = _sample_count(totals.offset_counts)
    if count <= 0:
        raise ValueError("Cannot summarize an empty accumulator")
    return MetricSet(
        values={
            "total_loss": totals.total_loss_sum / count,
            "classification_loss": totals.classification_loss_sum / count,
            "regression_loss": totals.regression_loss_sum / count,
            "offset_accuracy": totals.offset_counts.correct_count / count,
            "macro_f1": macro_f1_from_counts(totals.offset_counts),
            "log_fee_mae": totals.log_fee_absolute_error_sum / count,
            "log_fee_mse": totals.log_fee_squared_error_sum / count,
        }
    )


def _add_metric_totals(
    left: _MinBlockFeeMetricTotals | None,
    right: _MinBlockFeeMetricTotals,
) -> _MinBlockFeeMetricTotals:
    if left is None:
        return right
    return _MinBlockFeeMetricTotals(
        total_loss_sum=left.total_loss_sum + right.total_loss_sum,
        classification_loss_sum=(
            left.classification_loss_sum + right.classification_loss_sum
        ),
        regression_loss_sum=left.regression_loss_sum + right.regression_loss_sum,
        log_fee_absolute_error_sum=(
            left.log_fee_absolute_error_sum + right.log_fee_absolute_error_sum
        ),
        log_fee_squared_error_sum=(
            left.log_fee_squared_error_sum + right.log_fee_squared_error_sum
        ),
        offset_counts=add_offset_classification_counts(
            left.offset_counts,
            right.offset_counts,
        ),
    )


def _sample_count(counts: OffsetClassificationCounts) -> int:
    return sum(counts.target_by_class)
