"""Core feature source/spec execution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
import polars as pl
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field

FloatVector = NDArray[np.float64]
LogFeeVector = NDArray[np.float32]
IntVector = NDArray[np.int64]


class FeatureConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class FeaturePrerequisites(FeatureConfigModel):
    history_seconds: int = Field(default=0, ge=0)
    warmup_rows: int = Field(default=0, ge=0)


@dataclass(slots=True, frozen=True)
class CanonicalBlockSeries:
    block_numbers: IntVector
    timestamps: IntVector
    log_base_fees: LogFeeVector


class ComputeSourceFn(Protocol):
    def __call__(self, blocks: pl.DataFrame) -> FloatVector: ...


class ComputeFeatureFn(Protocol):
    def __call__(
        self,
        blocks: pl.DataFrame,
        series: CanonicalBlockSeries,
        sources: Mapping[str, FloatVector],
        features: Mapping[str, FloatVector],
    ) -> FloatVector: ...


@dataclass(frozen=True, slots=True)
class SourceSpec:
    """Available model-time source with explicit lag and null policy."""

    source_columns: tuple[str, ...]
    warmup_rows: int
    required_after_warmup: bool
    compute: ComputeSourceFn
    optional_enrichments: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    """Formula over source/spec dependencies."""

    source_dependencies: tuple[str, ...]
    feature_dependencies: tuple[str, ...]
    history_seconds: int
    warmup_rows: int
    compute: ComputeFeatureFn


@dataclass(frozen=True, slots=True)
class FeatureCatalog:
    sources: dict[str, SourceSpec]
    features: dict[str, FeatureSpec]
    allowed_outputs: tuple[str, ...]
    fingerprint_sources: tuple[Path, ...]


def validate_feature_names(
    features_id: str,
    feature_names: tuple[str, ...],
    *,
    known_feature_names: tuple[str, ...],
) -> None:
    if not features_id:
        raise ValueError("features.id must be non-empty")
    if not feature_names:
        raise ValueError("features.outputs must not be empty")
    duplicates = [name for name in dict.fromkeys(feature_names) if feature_names.count(name) > 1]
    if duplicates:
        raise ValueError("features.outputs must not contain duplicates: " + ", ".join(duplicates))
    unknown = [name for name in feature_names if name not in known_feature_names]
    if unknown:
        raise ValueError("Unknown feature outputs: " + ", ".join(unknown))
