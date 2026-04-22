"""Explicit temporal geometry semantics shared by compilers, stores, and realization."""

from __future__ import annotations

from enum import StrEnum


class CandidateStartMode(StrEnum):
    NEXT_BLOCK = "next_block"
    CURRENT_ROW = "current_row"


class ActionSpaceMode(StrEnum):
    FIXED_EX_ANTE = "fixed_ex_ante"
    REALIZED_PER_SAMPLE = "realized_per_sample"


class BaselineRowMode(StrEnum):
    FIRST_CANDIDATE = "first_candidate"
