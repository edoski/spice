"""Dataset-builder registry."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from ...core.components import ComponentCatalog
from ...core.errors import ConfigResolutionError
from .base import (
    CompiledDatasetBuilderContract,
    DatasetBuilderConfig,
    DatasetBuilderSpec,
)

_DATASET_BUILDERS = ComponentCatalog[DatasetBuilderSpec[Any]](
    kind_label="dataset builder",
    entry_point_group="spice.dataset_builders",
)


def register_dataset_builder_spec(spec: DatasetBuilderSpec[Any]) -> None:
    _DATASET_BUILDERS.register(spec.id, spec)


def _load_builtin_dataset_builders() -> None:
    from . import paper_classification_temporal, standard_temporal  # noqa: F401


_DATASET_BUILDERS.configure_builtin_loader(_load_builtin_dataset_builders)


def dataset_builder_spec(builder_id: str) -> DatasetBuilderSpec[Any]:
    try:
        return _DATASET_BUILDERS.get(builder_id)
    except ConfigResolutionError as exc:
        raise ConfigResolutionError(
            str(exc).replace("dataset builder", "dataset_builder.id")
        ) from exc


def coerce_dataset_builder_config(
    payload: Mapping[str, object] | DatasetBuilderConfig,
) -> DatasetBuilderConfig:
    if isinstance(payload, DatasetBuilderConfig):
        raw_payload = payload.model_dump(mode="json")
        builder_id = payload.id
    else:
        raw_payload = dict(payload)
        builder_id = _mapping_builder_id(raw_payload)
    spec = dataset_builder_spec(builder_id)
    return spec.config_type.model_validate(raw_payload)


def compile_dataset_builder_contract(
    config: DatasetBuilderConfig,
) -> CompiledDatasetBuilderContract:
    return dataset_builder_spec(config.id).compile(config)


def _mapping_builder_id(payload: Mapping[str, object]) -> str:
    value = payload.get("id")
    if not isinstance(value, str):
        raise ConfigResolutionError("dataset_builder.id is required")
    return cast(str, value)
