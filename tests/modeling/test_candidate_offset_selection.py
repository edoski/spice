from __future__ import annotations

import math

import torch

from spice.config import PredictionConfig
from spice.modeling.models import ModelOutputs
from spice.prediction import ActionSpaceDecodeContext, DecodedOffsets, compile_prediction_contract
from spice.prediction.families.candidate_offset_selection.batch import CandidateSlateTargetBatch
from spice.prediction.families.candidate_offset_selection.loss import compute_selection_loss
from spice.prediction.families.candidate_offset_selection.outputs import CANDIDATE_LOGITS_HEAD_ID


def _prediction_contract():
    prediction = PredictionConfig.model_validate(
        {
            "id": "candidate_offset_selection",
            "family_id": "candidate_offset_selection",
        }
    )
    return compile_prediction_contract(
        prediction_id=prediction.id,
        family_id=prediction.family_id,
    )


def test_selection_loss_prefers_cheaper_candidates_and_ignores_masked_slots() -> None:
    candidate_log_fees = torch.tensor(
        [[math.log(10.0), math.log(5.0), math.log(1000.0)]],
        dtype=torch.float32,
    )
    candidate_mask = torch.tensor([[True, True, False]])
    logits_bad = torch.tensor([[4.0, -4.0, 100.0]], dtype=torch.float32)
    logits_good = torch.tensor([[-4.0, 4.0, 100.0]], dtype=torch.float32)

    targets = CandidateSlateTargetBatch(
        candidate_log_fees=candidate_log_fees,
        candidate_mask=candidate_mask,
        optimum_offsets=torch.tensor([1], dtype=torch.int64),
        optimum_log_fees=torch.tensor([math.log(5.0)], dtype=torch.float32),
        baseline_candidate_indices=torch.tensor([0], dtype=torch.int64),
    )

    bad_loss = compute_selection_loss(logits_bad, targets)
    good_loss = compute_selection_loss(logits_good, targets)

    assert good_loss.item() < bad_loss.item()


def test_candidate_offset_decode_ignores_masked_slots() -> None:
    contract = _prediction_contract()
    predictions = contract.allocate_decoded_result(1)
    assert isinstance(predictions, DecodedOffsets)
    outputs = ModelOutputs(
        heads={
            CANDIDATE_LOGITS_HEAD_ID: torch.tensor([[4.0, -4.0, 100.0]], dtype=torch.float32)
        }
    )

    contract.decode_batch_result_into(
        predictions,
        outputs,
        ActionSpaceDecodeContext(
            sample_positions=torch.tensor([0], dtype=torch.int64),
            action_mask=torch.tensor([[True, True, False]], dtype=torch.bool),
        ),
    )

    assert torch.equal(predictions.tensor, torch.tensor([0], dtype=torch.int64))
