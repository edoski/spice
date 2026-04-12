"""Runtime configuration validated by Pydantic."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Self, cast

from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator, model_validator

from .json import JsonObject


class ChainName(StrEnum):
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    AVALANCHE = "avalanche"


class ModelFamily(StrEnum):
    LSTM = "lstm"
    TRANSFORMER = "transformer"
    TRANSFORMER_LSTM = "transformer_lstm"


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


class DatasetSpanConfig(ConfigModel):
    start_date: date
    end_date: date

    @property
    def start_timestamp(self) -> int:
        return _utc_midnight_timestamp(self.start_date)

    @property
    def end_timestamp(self) -> int:
        return _utc_midnight_timestamp(self.end_date + timedelta(days=1))

    @model_validator(mode="after")
    def validate_span(self) -> Self:
        if self.start_date > self.end_date:
            raise ValueError(
                "dataset.span.start_date must be on or before dataset.span.end_date"
            )
        return self


class DatasetTemporalConfig(ConfigModel):
    max_delay_seconds: int = Field(gt=0)
    lookback_seconds: int = Field(gt=0)


class DatasetSamplingConfig(ConfigModel):
    anchor_count: int = Field(gt=0)
    history_anchor_count: int = Field(gt=0)

    @property
    def effective_history_anchor_count(self) -> int:
        return self.history_anchor_count

    @model_validator(mode="after")
    def validate_history_anchor_count(self) -> Self:
        if self.effective_history_anchor_count < self.anchor_count:
            raise ValueError(
                "history_anchor_count must be at least dataset.sampling.anchor_count"
            )
        return self


class DatasetConfig(ConfigModel):
    id: str
    span: DatasetSpanConfig
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
    duration_days: int = Field(gt=0)


class ModelConfig(ConfigModel):
    family: ModelFamily
    input_projection_dim: int = Field(gt=0)
    hidden_size: int = Field(gt=0)
    num_layers: int = Field(gt=0)
    dropout: float = Field(ge=0.0, lt=1.0)
    d_model: int = Field(gt=0)
    nhead: int = Field(gt=0)
    transformer_layers: int = Field(gt=0)
    feedforward_dim: int = Field(gt=0)
    head_hidden_dim: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_transformer_dimensions(self) -> Self:
        if self.d_model % self.nhead != 0:
            raise ValueError("d_model must be divisible by nhead")
        if self.d_model % 2 != 0:
            raise ValueError("d_model must be even for sinusoidal positional encodings")
        return self


class TrackingConfig(ConfigModel):
    enabled: bool
    experiment_name: str
    tracking_uri: str
    tags: dict[str, str]


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


class TuningTrainingSearchSpace(ConfigModel):
    learning_rate: list[float] | None = Field(default=None, min_length=1)
    weight_decay: list[float] | None = Field(default=None, min_length=1)

    @field_validator("learning_rate")
    @classmethod
    def validate_learning_rate_candidates(cls, values: list[float] | None) -> list[float] | None:
        if values is not None and any(value <= 0.0 for value in values):
            raise ValueError("tuning.search_space.training.learning_rate values must be positive")
        return values

    @field_validator("weight_decay")
    @classmethod
    def validate_weight_decay_candidates(cls, values: list[float] | None) -> list[float] | None:
        if values is not None and any(value < 0.0 for value in values):
            raise ValueError(
                "tuning.search_space.training.weight_decay values must be non-negative"
            )
        return values

    @model_validator(mode="after")
    def validate_non_empty_group(self) -> Self:
        if self.learning_rate is None and self.weight_decay is None:
            raise ValueError("tuning.search_space.training must declare at least one field")
        return self


class TuningModelSearchSpace(ConfigModel):
    hidden_size: list[int] | None = Field(default=None, min_length=1)
    dropout: list[float] | None = Field(default=None, min_length=1)

    @field_validator("hidden_size")
    @classmethod
    def validate_hidden_size_candidates(cls, values: list[int] | None) -> list[int] | None:
        if values is not None and any(value <= 0 for value in values):
            raise ValueError("tuning.search_space.model.hidden_size values must be positive")
        return values

    @field_validator("dropout")
    @classmethod
    def validate_dropout_candidates(cls, values: list[float] | None) -> list[float] | None:
        if values is not None and any(value < 0.0 or value >= 1.0 for value in values):
            raise ValueError("tuning.search_space.model.dropout values must be in [0.0, 1.0)")
        return values

    @model_validator(mode="after")
    def validate_non_empty_group(self) -> Self:
        if self.hidden_size is None and self.dropout is None:
            raise ValueError("tuning.search_space.model must declare at least one field")
        return self


class TuningSearchSpace(ConfigModel):
    training: TuningTrainingSearchSpace | None = None
    model: TuningModelSearchSpace | None = None

    @model_validator(mode="after")
    def validate_non_empty_search_space(self) -> Self:
        if self.training is None and self.model is None:
            raise ValueError("tuning.search_space must declare at least one parameter group")
        return self


class TunedTrainingParams(ConfigModel):
    learning_rate: float | None = Field(default=None, gt=0.0)
    weight_decay: float | None = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def validate_non_empty_group(self) -> Self:
        if self.learning_rate is None and self.weight_decay is None:
            raise ValueError("tuned training params must declare at least one field")
        return self


class TunedModelParams(ConfigModel):
    hidden_size: int | None = Field(default=None, gt=0)
    dropout: float | None = Field(default=None, ge=0.0, lt=1.0)

    @model_validator(mode="after")
    def validate_non_empty_group(self) -> Self:
        if self.hidden_size is None and self.dropout is None:
            raise ValueError("tuned model params must declare at least one field")
        return self


class TunedParameterSet(ConfigModel):
    training: TunedTrainingParams | None = None
    model: TunedModelParams | None = None

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
    search_space: TuningSearchSpace


class RuntimeConfig(ConfigModel):
    output_root: Path
    hydra_run_dir: Path
    hydra_sweep_dir: Path


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
    mlruns_dir: Path


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
    model: ModelConfig
    artifact: ArtifactConfig
    acquisition: AcquisitionConfig
    split: SplitConfig
    training: TrainingConfig
    simulation: SimulationConfig
    tracking: TrackingConfig
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
    def validate_evaluation_window(self) -> Self:
        evaluation_seconds = self.evaluation.duration_days * 24 * 60 * 60
        span_seconds = self.dataset.span.end_timestamp - self.dataset.span.start_timestamp
        if evaluation_seconds >= span_seconds:
            raise ValueError(
                "evaluation.duration_days must be shorter than the configured dataset span"
            )
        return self

    @property
    def span_start_timestamp(self) -> int:
        return self.dataset.span.start_timestamp

    @property
    def span_end_timestamp(self) -> int:
        return self.dataset.span.end_timestamp

    @property
    def evaluation_window_start_timestamp(self) -> int:
        return self.span_end_timestamp - self.evaluation.duration_days * 24 * 60 * 60

    @property
    def evaluation_window_end_timestamp(self) -> int:
        return self.span_end_timestamp

    @property
    def history_window_start_timestamp(self) -> int:
        return self.span_start_timestamp

    @property
    def history_window_end_timestamp(self) -> int:
        return self.evaluation_window_start_timestamp


_EXPERIMENT_CONFIG_ADAPTER = TypeAdapter(ExperimentConfig)
_CONF_ROOT = Path(__file__).resolve().parents[1] / "conf"
_PRESET_GROUPS = frozenset({"chain", "model", "provider"})


def coerce_config(cfg: DictConfig, *, task: WorkflowTask | str) -> ExperimentConfig:
    resolved_task = WorkflowTask(task)
    working = OmegaConf.create(OmegaConf.to_container(cfg, resolve=False))
    OmegaConf.set_struct(working, False)
    OmegaConf.update(working, "task", resolved_task.value, merge=False)
    OmegaConf.resolve(working)
    payload = OmegaConf.to_container(working, resolve=True, enum_to_str=True)
    if not isinstance(payload, dict):
        raise TypeError("Hydra configuration did not produce a mapping payload")
    payload.pop("hydra", None)
    return _EXPERIMENT_CONFIG_ADAPTER.validate_python(payload)


def config_to_dict(cfg: ExperimentConfig) -> JsonObject:
    payload = _EXPERIMENT_CONFIG_ADAPTER.dump_python(cfg, mode="json")
    if not isinstance(payload, dict):
        raise TypeError("ExperimentConfig did not serialize to a mapping payload")
    return cast(JsonObject, payload)


def revalidate_config(cfg: ExperimentConfig) -> ExperimentConfig:
    return _EXPERIMENT_CONFIG_ADAPTER.validate_python(config_to_dict(cfg))


def _load_mapping_config(path: Path) -> DictConfig:
    loaded = OmegaConf.load(path)
    if not isinstance(loaded, DictConfig):
        raise TypeError(f"Configuration must be a mapping: {path}")
    return loaded


def _load_preset(group: str, name: str) -> DictConfig:
    path = _CONF_ROOT / group / f"{name}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Unknown {group} preset: {name}")
    preset = _load_mapping_config(path)
    if group == "provider":
        merged = OmegaConf.merge(_load_mapping_config(_CONF_ROOT / group / "base.yaml"), preset)
        if not isinstance(merged, DictConfig):
            raise TypeError(f"Preset must remain a mapping after merge: {path}")
        preset = merged
    payload = OmegaConf.to_container(preset, resolve=False)
    if not isinstance(payload, dict):
        raise TypeError(f"Preset must serialize to a mapping: {path}")
    payload.pop("defaults", None)
    stripped = OmegaConf.create(payload)
    if not isinstance(stripped, DictConfig):
        raise TypeError(f"Preset must remain a mapping after defaults stripping: {path}")
    return stripped


def _apply_named_preset(config: DictConfig, *, group: str, name: str) -> None:
    preset = _load_preset(group, name)
    payload = OmegaConf.to_container(preset, resolve=False)
    OmegaConf.update(config, group, payload, merge=False)


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
        OmegaConf.to_container(
            OmegaConf.merge(acquisition, rpc_profile),
            resolve=False,
        ),
        merge=False,
    )


def _refresh_derived_fields(config: DictConfig, *, task: WorkflowTask | str) -> None:
    resolved_task = WorkflowTask(task)
    output_root = Path(str(OmegaConf.select(config, "runtime.output_root")))
    dataset_id = str(OmegaConf.select(config, "dataset.id"))
    study_id = str(OmegaConf.select(config, "study.id"))
    chain_name = str(OmegaConf.select(config, "chain.name"))
    family = str(OmegaConf.select(config, "model.family"))
    artifact_variant = str(OmegaConf.select(config, "artifact.variant"))
    max_delay_seconds = int(OmegaConf.select(config, "dataset.temporal.max_delay_seconds"))
    dataset_root = output_root / "datasets" / chain_name / dataset_id
    artifact_base_root = (
        output_root
        / "models"
        / chain_name
        / dataset_id
        / family
        / f"{max_delay_seconds}s"
    )
    variant_root = artifact_base_root / artifact_variant / study_id
    tuned_study_root = artifact_base_root / ArtifactVariant.TUNED.value / study_id
    if resolved_task is WorkflowTask.TUNE:
        artifact_root = tuned_study_root
    else:
        artifact_root = variant_root
    OmegaConf.update(config, "task", resolved_task.value, merge=False)
    OmegaConf.update(
        config,
        "runtime.hydra_run_dir",
        f".hydra/runs/{resolved_task.value}",
        merge=False,
    )
    OmegaConf.update(
        config,
        "runtime.hydra_sweep_dir",
        f".hydra/sweeps/{resolved_task.value}",
        merge=False,
    )
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
    OmegaConf.update(
        config,
        "paths.mlruns_dir",
        str(output_root / ".." / ".mlflow"),
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
def _partition_overrides(
    overrides: Iterable[str] | None,
) -> tuple[dict[str, str], list[str]]:
    named: dict[str, str] = {}
    dotlist: list[str] = []
    for raw_override in overrides or ():
        normalized = raw_override[1:] if raw_override.startswith("+") else raw_override
        if "=" not in normalized:
            raise ValueError(f"Overrides must use key=value syntax: {raw_override}")
        key, value = normalized.split("=", 1)
        if key in _PRESET_GROUPS:
            named[key] = value
            continue
        dotlist.append(normalized)
    return named, dotlist


def load_params_config(
    task: WorkflowTask | str,
    *,
    params_path: Path = Path("params.yaml"),
    overrides: Iterable[str] | None = None,
) -> ExperimentConfig:
    created = OmegaConf.create(
        OmegaConf.to_container(_load_mapping_config(params_path), resolve=False)
    )
    if not isinstance(created, DictConfig):
        raise TypeError(f"Configuration must remain a mapping: {params_path}")
    working = created
    OmegaConf.set_struct(working, False)
    named_overrides, dotlist_overrides = _partition_overrides(overrides)
    for group, name in named_overrides.items():
        _apply_named_preset(working, group=group, name=name)
    _apply_rpc_profile(working)
    if dotlist_overrides:
        merged = OmegaConf.merge(working, OmegaConf.from_cli(dotlist_overrides))
        if not isinstance(merged, DictConfig):
            raise TypeError("Overrides must preserve a mapping configuration")
        working = merged
    _normalize_runtime_fields(working)
    _refresh_derived_fields(working, task=task)
    return coerce_config(working, task=task)
