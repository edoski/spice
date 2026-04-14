"""Open registry for prediction-family specs."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, cast

from ..core.components import ComponentCatalog
from .base import PredictionFamilyConfig
from .contracts import CompiledPredictionContract

PredictionFamilyConfigT = TypeVar("PredictionFamilyConfigT", bound=PredictionFamilyConfig)


@dataclass(frozen=True, slots=True)
class PredictionFamilySpec(Generic[PredictionFamilyConfigT]):
    id: str
    config_type: type[PredictionFamilyConfigT]
    compile: Callable[[str, PredictionFamilyConfigT], CompiledPredictionContract]


_PREDICTION_FAMILY_SPECS = ComponentCatalog[PredictionFamilySpec[Any]](
    kind_label="prediction family",
    entry_point_group="spice.prediction_families",
)


def register_prediction_family_spec(spec: PredictionFamilySpec[Any]) -> None:
    _PREDICTION_FAMILY_SPECS.register(spec.id, spec)


def _load_builtin_prediction_families() -> None:
    from .families import candidate_offset_selection, min_block_fee_multitask  # noqa: F401


_PREDICTION_FAMILY_SPECS.configure_builtin_loader(_load_builtin_prediction_families)


def prediction_family_spec(family_id: str) -> PredictionFamilySpec[Any]:
    try:
        return _PREDICTION_FAMILY_SPECS.get(family_id)
    except ValueError as exc:
        raise ValueError(str(exc).replace("prediction family", "prediction.family.id")) from exc


def coerce_prediction_family_config(
    raw_config: Mapping[str, object] | PredictionFamilyConfig,
) -> PredictionFamilyConfig:
    if isinstance(raw_config, PredictionFamilyConfig):
        family_id = raw_config.id
        payload = raw_config.model_dump(mode="json")
    elif isinstance(raw_config, Mapping):
        if "id" not in raw_config:
            raise ValueError("prediction.family.id is required")
        family_id = str(raw_config["id"])
        payload = dict(raw_config)
    else:
        raise TypeError("prediction.family must be a mapping")
    return prediction_family_spec(family_id).config_type.model_validate(payload)


def compile_prediction_contract(
    *,
    prediction_id: str,
    family_config: PredictionFamilyConfig,
) -> CompiledPredictionContract:
    spec = prediction_family_spec(family_config.id)
    return spec.compile(prediction_id, cast(Any, family_config))
