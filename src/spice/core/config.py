"""Runtime configuration validated by Pydantic."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Self, cast

from hydra import compose, initialize_config_module
from omegaconf import DictConfig, OmegaConf
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializeAsAny,
    TypeAdapter,
    field_validator,
    model_validator,
)

from ..features import validate_feature_selection
from .json import JsonObject


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


class ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def _utc_midnight_timestamp(value: date) -> int:
    return int(datetime.combine(value, time.min, tzinfo=UTC).timestamp())


class ChainConfig(ConfigModel):
    name: ChainName
    chain_id: int = Field(gt=0)
    block_time_seconds: float = Field(gt=0)
    uses_poa_extra_data: bool


class DatasetTemporalConfig(ConfigModel):
    max_delay_seconds: int = Field(gt=0)
    lookback_seconds: int = Field(gt=0)


class DatasetSamplingConfig(ConfigModel):
    sample_count: int = Field(gt=0)


class DatasetConfig(ConfigModel):
    id: str
    temporal: DatasetTemporalConfig
    sampling: DatasetSamplingConfig

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not value or "/" in value or "\\" in value:
            raise ValueError("dataset id must be a non-empty path segment")
        return value


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
    dry_run: bool
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


class EvaluationConfig(ConfigModel):
    date: date


class ModelConfig(ConfigModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not value or "/" in value or "\\" in value:
            raise ValueError("model.id must be a non-empty path segment")
        return value


class StudyConfig(ConfigModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not value or "/" in value or "\\" in value:
            raise ValueError("study id must be a non-empty path segment")
        return value


class ArtifactConfig(ConfigModel):
    variant: ArtifactVariant


class FeatureSetConfig(ConfigModel):
    id: str
    outputs: list[str] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not value or "/" in value or "\\" in value:
            raise ValueError("feature_set.id must be a non-empty path segment")
        return value

    @field_validator("outputs")
    @classmethod
    def validate_outputs(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("feature_set.outputs must not contain duplicates")
        return value


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

    @classmethod
    def validate_id(cls, value: str) -> str:
        if not value or "/" in value or "\\" in value:
            raise ValueError("tuning_space.model.id must be a non-empty path segment")
        return value

    @field_validator("id")
    @classmethod
    def validate_model_id(cls, value: str) -> str:
        return cls.validate_id(value)


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
        if not value or "/" in value or "\\" in value:
            raise ValueError("tuned model params id must be a non-empty path segment")
        return value


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


class RuntimeConfig(ConfigModel):
    output_root: Path


class PathsConfig(ConfigModel):
    output_root: Path
    dataset_root: Path
    metadata_root: Path
    history_dir: Path
    evaluation_dir: Path
    dataset_metadata_path: Path
    artifact_root: Path
    checkpoint_dir: Path
    train_report_path: Path
    simulation_report_path: Path
    tuning_root: Path
    tuning_best_params_path: Path


class ProviderConfig(ConfigModel):
    name: RpcProviderName
    endpoints: dict[ChainName, str]
    references: dict[ChainName, str]
    timeout_seconds: float = Field(gt=0.0)
    retry_count: int = Field(ge=0)
    backoff_factor: float = Field(ge=0.0)

    def endpoint_for(self, chain_name: ChainName) -> str:
        value = self.endpoints.get(chain_name, "")
        if not value:
            raise ValueError(f"Missing RPC endpoint for chain: {chain_name.value}")
        return value

    def reference_for(self, chain_name: ChainName) -> str:
        reference = self.references.get(chain_name)
        if reference:
            return reference
        return self.endpoint_for(chain_name)


class ExperimentConfig(ConfigModel):
    task: WorkflowTask
    chain: ChainConfig
    dataset: DatasetConfig
    evaluation: EvaluationConfig
    study: StudyConfig
    model: SerializeAsAny[ModelConfig]
    tuning_space: TuningSpaceConfig | None = None
    artifact: ArtifactConfig
    feature_set: FeatureSetConfig
    acquisition: AcquisitionConfig
    split: SplitConfig
    training: TrainingConfig
    simulation: SimulationConfig
    tuning: TuningConfig
    runtime: RuntimeConfig
    paths: PathsConfig
    provider: ProviderConfig

    @model_validator(mode="after")
    def validate_provider_for_task(self) -> Self:
        if self.task is WorkflowTask.ACQUIRE:
            self.provider.endpoint_for(self.chain.name)
        return self

    @model_validator(mode="after")
    def validate_history_sample_budget(self) -> Self:
        if self.effective_history_sample_budget < self.dataset.sampling.sample_count:
            raise ValueError(
                "acquisition.history_sample_budget must be at least "
                "dataset.sampling.sample_count"
            )
        return self

    @model_validator(mode="after")
    def validate_feature_selection(self) -> Self:
        validate_feature_selection(self.feature_set.id, tuple(self.feature_set.outputs))
        return self

    @model_validator(mode="after")
    def validate_tuning_space(self) -> Self:
        if self.tuning_space is not None and self.tuning_space.model.id != self.model.id:
            raise ValueError("tuning_space.model.id must match model.id")
        if self.task is WorkflowTask.TUNE:
            if self.tuning_space is None:
                raise ValueError("tuning_space is required for tune")
            if not self.tuning_space.has_candidates():
                raise ValueError("tuning_space must declare at least one tunable parameter")
        return self

    @property
    def model_id(self) -> str:
        return self.model.id

    @property
    def evaluation_window_start_timestamp(self) -> int:
        return _utc_midnight_timestamp(self.evaluation.date)

    @property
    def evaluation_window_end_timestamp(self) -> int:
        return _utc_midnight_timestamp(self.evaluation.date + timedelta(days=1))

    @property
    def history_window_end_timestamp(self) -> int:
        return self.evaluation_window_start_timestamp

    @property
    def effective_history_sample_budget(self) -> int:
        if self.acquisition.history_sample_budget is None:
            return self.dataset.sampling.sample_count
        return self.acquisition.history_sample_budget


_EXPERIMENT_CONFIG_ADAPTER = TypeAdapter(ExperimentConfig)
_CONF_ROOT = Path(__file__).resolve().parents[1] / "conf"


def coerce_config(cfg: DictConfig, *, task: WorkflowTask | str) -> ExperimentConfig:
    resolved_task = WorkflowTask(task)
    working = OmegaConf.create(OmegaConf.to_container(cfg, resolve=False))
    OmegaConf.set_struct(working, False)
    _normalize_runtime_fields(working)
    _apply_rpc_profile(working)
    _refresh_derived_fields(working, task=resolved_task)
    OmegaConf.update(working, "task", resolved_task.value, merge=False)
    OmegaConf.resolve(working)
    payload = OmegaConf.to_container(working, resolve=True, enum_to_str=True)
    if not isinstance(payload, dict):
        raise TypeError("Hydra configuration did not produce a mapping payload")
    payload.pop("hydra", None)
    _coerce_modeling_payload(payload)
    return _EXPERIMENT_CONFIG_ADAPTER.validate_python(payload)


def config_to_dict(cfg: ExperimentConfig) -> JsonObject:
    payload = _EXPERIMENT_CONFIG_ADAPTER.dump_python(cfg, mode="json")
    if not isinstance(payload, dict):
        raise TypeError("ExperimentConfig did not serialize to a mapping payload")
    return cast(JsonObject, payload)


def revalidate_config(cfg: ExperimentConfig) -> ExperimentConfig:
    payload = config_to_dict(cfg)
    _coerce_modeling_payload(payload)
    return _EXPERIMENT_CONFIG_ADAPTER.validate_python(payload)


def _load_mapping_config(path: Path) -> DictConfig:
    loaded = OmegaConf.load(path)
    if not isinstance(loaded, DictConfig):
        raise TypeError(f"Configuration must be a mapping: {path}")
    return loaded


def _apply_rpc_profile(config: DictConfig) -> None:
    provider_name = OmegaConf.select(config, "provider.name")
    chain_name = OmegaConf.select(config, "chain.name")
    if not isinstance(provider_name, str) or not isinstance(chain_name, str):
        return
    path = _CONF_ROOT / "rpc_profile" / provider_name / f"{chain_name}.yaml"
    if not path.is_file():
        return
    rpc_profile = _load_mapping_config(path)
    acquisition = OmegaConf.select(config, "acquisition")
    OmegaConf.update(
        config,
        "acquisition",
        OmegaConf.to_container(OmegaConf.merge(rpc_profile, acquisition), resolve=False),
        merge=False,
    )


def _refresh_derived_fields(config: DictConfig, *, task: WorkflowTask | str) -> None:
    resolved_task = WorkflowTask(task)
    output_root = Path(str(OmegaConf.select(config, "runtime.output_root")))
    dataset_id = str(OmegaConf.select(config, "dataset.id"))
    study_id = str(OmegaConf.select(config, "study.id"))
    chain_name = str(OmegaConf.select(config, "chain.name"))
    model_id = str(OmegaConf.select(config, "model.id"))
    artifact_variant = str(OmegaConf.select(config, "artifact.variant"))
    feature_set_id = str(OmegaConf.select(config, "feature_set.id"))
    max_delay_seconds = int(OmegaConf.select(config, "dataset.temporal.max_delay_seconds"))
    dataset_root = output_root / "datasets" / chain_name / dataset_id
    artifact_base_root = (
        output_root
        / "models"
        / chain_name
        / dataset_id
        / feature_set_id
        / model_id
        / f"{max_delay_seconds}s"
    )
    variant_root = artifact_base_root / artifact_variant / study_id
    tuned_study_root = artifact_base_root / ArtifactVariant.TUNED.value / study_id
    artifact_root = tuned_study_root if resolved_task is WorkflowTask.TUNE else variant_root
    OmegaConf.update(config, "paths.output_root", str(output_root), merge=False)
    OmegaConf.update(config, "paths.dataset_root", str(dataset_root), merge=False)
    OmegaConf.update(config, "paths.metadata_root", str(dataset_root / ".spice"), merge=False)
    OmegaConf.update(config, "paths.history_dir", str(dataset_root / "history"), merge=False)
    OmegaConf.update(config, "paths.evaluation_dir", str(dataset_root / "evaluation"), merge=False)
    OmegaConf.update(
        config,
        "paths.dataset_metadata_path",
        str(dataset_root / ".spice" / "metadata.json"),
        merge=False,
    )
    OmegaConf.update(config, "paths.artifact_root", str(artifact_root), merge=False)
    OmegaConf.update(
        config,
        "paths.checkpoint_dir",
        str(artifact_root / "checkpoints"),
        merge=False,
    )
    OmegaConf.update(
        config,
        "paths.train_report_path",
        str(artifact_root / "train_report.json"),
        merge=False,
    )
    OmegaConf.update(
        config,
        "paths.simulation_report_path",
        str(artifact_root / "simulation_report.json"),
        merge=False,
    )
    OmegaConf.update(config, "paths.tuning_root", str(tuned_study_root / "tuning"), merge=False)
    OmegaConf.update(
        config,
        "paths.tuning_best_params_path",
        str(tuned_study_root / "tuning" / "best_params.json"),
        merge=False,
    )


def _normalize_runtime_fields(config: DictConfig) -> None:
    compile_value = OmegaConf.select(config, "training.compile")
    if isinstance(compile_value, bool):
        OmegaConf.update(
            config,
            "training.compile",
            "on" if compile_value else "off",
            merge=False,
        )


def _coerce_modeling_payload(payload: dict[str, object]) -> None:
    from ..modeling.registry import coerce_model_config, coerce_tuning_space_config

    raw_model = payload.get("model")
    if raw_model is None:
        raise ValueError("model config is required")
    model_config = coerce_model_config(raw_model)
    payload["model"] = model_config
    payload["tuning_space"] = coerce_tuning_space_config(
        payload.get("tuning_space"),
        model_config=model_config,
    )


def load_hydra_config(
    task: WorkflowTask | str,
    *,
    overrides: Iterable[str] | None = None,
) -> ExperimentConfig:
    resolved_task = WorkflowTask(task)
    with initialize_config_module(version_base=None, config_module="spice.conf"):
        config = compose(config_name=resolved_task.value, overrides=list(overrides or ()))
    if not isinstance(config, DictConfig):
        raise TypeError("Hydra compose did not produce a mapping configuration")
    return coerce_config(config, task=resolved_task)
