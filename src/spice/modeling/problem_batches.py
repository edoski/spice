"""Shared same-problem batch contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

import torch


@dataclass(frozen=True, slots=True)
class CandidateChoiceTargets:
    candidate_log_fees: torch.Tensor
    candidate_mask: torch.Tensor


class TemporalProblemBatch(Protocol):
    @property
    def sample_positions(self) -> torch.Tensor: ...

    def to_device(self, device: torch.device) -> TemporalProblemBatch: ...

    def model_kwargs(self) -> Mapping[str, torch.Tensor]: ...

    def objective_targets(self) -> CandidateChoiceTargets: ...
