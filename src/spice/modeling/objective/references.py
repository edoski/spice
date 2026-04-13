"""Objective reference derivation from candidate fee slates."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch


@dataclass(frozen=True, slots=True)
class CandidateReferenceTensors:
    masked_logits: torch.Tensor
    predicted_candidate_index: torch.Tensor
    optimal_candidate_index: torch.Tensor
    realized_log_fee: torch.Tensor
    baseline_log_fee: torch.Tensor
    optimal_log_fee: torch.Tensor


@dataclass(frozen=True, slots=True)
class CandidateReferenceArrays:
    predicted_candidate_index: np.ndarray
    optimal_candidate_index: np.ndarray
    realized_log_fee: np.ndarray
    baseline_log_fee: np.ndarray
    optimal_log_fee: np.ndarray


def masked_candidate_logits(logits: torch.Tensor, candidate_mask: torch.Tensor) -> torch.Tensor:
    return logits.masked_fill(~candidate_mask, torch.finfo(logits.dtype).min)


def candidate_reference_tensors(
    logits: torch.Tensor,
    candidate_log_fees: torch.Tensor,
    candidate_mask: torch.Tensor,
) -> CandidateReferenceTensors:
    masked_logits = masked_candidate_logits(logits, candidate_mask)
    masked_candidate_fees = candidate_log_fees.masked_fill(
        ~candidate_mask,
        torch.finfo(candidate_log_fees.dtype).max,
    )
    predicted_candidate_index = masked_logits.argmax(dim=-1)
    optimal_candidate_index = masked_candidate_fees.argmin(dim=-1)
    realized_log_fee = candidate_log_fees.gather(
        dim=1,
        index=predicted_candidate_index.unsqueeze(-1),
    ).squeeze(-1)
    baseline_log_fee = candidate_log_fees[:, 0]
    optimal_log_fee = masked_candidate_fees.gather(
        dim=1,
        index=optimal_candidate_index.unsqueeze(-1),
    ).squeeze(-1)
    return CandidateReferenceTensors(
        masked_logits=masked_logits,
        predicted_candidate_index=predicted_candidate_index,
        optimal_candidate_index=optimal_candidate_index,
        realized_log_fee=realized_log_fee,
        baseline_log_fee=baseline_log_fee,
        optimal_log_fee=optimal_log_fee,
    )


def candidate_reference_arrays(
    candidate_log_fees: np.ndarray,
    candidate_mask: np.ndarray,
    predicted_candidate_index: np.ndarray,
) -> CandidateReferenceArrays:
    masked_candidate_fees = np.where(candidate_mask, candidate_log_fees, np.inf)
    optimal_candidate_index = masked_candidate_fees.argmin(axis=-1).astype(np.int64, copy=False)
    row_indices = np.arange(candidate_log_fees.shape[0], dtype=np.int64)
    realized_log_fee = candidate_log_fees[row_indices, predicted_candidate_index]
    baseline_log_fee = candidate_log_fees[:, 0]
    optimal_log_fee = masked_candidate_fees[row_indices, optimal_candidate_index]
    return CandidateReferenceArrays(
        predicted_candidate_index=predicted_candidate_index.astype(np.int64, copy=False),
        optimal_candidate_index=optimal_candidate_index,
        realized_log_fee=realized_log_fee.astype(np.float32, copy=False),
        baseline_log_fee=baseline_log_fee.astype(np.float32, copy=False),
        optimal_log_fee=optimal_log_fee.astype(np.float32, copy=False),
    )
