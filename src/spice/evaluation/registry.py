"""Evaluator contract registry."""

from __future__ import annotations

from ..prediction import DecodedOffsets
from .config import EvaluationEngine, EvaluationSampler, EvaluatorConfig
from .contracts import CompiledEvaluatorContract, RunEvaluatorFn
from .metrics import (
    NOTEBOOK_BASEFEE_METRIC_DESCRIPTORS,
    NOTEBOOK_ROLLOUT_METRIC_DESCRIPTORS,
    REPLAY_METRIC_DESCRIPTORS,
)
from .notebook import run_notebook_basefee_fullset, run_notebook_rollout_fullset
from .replay import run_fullset, run_poisson_arrivals, run_uniform_window


def compile_evaluator_contract(
    evaluator_config: EvaluatorConfig,
) -> CompiledEvaluatorContract:
    if evaluator_config.engine is EvaluationEngine.NOTEBOOK_ROLLOUT:
        return CompiledEvaluatorContract(
            evaluation_id=evaluator_config.id,
            metric_descriptors=NOTEBOOK_ROLLOUT_METRIC_DESCRIPTORS,
            primary_metric_id="profit_over_baseline",
            direction="maximize",
            config_payload=evaluator_config.model_dump(mode="json", exclude_none=True),
            accepted_decoded_result_id=DecodedOffsets.decoded_result_id,
            run_fn=run_notebook_rollout_fullset,
        )
    if evaluator_config.engine is EvaluationEngine.NOTEBOOK_BASEFEE:
        return CompiledEvaluatorContract(
            evaluation_id=evaluator_config.id,
            metric_descriptors=NOTEBOOK_BASEFEE_METRIC_DESCRIPTORS,
            primary_metric_id="fee_delta_over_anchor",
            direction="maximize",
            config_payload=evaluator_config.model_dump(mode="json", exclude_none=True),
            accepted_decoded_result_id=DecodedOffsets.decoded_result_id,
            run_fn=run_notebook_basefee_fullset,
        )
    if evaluator_config.sampler is EvaluationSampler.FULLSET:
        run_fn = run_fullset
    elif evaluator_config.sampler is EvaluationSampler.UNIFORM_WINDOW:

        def run_fn(
            store,
            realization_policy,
            decoded_result,
            sample_indices,
        ):
            return run_uniform_window(
                store,
                realization_policy,
                decoded_result,
                sample_indices,
                config=evaluator_config,
            )

    elif evaluator_config.sampler is EvaluationSampler.POISSON_ARRIVALS:

        def run_fn(
            store,
            realization_policy,
            decoded_result,
            sample_indices,
        ):
            return run_poisson_arrivals(
                store,
                realization_policy,
                decoded_result,
                sample_indices,
                config=evaluator_config,
            )

    else:
        raise ValueError("replay evaluator requires evaluation.sampler")
    resolved_run_fn: RunEvaluatorFn = run_fn
    return CompiledEvaluatorContract(
        evaluation_id=evaluator_config.id,
        metric_descriptors=REPLAY_METRIC_DESCRIPTORS,
        primary_metric_id="profit_over_baseline",
        direction="maximize",
        config_payload=evaluator_config.model_dump(mode="json", exclude_none=True),
        accepted_decoded_result_id=DecodedOffsets.decoded_result_id,
        run_fn=resolved_run_fn,
    )
