"""Family-aware Hamilton feature graph helpers."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from functools import cache
from hashlib import sha256
from typing import Any, cast

import numpy as np
import polars as pl
from hamilton import driver
from hamilton.graph_types import HamiltonNode
from numpy.typing import NDArray

from .families import (
    FEATURE_KIND_TAG,
    FEATURE_KIND_VALUE,
    FeaturePrerequisites,
    feature_family_spec,
)

FloatMatrix = NDArray[np.float32]
FloatVector = NDArray[np.float32]
IntVector = NDArray[np.int64]


@dataclass(slots=True, frozen=True)
class FeatureSelection:
    feature_set_id: str
    feature_family_id: str
    feature_names: tuple[str, ...]


def make_feature_selection(
    *,
    feature_set_id: str,
    feature_family_id: str,
    feature_names: tuple[str, ...],
) -> FeatureSelection:
    selection = FeatureSelection(
        feature_set_id=feature_set_id,
        feature_family_id=feature_family_id,
        feature_names=feature_names,
    )
    validate_feature_selection(
        selection.feature_set_id,
        selection.feature_family_id,
        selection.feature_names,
    )
    return selection


@dataclass(slots=True)
class CanonicalBlockSeries:
    block_numbers: IntVector
    timestamps: IntVector
    log_base_fees: FloatVector


@dataclass(slots=True)
class ResolvedFeatureTable:
    feature_set_id: str
    feature_family_id: str
    feature_names: tuple[str, ...]
    feature_graph_fingerprint: str
    feature_prerequisites: FeaturePrerequisites
    series: CanonicalBlockSeries
    feature_matrix: FloatMatrix


@cache
def build_feature_driver(feature_family_id: str) -> driver.Driver:
    return driver.Builder().with_modules(*feature_family_spec(feature_family_id).modules).build()


@cache
def _node_map(feature_family_id: str) -> dict[str, HamiltonNode]:
    return {
        node.name: node
        for node in build_feature_driver(feature_family_id).list_available_variables()
    }


@cache
def feature_node_map(feature_family_id: str) -> dict[str, HamiltonNode]:
    return {
        name: node
        for name, node in _node_map(feature_family_id).items()
        if node.tags.get(FEATURE_KIND_TAG) == FEATURE_KIND_VALUE
    }


def validate_feature_selection(
    feature_set_id: str,
    feature_family_id: str,
    feature_names: tuple[str, ...],
) -> None:
    if not feature_set_id:
        raise ValueError("feature_set.id must be non-empty")
    feature_family_spec(feature_family_id)
    if not feature_names:
        raise ValueError("feature_set.outputs must not be empty")
    duplicates = [name for name in dict.fromkeys(feature_names) if feature_names.count(name) > 1]
    if duplicates:
        raise ValueError(
            "feature_set.outputs must not contain duplicates: " + ", ".join(duplicates)
        )
    family_nodes = feature_node_map(feature_family_id)
    unknown = [name for name in feature_names if name not in family_nodes]
    if unknown:
        raise ValueError(
            f"Unknown feature outputs for family {feature_family_id}: " + ", ".join(unknown)
        )


def resolve_feature_prerequisites(
    feature_family_id: str,
    feature_names: tuple[str, ...],
) -> FeaturePrerequisites:
    validate_feature_selection("validated", feature_family_id, feature_names)
    family_nodes = feature_node_map(feature_family_id)
    return feature_family_spec(feature_family_id).resolve_prerequisites(feature_names, family_nodes)


def _dependency_closure(
    feature_family_id: str,
    feature_names: tuple[str, ...],
) -> list[HamiltonNode]:
    nodes = _node_map(feature_family_id)
    stack = list(feature_names)
    visited: set[str] = set()
    ordered: list[HamiltonNode] = []
    while stack:
        name = stack.pop()
        if name in visited:
            continue
        visited.add(name)
        node = nodes[name]
        ordered.append(node)
        stack.extend(sorted(node.required_dependencies))
        stack.extend(sorted(node.optional_dependencies))
    return sorted(ordered, key=lambda item: item.name)


def feature_graph_fingerprint(
    feature_family_id: str,
    feature_names: tuple[str, ...],
) -> str:
    validate_feature_selection("validated", feature_family_id, feature_names)
    digest = sha256()
    digest.update(feature_family_id.encode("utf-8"))
    digest.update(b"\0")
    for name in feature_names:
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
    for node in _dependency_closure(feature_family_id, feature_names):
        digest.update(node.name.encode("utf-8"))
        digest.update(b"\0")
        if node.is_external_input:
            continue
        for function in node.originating_functions or ():
            digest.update(function.__module__.encode("utf-8"))
            digest.update(b"\0")
            digest.update(function.__qualname__.encode("utf-8"))
            digest.update(b"\0")
            digest.update(inspect.getsource(function).encode("utf-8"))
            digest.update(b"\0")
    return digest.hexdigest()


def build_feature_table(
    blocks: pl.DataFrame,
    *,
    selection: FeatureSelection,
) -> ResolvedFeatureTable:
    validate_feature_selection(
        selection.feature_set_id,
        selection.feature_family_id,
        selection.feature_names,
    )
    feature_prerequisites = resolve_feature_prerequisites(
        selection.feature_family_id,
        selection.feature_names,
    )
    graph_fingerprint = feature_graph_fingerprint(
        selection.feature_family_id,
        selection.feature_names,
    )
    final_vars = cast(
        Any,
        [*selection.feature_names, "block_numbers", "timestamps", "log_base_fee"],
    )
    result = build_feature_driver(selection.feature_family_id).execute(
        final_vars,
        inputs={
            "blocks": blocks,
        },
    )
    block_numbers = np.asarray(result["block_numbers"], dtype=np.int64)
    timestamps = np.asarray(result["timestamps"], dtype=np.int64)
    log_base_fees = np.asarray(result["log_base_fee"], dtype=np.float32)
    raw_feature_columns = [
        np.asarray(result[feature_name], dtype=np.float64)
        for feature_name in selection.feature_names
    ]
    if raw_feature_columns:
        feature_matrix = np.column_stack(raw_feature_columns).astype(np.float32, copy=False)
    else:  # pragma: no cover
        feature_matrix = np.empty((timestamps.shape[0], 0), dtype=np.float32)
    return ResolvedFeatureTable(
        feature_set_id=selection.feature_set_id,
        feature_family_id=selection.feature_family_id,
        feature_names=selection.feature_names,
        feature_graph_fingerprint=graph_fingerprint,
        feature_prerequisites=feature_prerequisites,
        series=CanonicalBlockSeries(
            block_numbers=block_numbers.astype(np.int64, copy=False),
            timestamps=timestamps.astype(np.int64, copy=False),
            log_base_fees=log_base_fees.astype(np.float32, copy=False),
        ),
        feature_matrix=feature_matrix.astype(np.float32, copy=False),
    )
