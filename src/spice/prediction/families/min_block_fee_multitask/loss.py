"""Paper-family multitask loss."""

from __future__ import annotations

import torch
import torch.nn.functional as F

from .batch import MinBlockFeeTargetBatch, MinBlockFeeTrainingState
from .outputs import masked_offset_logits


def compute_multitask_loss(
    offset_logits: torch.Tensor,
    fee_predictions: torch.Tensor,
    targets: MinBlockFeeTargetBatch,
    *,
    training_state: MinBlockFeeTrainingState,
    classification_loss_weight: float,
    regression_loss_weight: float,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    masked_logits = masked_offset_logits(offset_logits, targets.candidate_mask)
    class_weights = training_state.class_weights.to(
        device=masked_logits.device,
        dtype=masked_logits.dtype,
    )
    classification_loss = F.cross_entropy(
        masked_logits,
        targets.min_block_offsets,
        weight=class_weights,
    )
    regression_loss = F.smooth_l1_loss(
        fee_predictions,
        targets.min_block_log_fees,
    )
    total_loss = (
        classification_loss_weight * classification_loss
        + regression_loss_weight * regression_loss
    )
    return total_loss, classification_loss, regression_loss
