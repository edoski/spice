"""Dataset-preparation seam types."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

import polars as pl
from pydantic import Field, field_validator, model_validator

from ...core.config_model import ConfigModel
from ...core.specs import (
    coerce_spec_config,
    coerce_spec_payload,
    lookup_local_spec,
    require_spec_config_from_table,
)
from ...core.validation import validate_path_segment
from ...semantics import DatasetBuilderSemantics
from .preparation import (
    ArtifactInferenceDatasetPreparationContext,
    ArtifactInferenceDatasetPreparationFacts,
    CompiledInferenceDatasetPreparationRequest,
    PreparedInferenceDataset,
    PreparedTrainingDataset,
    TrainingDatasetPreparationContext,
    TrainingDatasetPreparationFacts,
)


class DatasetBuilderConfig(ConfigModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return validate_path_segment(value, label="dataset_builder.id")


class FixedSequenceTemporalDatasetBuilderConfig(DatasetBuilderConfig):
    id: str = "fixed_sequence_temporal"
    min_sequence_length: int = Field(default=64, gt=0)
    max_sequence_length: int = Field(default=4096, gt=0)

    @field_validator("id")
    @classmethod
    def validate_fixed_sequence_temporal_id(cls, value: str) -> str:
        value = DatasetBuilderConfig.validate_id(value)
        if value != "fixed_sequence_temporal":
            raise ValueError("dataset_builder.id must be fixed_sequence_temporal")
        return value

    @model_validator(mode="after")
    def validate_sequence_bounds(self) -> FixedSequenceTemporalDatasetBuilderConfig:
        if self.max_sequence_length < self.min_sequence_length:
            raise ValueError("max_sequence_length must be >= min_sequence_length")
        return self


class BuilderRuntimeMetadata(ConfigModel):
    pass


class FixedSequenceTemporalBuilderRuntimeMetadata(BuilderRuntimeMetadata):
    sequence_length: int = Field(gt=0)
    median_dt_seconds: float = Field(gt=0.0)
    min_sequence_length: int = Field(gt=0)
    max_sequence_length: int = Field(gt=0)
    split_strategy: Literal["global_feature_table"] = "global_feature_table"

    @model_validator(mode="after")
    def validate_sequence_bounds(self) -> FixedSequenceTemporalBuilderRuntimeMetadata:
        if self.max_sequence_length < self.min_sequence_length:
            raise ValueError("max_sequence_length must be >= min_sequence_length")
        return self


PrepareTrainingFn = Callable[
    [pl.DataFrame, TrainingDatasetPreparationFacts, TrainingDatasetPreparationContext],
    PreparedTrainingDataset,
]
PrepareInferenceFn = Callable[
    [pl.DataFrame, pl.DataFrame, CompiledInferenceDatasetPreparationRequest],
    PreparedInferenceDataset,
]


@dataclass(frozen=True, slots=True)
class CompiledDatasetBuilderContract:
    dataset_builder_id: str
    prepare_training_fn: PrepareTrainingFn
    prepare_inference_fn: PrepareInferenceFn

    @property
    def semantics(self) -> DatasetBuilderSemantics:
        return DatasetBuilderSemantics(dataset_builder_id=self.dataset_builder_id)

    def prepare_training_dataset(
        self,
        blocks: pl.DataFrame,
        *,
        facts: TrainingDatasetPreparationFacts,
        context: TrainingDatasetPreparationContext,
    ) -> PreparedTrainingDataset:
        return self.prepare_training_fn(blocks, facts, context)

    def prepare_inference_dataset(
        self,
        history_blocks: pl.DataFrame,
        evaluation_blocks: pl.DataFrame,
        *,
        facts: ArtifactInferenceDatasetPreparationFacts,
        context: ArtifactInferenceDatasetPreparationContext,
    ) -> PreparedInferenceDataset:
        builder_runtime_metadata = coerce_builder_runtime_metadata(
            self.dataset_builder_id,
            context.builder_runtime_metadata,
        )
        return self.prepare_inference_fn(
            history_blocks,
            evaluation_blocks,
            CompiledInferenceDatasetPreparationRequest(
                feature_contract=context.feature_contract,
                problem_contract=context.problem_contract,
                delay_seconds=facts.delay_seconds,
                builder_runtime_metadata=builder_runtime_metadata,
                scaler=context.scaler,
                temporal_capability=context.temporal_capability,
                window_start_timestamp=facts.evaluation_window.start_timestamp,
                window_end_timestamp=facts.evaluation_window.exclusive_end_timestamp,
            ),
        )


def _compile_fixed_sequence_temporal(
    config: FixedSequenceTemporalDatasetBuilderConfig,
) -> CompiledDatasetBuilderContract:
    from .fixed_sequence_temporal import compile_dataset_builder

    return compile_dataset_builder(config)


@dataclass(frozen=True, slots=True)
class DatasetBuilderSpec:
    config_type: type[DatasetBuilderConfig]
    runtime_metadata_type: type[BuilderRuntimeMetadata]
    compile_contract: Callable[[Any], CompiledDatasetBuilderContract]


_DATASET_BUILDER_SPECS: dict[str, DatasetBuilderSpec] = {
    "fixed_sequence_temporal": DatasetBuilderSpec(
        config_type=FixedSequenceTemporalDatasetBuilderConfig,
        runtime_metadata_type=FixedSequenceTemporalBuilderRuntimeMetadata,
        compile_contract=_compile_fixed_sequence_temporal,
    ),
}


def dataset_builder_spec(builder_id: str) -> DatasetBuilderSpec:
    return lookup_local_spec(_DATASET_BUILDER_SPECS, builder_id, "dataset_builder.id")


def fixed_sequence_temporal_runtime_metadata(
    *,
    sequence_length: int,
    median_dt_seconds: float,
    min_sequence_length: int,
    max_sequence_length: int,
) -> FixedSequenceTemporalBuilderRuntimeMetadata:
    return FixedSequenceTemporalBuilderRuntimeMetadata(
        sequence_length=sequence_length,
        median_dt_seconds=median_dt_seconds,
        min_sequence_length=min_sequence_length,
        max_sequence_length=max_sequence_length,
    )


def validate_feature_prerequisites(
    actual,
    expected,
) -> None:
    if actual != expected:
        raise ValueError(
            "Resolved feature prerequisites do not match the current feature graph: "
            f"expected {expected.model_dump(mode='json')}, "
            f"got {actual.model_dump(mode='json')}"
        )


def coerce_builder_runtime_metadata(
    builder_id: str,
    payload: object,
) -> BuilderRuntimeMetadata:
    spec = dataset_builder_spec(builder_id)
    return coerce_spec_payload(
        payload,
        owner="builder runtime metadata",
        base_payload_type=BuilderRuntimeMetadata,
        spec=spec,
        spec_payload_type=lambda entry: entry.runtime_metadata_type,
    )


def coerce_dataset_builder_config(
    payload: object,
) -> DatasetBuilderConfig:
    return coerce_spec_config(
        payload,
        owner="dataset_builder",
        base_config_type=DatasetBuilderConfig,
        id_label="dataset_builder.id",
        lookup_spec=dataset_builder_spec,
        spec_config_type=lambda spec: spec.config_type,
    )


def compile_dataset_builder_contract(
    config: DatasetBuilderConfig,
) -> CompiledDatasetBuilderContract:
    spec = dataset_builder_spec(config.id)
    concrete_config = require_spec_config_from_table(
        config,
        config_id=config.id,
        lookup_spec=dataset_builder_spec,
        spec_config_type=lambda entry: entry.config_type,
        label="dataset builder config",
    )
    return spec.compile_contract(concrete_config)
