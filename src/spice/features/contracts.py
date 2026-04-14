"""Compiled feature contracts shared across workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import polars as pl

from .engine import (
    FeatureSelection,
    ResolvedFeatureTable,
    build_feature_table,
    feature_graph_fingerprint,
    make_feature_selection,
    resolve_feature_prerequisites,
)
from .families import FeatureFamilyConfig, FeaturePrerequisites, feature_family_spec

if TYPE_CHECKING:
    from ..config.models import FeatureSetConfig


@dataclass(frozen=True, slots=True)
class CompiledFeatureContract:
    feature_set_id: str
    feature_family_id: str
    feature_names: tuple[str, ...]
    feature_graph_fingerprint: str
    feature_prerequisites: FeaturePrerequisites

    @property
    def selection(self) -> FeatureSelection:
        return FeatureSelection(
            feature_set_id=self.feature_set_id,
            feature_family_id=self.feature_family_id,
            feature_names=self.feature_names,
        )

    def build_table(self, blocks: pl.DataFrame) -> ResolvedFeatureTable:
        return build_feature_table(blocks, selection=self.selection)


def compile_feature_contract(*, feature_set: FeatureSetConfig) -> CompiledFeatureContract:
    family_spec = feature_family_spec(feature_set.family.id)
    return family_spec.compile_contract(
        feature_set.id,
        feature_set.family,
        tuple(feature_set.outputs),
    )


def compile_feature_contract_for_family(
    feature_set_id: str,
    family_config: FeatureFamilyConfig,
    feature_names: tuple[str, ...],
) -> CompiledFeatureContract:
    selection = make_feature_selection(
        feature_set_id=feature_set_id,
        feature_family_id=family_config.id,
        feature_names=feature_names,
    )
    return CompiledFeatureContract(
        feature_set_id=selection.feature_set_id,
        feature_family_id=selection.feature_family_id,
        feature_names=selection.feature_names,
        feature_graph_fingerprint=feature_graph_fingerprint(
            selection.feature_family_id,
            selection.feature_names,
        ),
        feature_prerequisites=resolve_feature_prerequisites(
            selection.feature_family_id,
            selection.feature_names,
        ),
    )
