"""Paper family output contract."""

from __future__ import annotations

import torch

from ...base import PredictionHeadSpec, PredictionOutputSpec

OFFSET_LOGITS_HEAD_ID = "min_block_offset_logits"
MIN_LOG_FEE_HEAD_ID = "min_block_log_fee"


def build_output_spec(max_candidate_slots: int) -> PredictionOutputSpec:
    if max_candidate_slots <= 0:
        raise ValueError("max_candidate_slots must be positive")
    return PredictionOutputSpec(
        heads=(
            PredictionHeadSpec(id=OFFSET_LOGITS_HEAD_ID, size=max_candidate_slots),
            PredictionHeadSpec(id=MIN_LOG_FEE_HEAD_ID, size=1),
        )
    )


def masked_offset_logits(logits: torch.Tensor, candidate_mask: torch.Tensor) -> torch.Tensor:
    return logits.masked_fill(~candidate_mask, torch.finfo(logits.dtype).min)
