"""Candidate-offset selection family config."""

from __future__ import annotations

from ...base import PredictionFamilyConfig


class CandidateOffsetSelectionFamilyConfig(PredictionFamilyConfig):
    id: str = "candidate_offset_selection"
