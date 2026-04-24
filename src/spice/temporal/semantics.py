"""Explicit temporal geometry semantics shared by compilers, stores, and realization."""

from __future__ import annotations

from enum import StrEnum


class BaselineRowMode(StrEnum):
    FIRST_CANDIDATE = "first_candidate"
