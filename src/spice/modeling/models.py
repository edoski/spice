"""Generic temporal model contracts."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass

import torch
from torch import nn


@dataclass(frozen=True, slots=True)
class ModelOutputs:
    heads: dict[str, torch.Tensor]

    def head(self, head_id: str) -> torch.Tensor:
        try:
            return self.heads[head_id]
        except KeyError as exc:
            known = ", ".join(sorted(self.heads)) or "<none>"
            raise ValueError(f"Unknown output head: {head_id}. Known heads: {known}") from exc


class TemporalModel(nn.Module, ABC):
    """Base class for models that solve the temporal candidate-choice problem."""
