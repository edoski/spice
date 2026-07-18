"""Feature normalization utilities."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ScalerStats(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    means: list[float]
    scales: list[float]
