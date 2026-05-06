# pyright: strict

"""Context-free typed loading for named config groups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar, cast

from ..evaluation import EvaluatorConfig
from ..execution.models import ExecutionSpec
from ..modeling.dataset_builders import DatasetBuilderConfig
from ..modeling.families.base import ModelConfig
from ..objectives import ObjectiveConfig
from .group_catalog import ConfigGroup, validate_named_group_payload
from .groups import load_named_group_document
from .models import (
    ChainSpec,
    DatasetSpec,
    FeaturesConfig,
    PredictionConfig,
    ProblemSpec,
    ProviderSpec,
    SplitConfig,
    TrainingConfig,
    TuningConfig,
)
from .surfaces import SurfaceFrame

ConfigT = TypeVar("ConfigT")


@dataclass(frozen=True, slots=True)
class TypedGroup(Generic[ConfigT]):
    group: ConfigGroup


CHAIN = TypedGroup[ChainSpec](ConfigGroup.CHAIN)
DATASET = TypedGroup[DatasetSpec](ConfigGroup.DATASET)
DATASET_BUILDER = TypedGroup[DatasetBuilderConfig](ConfigGroup.DATASET_BUILDER)
EVALUATION = TypedGroup[EvaluatorConfig](ConfigGroup.EVALUATION)
EXECUTION = TypedGroup[ExecutionSpec](ConfigGroup.EXECUTION)
FEATURES = TypedGroup[FeaturesConfig](ConfigGroup.FEATURES)
MODEL = TypedGroup[ModelConfig[str]](ConfigGroup.MODEL)
OBJECTIVE = TypedGroup[ObjectiveConfig](ConfigGroup.OBJECTIVE)
PREDICTION = TypedGroup[PredictionConfig](ConfigGroup.PREDICTION)
PROBLEM = TypedGroup[ProblemSpec](ConfigGroup.PROBLEM)
PROVIDER = TypedGroup[ProviderSpec](ConfigGroup.PROVIDER)
SPLIT = TypedGroup[SplitConfig](ConfigGroup.SPLIT)
SURFACE = TypedGroup[SurfaceFrame](ConfigGroup.SURFACE)
TRAINING = TypedGroup[TrainingConfig](ConfigGroup.TRAINING)
TUNING = TypedGroup[TuningConfig](ConfigGroup.TUNING)


def load(spec: TypedGroup[ConfigT], name: str) -> ConfigT:
    payload = load_named_group_document(name, spec.group)
    return cast(
        ConfigT,
        validate_named_group_payload(spec.group, name=name, payload=payload),
    )
