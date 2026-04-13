"""Differentiable training objective."""

from __future__ import annotations

import torch

from .references import masked_candidate_logits


def compute_objective_loss(
    logits: torch.Tensor,
    candidate_log_fees: torch.Tensor,
    candidate_mask: torch.Tensor,
) -> torch.Tensor:
    masked_logits = masked_candidate_logits(logits, candidate_mask)
    policy = torch.softmax(masked_logits, dim=-1)
    baseline_log_fee = candidate_log_fees[:, 0].unsqueeze(-1)
    relative_fee = torch.exp(candidate_log_fees - baseline_log_fee)
    return (policy * relative_fee).sum(dim=-1).mean()
