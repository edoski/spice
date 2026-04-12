"""Explicit runtime configuration models."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializeAsAny,
    field_validator,
    model_validator,
)

from ..features import validate_feature_selection


class ChainName(StrEnum):
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    AVALANCHE = "avalanche"


class RpcProviderName(StrEnum):
    DIRECT = "direct"
    ALCHEMY = "alchemy"
    PUBLICNODE = "publicnode"


class WorkflowTask(StrEnum):
    ACQUIRE = "acquire"
    TUNE = "tune"
    TRAIN = "train"
    SIMULATE = "simulate"


class StudyDirection(StrEnum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


class TuningObjective(StrEnum):
    VALIDATION_LOSS = "validation_loss"
    VALIDATION_ACCURACY = "validation_accuracy"
    VALIDATION_COST_OVER_OPTIMUM = "validation_cost_over_optimum"
    VALIDATION_PROFIT_OVER_BASELINE = "validation_profit_over_baseline"

    @property
    def metric_name(self) -> str:
        return self.value.removeprefix("validation_")


class TrainingPrecision(StrEnum):
    AUTO = "auto"
    FP32 = "fp32"
    FP16_MIXED = "fp16-mixed"
    BF16_MIXED = "bf16-mixed"


class CompileMode(StrEnum):
    AUTO = "auto"
    OFF = "off"
    ON = "on"


class ArtifactVariant(StrEnum):
    BASELINE = "baseline"
    TUNED = "tuned"


class ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def _validate_path_segment(value: str, *, label: str) -> str:
    if not value or "/" in value or "\\" in value:
        raise ValueError(f"{label} must be a non-empty path segment")
    return value


def _utc_midnight_timestamp(value: date) -> int:
    return int(datetime.combine(value, time.min, tzinfo=UTC).timestamp())


class ChainSpec(ConfigModel):
    name: ChainName
    chain_id: int = Field(gt=0)
    block_time_seconds: float = Field(gt=0)
    uses_poa_extra_data: bool


class DatasetTemporalSpec(ConfigModel):
    max_delay_seconds: int = Field(gt=0)
    lookback_seconds: int = Field(gt=0)


class DatasetSamplingSpec(ConfigModel):
    sample_count: int = Field(gt=0)


class DatasetSpec(ConfigModel):
    id: str
    evaluation_date: date
    temporal: DatasetTemporalSpec
    sampling: DatasetSamplingSpec
    history_context_blocks: int = Field(gt=0)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_path_segment(value, label="dataset.id")


class StorageSpec(ConfigModel):
    root: Path = Path("outputs")


class SplitConfig(ConfigModel):
    train_fraction: float = Field(gt=0.0, lt=1.0)
    validation_fraction: float = Field(ge=0.0, lt=1.0)

    @model_validator(mode="after")
    def validate_split(self) -> Self:
        if self.train_fraction + self.validation_fraction >= 1.0:
            raise ValueError("train_fraction + validation_fraction must be less than 1")
        return self


class EarlyStoppingConfig(ConfigModel):
    patience: int = Field(gt=0)
    min_delta: float = Field(ge=0.0)


class TrainingConfig(ConfigModel):
    learning_rate: float = Field(gt=0.0)
    weight_decay: float = Field(ge=0.0)
    batch_size: int = Field(gt=0)
    max_epochs: int = Field(gt=0)
    early_stopping: EarlyStoppingConfig
    gradient_clip_norm: float = Field(gt=0.0)
    action_loss_weight: float = Field(gt=0.0)
    fee_loss_weight: float = Field(gt=0.0)
    device: str
    seed: int = Field(ge=0)
    deterministic: bool
    log_every_n_steps: int = Field(gt=0)
    precision: TrainingPrecision
    compile: CompileMode


class AcquisitionConfig(ConfigModel):
    dry_run: bool = False
    history_sample_budget: int | None = Field(default=None, gt=0)
    chunk_size: int = Field(gt=0)
    rpc_batch_size: int = Field(gt=0)
    rpc_concurrency: int = Field(gt=0)
    rpc_min_batch_size: int = Field(gt=0)
    rpc_concurrency_rungs: list[int] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_rpc_runtime(self) -> Self:
        if self.rpc_min_batch_size > self.rpc_batch_size:
            raise ValueError("rpc_min_batch_size must be less than or equal to rpc_batch_size")
        if sorted(self.rpc_concurrency_rungs) != self.rpc_concurrency_rungs:
            raise ValueError("rpc_concurrency_rungs must be sorted in ascending order")
        if len(set(self.rpc_concurrency_rungs)) != len(self.rpc_concurrency_rungs):
            raise ValueError("rpc_concurrency_rungs must not contain duplicates")
        if any(value <= 0 for value in self.rpc_concurrency_rungs):
            raise ValueError("rpc_concurrency_rungs values must be positive")
        if self.rpc_concurrency not in self.rpc_concurrency_rungs:
            raise ValueError("rpc_concurrency must be present in rpc_concurrency_rungs")
        return self


class SimulationConfig(ConfigModel):
    window_seconds: int = Field(gt=0)
    arrival_rate_per_second: float = Field(gt=0.0)
    repetitions: int = Field(gt=0)
    seed: int = Field(ge=0)


class ModelConfig(ConfigModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_path_segment(value, label="model.id")


class FeatureSetConfig(ConfigModel):
    id: str
    outputs: list[str] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_path_segment(value, label="feature_set.id")

    @field_validator("outputs")
    @classmethod
    def validate_outputs(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("feature_set.outputs must not contain duplicates")
        return value

    @model_validator(mode="after")
    def validate_feature_selection(self) -> Self:
        validate_feature_selection(self.id, tuple(self.outputs))
        return self


class StudyConfig(ConfigModel):
    id: str = "default"

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_path_segment(value, label="study.id")


class ArtifactConfig(ConfigModel):
    variant: ArtifactVariant = ArtifactVariant.BASELINE


class TuningTrainingSearchSpace(ConfigModel):
    learning_rate: list[float] | None = Field(default=None, min_length=1)
    weight_decay: list[float] | None = Field(default=None, min_length=1)

    @field_validator("learning_rate")
    @classmethod
    def validate_learning_rate_candidates(cls, values: list[float] | None) -> list[float] | None:
        if values is not None and any(value <= 0.0 for value in values):
            raise ValueError("tuning_space.training.learning_rate values must be positive")
        return values

    @field_validator("weight_decay")
    @classmethod
    def validate_weight_decay_candidates(cls, values: list[float] | None) -> list[float] | None:
        if values is not None and any(value < 0.0 for value in values):
            raise ValueError(
                "tuning_space.training.weight_decay values must be non-negative"
            )
        return values

    @model_validator(mode="after")
    def validate_non_empty_group(self) -> Self:
        if self.learning_rate is None and self.weight_decay is None:
            raise ValueError("tuning_space.training must declare at least one field")
        return self


class ModelTuningSpaceConfig(ConfigModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_path_segment(value, label="tuning_space.model.id")


class TuningSpaceConfig(ConfigModel):
    training: TuningTrainingSearchSpace | None = None
    model: SerializeAsAny[ModelTuningSpaceConfig]

    def has_candidates(self) -> bool:
        model_candidates = self.model.model_dump(exclude={"id"}, exclude_none=True)
        return self.training is not None or bool(model_candidates)


class TunedTrainingParams(ConfigModel):
    learning_rate: float | None = Field(default=None, gt=0.0)
    weight_decay: float | None = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def validate_non_empty_group(self) -> Self:
        if self.learning_rate is None and self.weight_decay is None:
            raise ValueError("tuned training params must declare at least one field")
        return self


class TunedModelParams(ConfigModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _validate_path_segment(value, label="tuned model params id")


class TunedParameterSet(ConfigModel):
    training: TunedTrainingParams | None = None
    model: SerializeAsAny[TunedModelParams] | None = None

    @model_validator(mode="after")
    def validate_non_empty_param_set(self) -> Self:
        if self.training is None and self.model is None:
            raise ValueError("tuned parameter set must declare at least one parameter group")
        return self


class TuningConfig(ConfigModel):
    direction: StudyDirection
    trial_count: int = Field(gt=0)
    timeout_seconds: int | None = Field(default=None, gt=0)
    objective_metric: TuningObjective
    sampler_seed: int = Field(ge=0)
    enable_pruning: bool


class ProviderSpec(ConfigModel):
    name: RpcProviderName
    timeout_seconds: float = Field(gt=0.0)
    retry_count: int = Field(ge=0)
    backoff_factor: float = Field(ge=0.0)

    def endpoint_for(self, chain_name: ChainName) -> str:
        return resolve_provider_endpoint(self.name, chain_name)

    def reference_for(self, chain_name: ChainName) -> str:
        return resolve_provider_reference(self.name, chain_name)


@dataclass(frozen=True, slots=True)
class PathLayout:
    output_root: Path
    dataset_root: Path
    metadata_root: Path
    history_dir: Path
    evaluation_dir: Path
    dataset_metadata_path: Path
    artifact_root: Path | None = None
    checkpoint_dir: Path | None = None
    train_report_path: Path | None = None
    simulation_report_path: Path | None = None
    tuning_root: Path | None = None
    tuning_best_params_path: Path | None = None


def build_path_layout(
    *,
    storage: StorageSpec,
    chain: ChainSpec,
    dataset: DatasetSpec,
    feature_set_id: str | None = None,
    model_id: str | None = None,
    max_delay_seconds: int | None = None,
    variant: ArtifactVariant = ArtifactVariant.BASELINE,
    study_id: str = "default",
    include_artifacts: bool = False,
    tuning_mode: bool = False,
) -> PathLayout:
    output_root = storage.root
    dataset_root = output_root / "datasets" / chain.name.value / dataset.id
    artifact_root: Path | None = None
    checkpoint_dir: Path | None = None
    train_report_path: Path | None = None
    simulation_report_path: Path | None = None
    tuning_root: Path | None = None
    tuning_best_params_path: Path | None = None

    if include_artifacts:
        if feature_set_id is None or model_id is None or max_delay_seconds is None:
            raise ValueError("artifact paths require feature_set_id, model_id, max_delay_seconds")
        artifact_base_root = (
            output_root
            / "models"
            / chain.name.value
            / dataset.id
            / feature_set_id
            / model_id
            / f"{max_delay_seconds}s"
        )
        variant_root = artifact_base_root / variant.value / study_id
        tuned_study_root = artifact_base_root / ArtifactVariant.TUNED.value / study_id
        artifact_root = tuned_study_root if tuning_mode else variant_root
        checkpoint_dir = artifact_root / "checkpoints"
        train_report_path = artifact_root / "train_report.json"
        simulation_report_path = artifact_root / "simulation_report.json"
        tuning_root = tuned_study_root / "tuning"
        tuning_best_params_path = tuning_root / "best_params.json"

    return PathLayout(
        output_root=output_root,
        dataset_root=dataset_root,
        metadata_root=dataset_root / ".spice",
        history_dir=dataset_root / "history",
        evaluation_dir=dataset_root / "evaluation",
        dataset_metadata_path=dataset_root / ".spice" / "metadata.json",
        artifact_root=artifact_root,
        checkpoint_dir=checkpoint_dir,
        train_report_path=train_report_path,
        simulation_report_path=simulation_report_path,
        tuning_root=tuning_root,
        tuning_best_params_path=tuning_best_params_path,
    )


def _resolve_direct_endpoint(chain_name: ChainName) -> tuple[str, str]:
    env_var = {
        ChainName.ETHEREUM: "ETHEREUM_RPC_URL",
        ChainName.POLYGON: "POLYGON_RPC_URL",
        ChainName.AVALANCHE: "AVALANCHE_RPC_URL",
    }[chain_name]
    value = os.getenv(env_var, "")
    if not value:
        raise ValueError(f"Missing RPC endpoint for chain: {chain_name.value}")
    return value, f"${env_var}"


def _resolve_alchemy_endpoint(chain_name: ChainName) -> tuple[str, str]:
    api_key = os.getenv("ALCHEMY_API_KEY", "")
    if not api_key:
        raise ValueError(f"Missing RPC endpoint for chain: {chain_name.value}")
    host = {
        ChainName.ETHEREUM: "https://eth-mainnet.g.alchemy.com/v2/{key}",
        ChainName.POLYGON: "https://polygon-mainnet.g.alchemy.com/v2/{key}",
        ChainName.AVALANCHE: "https://avax-mainnet.g.alchemy.com/v2/{key}",
    }[chain_name]
    return host.format(key=api_key), host.format(key="$ALCHEMY_API_KEY")


def _resolve_publicnode_endpoint(chain_name: ChainName) -> tuple[str, str]:
    endpoint = {
        ChainName.ETHEREUM: "https://ethereum-rpc.publicnode.com",
        ChainName.POLYGON: "https://polygon-bor-rpc.publicnode.com",
        ChainName.AVALANCHE: "https://avalanche-c-chain-rpc.publicnode.com",
    }[chain_name]
    return endpoint, endpoint


def resolve_provider_endpoint(provider_name: RpcProviderName, chain_name: ChainName) -> str:
    endpoint, _ = _resolve_provider(provider_name, chain_name)
    return endpoint


def resolve_provider_reference(provider_name: RpcProviderName, chain_name: ChainName) -> str:
    _, reference = _resolve_provider(provider_name, chain_name)
    return reference


def _resolve_provider(
    provider_name: RpcProviderName,
    chain_name: ChainName,
) -> tuple[str, str]:
    if provider_name is RpcProviderName.DIRECT:
        return _resolve_direct_endpoint(chain_name)
    if provider_name is RpcProviderName.ALCHEMY:
        return _resolve_alchemy_endpoint(chain_name)
    if provider_name is RpcProviderName.PUBLICNODE:
        return _resolve_publicnode_endpoint(chain_name)
    raise ValueError(f"Unsupported provider: {provider_name}")


def apply_rpc_profile(
    *,
    provider_name: RpcProviderName,
    chain_name: ChainName,
    acquisition: AcquisitionConfig,
) -> AcquisitionConfig:
    del chain_name
    if provider_name is RpcProviderName.PUBLICNODE:
        return acquisition.model_copy(
            update={
                "chunk_size": 8192,
                "rpc_batch_size": 256,
                "rpc_concurrency": 48,
                "rpc_min_batch_size": 64,
                "rpc_concurrency_rungs": [8, 16, 24, 32, 48],
            }
        )
    return acquisition


class WorkflowConfig(ConfigModel):
    task: WorkflowTask
    chain: ChainSpec
    dataset: DatasetSpec
    storage: StorageSpec

    @property
    def evaluation_window_start_timestamp(self) -> int:
        return _utc_midnight_timestamp(self.dataset.evaluation_date)

    @property
    def evaluation_window_end_timestamp(self) -> int:
        return _utc_midnight_timestamp(self.dataset.evaluation_date + timedelta(days=1))

    @property
    def history_window_end_timestamp(self) -> int:
        return self.evaluation_window_start_timestamp


class AcquireConfig(WorkflowConfig):
    task: WorkflowTask = WorkflowTask.ACQUIRE
    provider: ProviderSpec
    acquisition: AcquisitionConfig

    @model_validator(mode="after")
    def validate_history_sample_budget(self) -> Self:
        if self.effective_history_sample_budget < self.dataset.sampling.sample_count:
            raise ValueError(
                "acquisition.history_sample_budget must be at least dataset.sampling.sample_count"
            )
        self.provider.endpoint_for(self.chain.name)
        return self

    @property
    def effective_history_sample_budget(self) -> int:
        if self.acquisition.history_sample_budget is None:
            return self.dataset.sampling.sample_count
        return self.acquisition.history_sample_budget

    @property
    def paths(self) -> PathLayout:
        return build_path_layout(storage=self.storage, chain=self.chain, dataset=self.dataset)


class ModelWorkflowConfig(WorkflowConfig):
    model: SerializeAsAny[ModelConfig]
    feature_set: FeatureSetConfig
    study: StudyConfig = StudyConfig()
    artifact: ArtifactConfig = ArtifactConfig()

    @property
    def paths(self) -> PathLayout:
        return build_path_layout(
            storage=self.storage,
            chain=self.chain,
            dataset=self.dataset,
            feature_set_id=self.feature_set.id,
            model_id=self.model.id,
            max_delay_seconds=self.dataset.temporal.max_delay_seconds,
            variant=self.artifact.variant,
            study_id=self.study.id,
            include_artifacts=True,
            tuning_mode=self.task is WorkflowTask.TUNE,
        )


class TrainConfig(ModelWorkflowConfig):
    task: WorkflowTask = WorkflowTask.TRAIN
    split: SplitConfig
    training: TrainingConfig


class TuneConfig(ModelWorkflowConfig):
    task: WorkflowTask = WorkflowTask.TUNE
    split: SplitConfig
    training: TrainingConfig
    tuning: TuningConfig
    tuning_space: TuningSpaceConfig

    @model_validator(mode="after")
    def validate_tuning_space(self) -> Self:
        if self.tuning_space.model.id != self.model.id:
            raise ValueError("tuning_space.model.id must match model.id")
        if not self.tuning_space.has_candidates():
            raise ValueError("tuning_space must declare at least one tunable parameter")
        return self


class SimulateConfig(ModelWorkflowConfig):
    task: WorkflowTask = WorkflowTask.SIMULATE
    training: TrainingConfig
    simulation: SimulationConfig


class PresetSpec(ConfigModel):
    dataset: str | None = None
    chain: str | None = None
    provider: str | None = None
    model: str | None = None
    feature_set: str | None = None
    acquisition: str | None = None
    training: str | None = None
    split: str | None = None
    simulation: str | None = None
    tuning: str | None = None
    tuning_space: str | None = None
    storage: StorageSpec | None = None
    study: StudyConfig | None = None
    artifact: ArtifactConfig | None = None

