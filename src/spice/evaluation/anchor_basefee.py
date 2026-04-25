"""Anchor-basefee evaluator."""

from __future__ import annotations

import numpy as np

from ..prediction import DecodedOffsets
from ..prediction.contracts import DecodedPredictionResult, require_decoded_offsets
from ..temporal.problem_store import CompiledProblemStore
from ..temporal.realization import CompiledRealizationPolicyContract
from .config import AnchorBasefeeEvaluatorConfig
from .contracts import CompiledEvaluatorContract, EvaluationSummary, IntVector
from .metrics import ANCHOR_BASEFEE_METRIC_DESCRIPTORS
from .summary import single_run_summary


def run_anchor_basefee_fullset(
    store: CompiledProblemStore,
    realization_policy: CompiledRealizationPolicyContract,
    decoded_result: DecodedPredictionResult,
    sample_indices: IntVector,
) -> EvaluationSummary:
    decoded_offsets = require_decoded_offsets(decoded_result)
    if sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")
    selected_positions = np.arange(sample_indices.shape[0], dtype=np.int64)
    realized = realization_policy.realize_selections(
        store,
        decoded_offsets,
        sample_indices,
        selected_positions,
    )
    anchor_rows = store.anchor_rows[sample_indices.astype(np.int64, copy=False)]
    realized_total = float(
        np.exp(store.log_base_fees[realized.realized_rows].astype(np.float64, copy=False)).sum()
    )
    anchor_total = float(
        np.exp(store.log_base_fees[anchor_rows].astype(np.float64, copy=False)).sum()
    )
    if anchor_total <= 0.0:
        raise ValueError("anchor fee total must be positive")
    requested_offsets = decoded_offsets.select(selected_positions)
    return single_run_summary(
        metric_values={
            "fee_delta_over_anchor": (anchor_total - realized_total) / anchor_total,
            "realized_fee_sum": realized_total,
            "anchor_fee_sum": anchor_total,
            "overflow_count": float(realized.overflow_mask.sum()),
            "zero_action_rate": float((requested_offsets == 0).mean(dtype=np.float64)),
        },
        n_events=int(sample_indices.shape[0]),
        metadata={
            "mode": "anchor_basefee_fullset",
            "overflow_count": int(realized.overflow_mask.sum()),
            "zero_action_count": int(np.count_nonzero(requested_offsets == 0)),
        },
    )


def compile_anchor_basefee_evaluator_contract(
    config: AnchorBasefeeEvaluatorConfig,
) -> CompiledEvaluatorContract:
    return CompiledEvaluatorContract(
        evaluation_id=config.id,
        metric_descriptors=ANCHOR_BASEFEE_METRIC_DESCRIPTORS,
        primary_metric_id="fee_delta_over_anchor",
        direction="maximize",
        config_payload=config.model_dump(mode="json", exclude_none=True),
        accepted_decoded_result_id=DecodedOffsets.decoded_result_id,
        run_fn=run_anchor_basefee_fullset,
    )
