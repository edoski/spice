"""Candidate-offset selection family config."""

from __future__ import annotations

from typing import Literal

from ...base import PredictionFamilyConfig


class CandidateOffsetSelectionFamilyConfig(PredictionFamilyConfig):
    id: Literal["candidate_offset_selection"] = "candidate_offset_selection"
