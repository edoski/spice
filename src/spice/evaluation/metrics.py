"""Evaluator metric descriptors."""

from __future__ import annotations

from ..prediction.base import MetricDescriptor

REPLAY_METRIC_DESCRIPTORS: tuple[MetricDescriptor, ...] = (
    MetricDescriptor(
        id="profit_over_baseline",
        label="profit over baseline",
        role="primary",
    ),
    MetricDescriptor(
        id="cost_over_optimum",
        label="cost over optimum",
        role="secondary",
    ),
    MetricDescriptor(
        id="baseline_cost_over_optimum",
        label="baseline cost over optimum",
        role="secondary",
    ),
    MetricDescriptor(
        id="realized_fee_sum",
        label="realized fee sum",
        role="diagnostic",
    ),
    MetricDescriptor(
        id="baseline_fee_sum",
        label="baseline fee sum",
        role="diagnostic",
    ),
    MetricDescriptor(
        id="optimum_fee_sum",
        label="optimum fee sum",
        role="diagnostic",
    ),
)

NOTEBOOK_ROLLOUT_METRIC_DESCRIPTORS: tuple[MetricDescriptor, ...] = (
    MetricDescriptor(
        id="profit_over_baseline",
        label="profit over baseline",
        role="primary",
    ),
    MetricDescriptor(
        id="cost_over_optimum",
        label="cost over optimum",
        role="secondary",
    ),
    MetricDescriptor(
        id="baseline_cost_over_optimum",
        label="baseline cost over optimum",
        role="secondary",
    ),
    MetricDescriptor(
        id="realized_fee_sum",
        label="realized fee sum",
        role="diagnostic",
    ),
    MetricDescriptor(
        id="baseline_fee_sum",
        label="baseline fee sum",
        role="diagnostic",
    ),
    MetricDescriptor(
        id="optimum_fee_sum",
        label="optimum fee sum",
        role="diagnostic",
    ),
    MetricDescriptor(
        id="mean_steps_to_stop",
        label="mean steps to stop",
        role="diagnostic",
    ),
    MetricDescriptor(
        id="zero_stop_rate",
        label="zero stop rate",
        role="diagnostic",
    ),
    MetricDescriptor(
        id="terminal_without_zero_count",
        label="terminal without zero count",
        role="diagnostic",
    ),
)

NOTEBOOK_BASEFEE_METRIC_DESCRIPTORS: tuple[MetricDescriptor, ...] = (
    MetricDescriptor(
        id="fee_delta_over_anchor",
        label="fee delta over anchor",
        role="primary",
    ),
    MetricDescriptor(
        id="realized_fee_sum",
        label="realized fee sum",
        role="diagnostic",
    ),
    MetricDescriptor(
        id="anchor_fee_sum",
        label="anchor fee sum",
        role="diagnostic",
    ),
    MetricDescriptor(
        id="overflow_count",
        label="overflow count",
        role="diagnostic",
    ),
    MetricDescriptor(
        id="zero_action_rate",
        label="zero action rate",
        role="diagnostic",
    ),
)
