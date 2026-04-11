"""Hydra-driven runtime configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from typing import Any

from omegaconf import DictConfig, OmegaConf
from pydantic import TypeAdapter

from .constants import DEFAULT_WINDOW_END_DATE, DEFAULT_WINDOW_START_DATE


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


def _utc_midnight_timestamp(value: date) -> int:
    return int(datetime.combine(value, time.min, tzinfo=UTC).timestamp())


@dataclass(slots=True)
class ChainConfig:
    name: ChainName = ChainName.ETHEREUM
    chain_id: int = 1
    block_time_seconds: float = 12.0
    uses_poa_extra_data: bool = False


@dataclass(slots=True)
class DatasetWindowConfig:
    start_date: date = DEFAULT_WINDOW_START_DATE
    end_date: date = DEFAULT_WINDOW_END_DATE

    @property
    def start_timestamp(self) -> int:
        return _utc_midnight_timestamp(self.start_date)

    @property
    def end_timestamp(self) -> int:
        return _utc_midnight_timestamp(self.end_date + timedelta(days=1))


@dataclass(slots=True)
class DatasetTemporalConfig:
    max_delay_seconds: int = 36
    lookback_seconds: int = 600


@dataclass(slots=True)
class DatasetSamplingConfig:
    anchor_count: int = 400_000
    history_anchor_count: int | None = None

    @property
    def effective_history_anchor_count(self) -> int:
        if self.history_anchor_count is None:
            return self.anchor_count
        return self.history_anchor_count


@dataclass(slots=True)
class DatasetConfig:
    id: str = "icdcs_2025_11_09"
    window: DatasetWindowConfig = field(default_factory=DatasetWindowConfig)
    temporal: DatasetTemporalConfig = field(default_factory=DatasetTemporalConfig)
    sampling: DatasetSamplingConfig = field(default_factory=DatasetSamplingConfig)


@dataclass(slots=True)
class SplitConfig:
    train_fraction: float = 0.8
    validation_fraction: float = 0.1


@dataclass(slots=True)
class EarlyStoppingConfig:
    patience: int = 8
    min_delta: float = 1e-4


@dataclass(slots=True)
class TrainingConfig:
    learning_rate: float = 3e-4
    weight_decay: float = 1e-2
    batch_size: int = 64
    max_epochs: int = 50
    early_stopping: EarlyStoppingConfig = field(default_factory=EarlyStoppingConfig)
    gradient_clip_norm: float = 1.0
    action_loss_weight: float = 1.0
    fee_loss_weight: float = 0.25
    device: str = "auto"
    seed: int = 2026
    deterministic: bool = True
    log_every_n_steps: int = 10


@dataclass(slots=True)
class AcquisitionConfig:
    requests_per_second: int = 10
    max_concurrent_requests: int = 2
    max_concurrent_chunks: int = 1
    chunk_size: int = 1000
    dry_run: bool = False
    overwrite: bool = False
    enrich_batch_size: int = 100
    max_methods_per_second: float = 20.0


@dataclass(slots=True)
class SimulationConfig:
    window_seconds: int = 7_200
    arrival_rate_per_second: float = 0.05
    repetitions: int = 50
    seed: int = 2026


@dataclass(slots=True)
class ModelConfig:
    family: ModelFamily = ModelFamily.LSTM
    input_projection_dim: int = 128
    hidden_size: int = 128
    num_layers: int = 2
    dropout: float = 0.1
    d_model: int = 128
    nhead: int = 4
    transformer_layers: int = 2
    feedforward_dim: int = 512
    head_hidden_dim: int = 64


@dataclass(slots=True)
class TrackingConfig:
    enabled: bool = True
    experiment_name: str = "spice"
    tracking_uri: str = ""
    tags: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class TuningConfig:
    apply_best_params: bool = False
    study_name: str = "spice-study"
    direction: str = "maximize"
    trial_count: int = 20
    timeout_seconds: int | None = None
    objective_metric: str = "validation_profit_over_baseline"
    sampler_seed: int = 2026
    enable_pruning: bool = True
    search_space: dict[str, list[Any]] = field(
        default_factory=lambda: {
            "training.learning_rate": [1e-4, 3e-4, 1e-3],
            "training.weight_decay": [0.0, 1e-2, 5e-2],
            "model.hidden_size": [64, 128, 256],
            "model.dropout": [0.0, 0.1, 0.2],
        }
    )


@dataclass(slots=True)
class RuntimeConfig:
    output_root: str = "artifacts"
    hydra_run_dir: str = ".hydra/runs/${task}/${now:%Y-%m-%d_%H-%M-%S}"
    hydra_sweep_dir: str = ".hydra/sweeps/${task}/${now:%Y-%m-%d_%H-%M-%S}"


@dataclass(slots=True)
class PathsConfig:
    output_root: str = "${runtime.output_root}"
    dataset_root: str = "${paths.output_root}/datasets/${chain.name}/${dataset.id}"
    metadata_root: str = "${paths.dataset_root}/.spice"
    raw_root: str = "${paths.dataset_root}/raw"
    raw_history_dir: str = "${paths.raw_root}/history"
    raw_evaluation_dir: str = "${paths.raw_root}/evaluation"
    enriched_root: str = "${paths.dataset_root}/enriched"
    enriched_history_dir: str = "${paths.enriched_root}/history"
    enriched_evaluation_dir: str = "${paths.enriched_root}/evaluation"
    dataset_metadata_path: str = "${paths.metadata_root}/metadata.json"
    artifact_root: str = (
        "${paths.output_root}/models/${chain.name}/${dataset.id}/${model.family}/"
        "${dataset.temporal.max_delay_seconds}s"
    )
    checkpoint_dir: str = "${paths.artifact_root}/checkpoints"
    train_report_path: str = "${paths.artifact_root}/train_report.json"
    simulation_report_path: str = "${paths.artifact_root}/simulation_report.json"
    tuning_root: str = "${paths.artifact_root}/tuning"
    tuning_best_params_path: str = "${paths.tuning_root}/best_params.json"
    mlruns_dir: str = "${paths.output_root}/mlruns"


@dataclass(slots=True)
class ProviderConfig:
    name: RpcProviderName = RpcProviderName.PUBLICNODE
    endpoints: dict[str, str] = field(default_factory=dict)
    references: dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 30.0
    retry_count: int = 5
    backoff_factor: float = 0.125

    def endpoint_for(self, chain_name: ChainName | str) -> str:
        key = chain_name.value if isinstance(chain_name, ChainName) else str(chain_name)
        value = self.endpoints.get(key, "")
        if not value:
            raise ValueError(f"Missing RPC endpoint for chain: {key}")
        return value

    def reference_for(self, chain_name: ChainName | str) -> str:
        key = chain_name.value if isinstance(chain_name, ChainName) else str(chain_name)
        reference = self.references.get(key)
        if reference:
            return reference
        return self.endpoint_for(key)

    def sensitive_values(self) -> tuple[str, ...]:
        return tuple(value for value in self.endpoints.values() if value)


@dataclass(slots=True)
class ExperimentConfig:
    task: str = "train"
    chain: ChainConfig = field(default_factory=ChainConfig)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    acquisition: AcquisitionConfig = field(default_factory=AcquisitionConfig)
    split: SplitConfig = field(default_factory=SplitConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    tuning: TuningConfig = field(default_factory=TuningConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    provider: ProviderConfig = field(default_factory=ProviderConfig)


_EXPERIMENT_CONFIG_ADAPTER = TypeAdapter(ExperimentConfig)


def _task_uses_provider(task: str) -> bool:
    return task == "acquire"


def coerce_config(cfg: DictConfig, *, task: str) -> ExperimentConfig:
    base = OmegaConf.create(config_to_dict(ExperimentConfig(task=task)))
    merged = OmegaConf.merge(base, cfg)
    OmegaConf.resolve(merged)
    payload = OmegaConf.to_container(merged, resolve=True, enum_to_str=True)
    if not isinstance(payload, dict):
        raise TypeError("Hydra configuration did not produce a mapping payload")
    config = _EXPERIMENT_CONFIG_ADAPTER.validate_python(payload)
    validate_config(config)
    return config


def config_to_dict(cfg: ExperimentConfig) -> dict[str, Any]:
    payload = _EXPERIMENT_CONFIG_ADAPTER.dump_python(cfg, mode="json")
    if not isinstance(payload, dict):
        raise TypeError("ExperimentConfig did not serialize to a mapping payload")
    return payload


def validate_config(cfg: ExperimentConfig) -> None:
    _validate_dataset(cfg.dataset)
    _validate_chain(cfg.chain)
    _validate_split(cfg.split)
    _validate_training(cfg.training)
    _validate_acquisition(cfg.acquisition)
    _validate_simulation(cfg.simulation)
    _validate_model(cfg.model)
    _validate_provider(cfg)
    _validate_tuning(cfg.tuning)


def _validate_dataset(cfg: DatasetConfig) -> None:
    if not cfg.id or "/" in cfg.id or "\\" in cfg.id:
        raise ValueError("dataset id must be a non-empty path segment")
    if cfg.window.start_date > cfg.window.end_date:
        raise ValueError("dataset.window.start_date must be on or before dataset.window.end_date")
    if cfg.temporal.max_delay_seconds <= 0:
        raise ValueError("dataset.temporal.max_delay_seconds must be positive")
    if cfg.temporal.lookback_seconds <= 0:
        raise ValueError("dataset.temporal.lookback_seconds must be positive")
    if cfg.sampling.anchor_count <= 0:
        raise ValueError("dataset.sampling.anchor_count must be positive")
    if cfg.sampling.history_anchor_count is not None and cfg.sampling.history_anchor_count <= 0:
        raise ValueError("dataset.sampling.history_anchor_count must be positive when set")
    if cfg.sampling.effective_history_anchor_count < cfg.sampling.anchor_count:
        raise ValueError(
            "dataset.sampling.history_anchor_count must be at least "
            "dataset.sampling.anchor_count"
        )


def _validate_chain(cfg: ChainConfig) -> None:
    if cfg.chain_id <= 0:
        raise ValueError("chain_id must be positive")
    if cfg.block_time_seconds <= 0:
        raise ValueError("block_time_seconds must be positive")


def _validate_split(cfg: SplitConfig) -> None:
    if not 0.0 < cfg.train_fraction < 1.0:
        raise ValueError("train_fraction must be greater than 0 and less than 1")
    if not 0.0 <= cfg.validation_fraction < 1.0:
        raise ValueError("validation_fraction must be non-negative and less than 1")
    if cfg.train_fraction + cfg.validation_fraction >= 1.0:
        raise ValueError("train_fraction + validation_fraction must be less than 1")


def _validate_training(cfg: TrainingConfig) -> None:
    if cfg.learning_rate <= 0:
        raise ValueError("learning_rate must be positive")
    if cfg.weight_decay < 0:
        raise ValueError("weight_decay must be non-negative")
    if cfg.batch_size <= 0:
        raise ValueError("training.batch_size must be positive")
    if cfg.max_epochs <= 0:
        raise ValueError("max_epochs must be positive")
    if cfg.early_stopping.patience <= 0:
        raise ValueError("training.early_stopping.patience must be positive")
    if cfg.early_stopping.min_delta < 0:
        raise ValueError("training.early_stopping.min_delta must be non-negative")
    if cfg.gradient_clip_norm <= 0:
        raise ValueError("gradient_clip_norm must be positive")
    if cfg.action_loss_weight <= 0 or cfg.fee_loss_weight <= 0:
        raise ValueError(
            "training.action_loss_weight and training.fee_loss_weight must be positive"
        )
    if cfg.seed < 0:
        raise ValueError("training seed must be non-negative")


def _validate_acquisition(cfg: AcquisitionConfig) -> None:
    if cfg.requests_per_second <= 0:
        raise ValueError("acquisition.requests_per_second must be positive")
    if cfg.max_concurrent_requests <= 0:
        raise ValueError("acquisition.max_concurrent_requests must be positive")
    if cfg.max_concurrent_chunks <= 0:
        raise ValueError("acquisition.max_concurrent_chunks must be positive")
    if cfg.chunk_size <= 0:
        raise ValueError("acquisition.chunk_size must be positive")
    if cfg.enrich_batch_size <= 0:
        raise ValueError("acquisition.enrich_batch_size must be positive")
    if cfg.max_methods_per_second <= 0:
        raise ValueError("acquisition.max_methods_per_second must be positive")


def _validate_simulation(cfg: SimulationConfig) -> None:
    if cfg.window_seconds <= 0:
        raise ValueError("window_seconds must be positive")
    if cfg.arrival_rate_per_second <= 0:
        raise ValueError("arrival_rate_per_second must be positive")
    if cfg.repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if cfg.seed < 0:
        raise ValueError("simulation seed must be non-negative")


def _validate_model(cfg: ModelConfig) -> None:
    if not 0.0 <= cfg.dropout < 1.0:
        raise ValueError("dropout must be between 0 and 1")
    if cfg.input_projection_dim <= 0:
        raise ValueError("input_projection_dim must be positive")
    if cfg.hidden_size <= 0:
        raise ValueError("hidden_size must be positive")
    if cfg.num_layers <= 0:
        raise ValueError("num_layers must be positive")
    if cfg.d_model <= 0 or cfg.nhead <= 0:
        raise ValueError("d_model and nhead must be positive")
    if cfg.d_model % cfg.nhead != 0:
        raise ValueError("d_model must be divisible by nhead")
    if cfg.d_model % 2 != 0:
        raise ValueError("d_model must be even for sinusoidal positional encodings")
    if cfg.transformer_layers <= 0:
        raise ValueError("transformer_layers must be positive")
    if cfg.feedforward_dim <= 0:
        raise ValueError("feedforward_dim must be positive")
    if cfg.head_hidden_dim <= 0:
        raise ValueError("head_hidden_dim must be positive")


def _validate_provider(cfg: ExperimentConfig) -> None:
    if _task_uses_provider(cfg.task):
        if cfg.provider.timeout_seconds <= 0:
            raise ValueError("provider timeout_seconds must be positive")
        if cfg.provider.retry_count < 0:
            raise ValueError("provider.retry_count must be non-negative")
        if cfg.provider.backoff_factor < 0:
            raise ValueError("provider.backoff_factor must be non-negative")
        cfg.provider.endpoint_for(cfg.chain.name)


def _validate_tuning(cfg: TuningConfig) -> None:
    if cfg.trial_count <= 0:
        raise ValueError("tuning.trial_count must be positive")
    if cfg.timeout_seconds is not None and cfg.timeout_seconds <= 0:
        raise ValueError("tuning.timeout_seconds must be positive when set")
