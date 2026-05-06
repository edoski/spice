"""Compiled feature contracts shared across workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import polars as pl

from ..semantics import FeatureSemantics
from .core import (
    FeatureCatalog,
    FeaturePrerequisites,
    ResolvedFeatureTable,
    _build_feature_table,
    _dependency_order,
    _feature_optional_enrichments,
    _feature_prerequisites,
    _feature_source_columns,
    _required_source_names,
    feature_graph_fingerprint,
    validate_feature_names,
)
from .registry import feature_entry

if TYPE_CHECKING:
    from ..config.models import FeaturesConfig


@dataclass(frozen=True, slots=True)
class CompiledFeatureContract:
    features_id: str
    feature_names: tuple[str, ...]
    ordered_feature_names: tuple[str, ...]
    required_source_names: tuple[str, ...]
    feature_graph_fingerprint: str
    feature_prerequisites: FeaturePrerequisites
    required_source_columns: frozenset[str]
    acquisition_enrichments: frozenset[str]
    _catalog: FeatureCatalog

    @property
    def semantics(self) -> FeatureSemantics:
        return FeatureSemantics(
            features_id=self.features_id,
            feature_names=self.feature_names,
            feature_graph_fingerprint=self.feature_graph_fingerprint,
            feature_prerequisites=self.feature_prerequisites,
        )

    def build_table(self, blocks: pl.DataFrame) -> ResolvedFeatureTable:
        return _build_feature_table(blocks, contract=self)


def compile_feature_contract(*, features: FeaturesConfig) -> CompiledFeatureContract:
    catalog = feature_entry(features.id)
    feature_names = tuple(features.outputs)
    validate_feature_names(
        features.id,
        feature_names,
        known_feature_names=catalog.allowed_outputs,
    )
    ordered_feature_names = _dependency_order(feature_names, catalog=catalog)
    required_source_names = _required_source_names(
        ordered_feature_names,
        catalog=catalog,
    )
    feature_prerequisites = _feature_prerequisites(
        ordered_feature_names,
        required_source_names=required_source_names,
        catalog=catalog,
    )
    return CompiledFeatureContract(
        features_id=features.id,
        feature_names=feature_names,
        ordered_feature_names=ordered_feature_names,
        required_source_names=required_source_names,
        feature_graph_fingerprint=feature_graph_fingerprint(
            features.id,
            feature_names,
            fingerprint_sources=catalog.fingerprint_sources,
        ),
        feature_prerequisites=feature_prerequisites,
        required_source_columns=_feature_source_columns(
            required_source_names,
            catalog=catalog,
        ),
        acquisition_enrichments=_feature_optional_enrichments(
            required_source_names,
            catalog=catalog,
        ),
        _catalog=catalog,
    )
