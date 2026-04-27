"""Candidate-offset selection prediction family."""

from __future__ import annotations

import torch

from ....modeling.models import ModelOutputs
from ....temporal.execution_policy import CompiledExecutionPolicyContract
from ....temporal.problem_store import CompiledProblemStore
from ...contracts import (
    ActionSpaceDecodeContext,
    CompiledPredictionContract,
    DecodedOffsets,
    DecodedPredictionResult,
    IntVector,
    PredictionTargetBatch,
    PreparedPredictionTargets,
    masked_offset_argmax,
)
from .batch import CandidateSlateTargetBatch, materialize_candidate_slate_targets
from .metrics import (
    TRAINING_METRIC_DESCRIPTORS,
    compute_batch_loss_and_state,
    create_epoch_accumulator,
)
from .outputs import (
    CANDIDATE_LOGITS_HEAD_ID,
    build_output_spec,
    candidate_logits,
)


def _prepare_targets(
    store: CompiledProblemStore,
    sample_indices: IntVector,
    execution_policy: CompiledExecutionPolicyContract,
) -> PreparedPredictionTargets:
    return materialize_candidate_slate_targets(
        store,
        sample_indices,
        execution_policy=execution_policy,
    )


def _compute_batch_loss_and_state(
    outputs: ModelOutputs,
    targets: PredictionTargetBatch,
    training_state: object | None,
) -> tuple[torch.Tensor, object]:
    del training_state
    if not isinstance(targets, CandidateSlateTargetBatch):
        raise TypeError("candidate_offset_selection expects CandidateSlateTargetBatch targets")
    return compute_batch_loss_and_state(outputs.head(CANDIDATE_LOGITS_HEAD_ID), targets)


def _create_epoch_accumulator():
    return create_epoch_accumulator()


def _decode_candidate_offsets_into(
    predictions: DecodedPredictionResult,
    outputs: ModelOutputs,
    decode_context: ActionSpaceDecodeContext,
) -> None:
    if not isinstance(predictions, DecodedOffsets):
        raise TypeError("candidate_offset_selection decodes candidate offsets")
    predictions.write(
        decode_context.sample_positions,
        masked_offset_argmax(candidate_logits(outputs), decode_context.action_mask),
    )


def compile_prediction_family(
    prediction_id: str,
) -> CompiledPredictionContract:
    return CompiledPredictionContract(
        prediction_id=prediction_id,
        prediction_family_id="candidate_offset_selection",
        training_metric_descriptors=TRAINING_METRIC_DESCRIPTORS,
        primary_metric_id="profit_over_baseline",
        direction="maximize",
        build_output_spec_fn=build_output_spec,
        prepare_targets_fn=_prepare_targets,
        compute_batch_loss_and_state_fn=_compute_batch_loss_and_state,
        create_epoch_accumulator_fn=_create_epoch_accumulator,
        decoded_result_id=DecodedOffsets.decoded_result_id,
        allocate_decoded_result_fn=DecodedOffsets.allocate,
        decode_batch_result_into_fn=_decode_candidate_offsets_into,
    )
