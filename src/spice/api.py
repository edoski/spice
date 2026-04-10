"""Supported high-level Python API for SPICE workflows."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .acquisition.cryo import (
    TimestampRange,
    evaluation_range,
    history_range_for_chain,
    run_cryo,
)
from .acquisition.enrich import enrich_path
from .acquisition.provenance import (
    EnrichedSourceManifest,
    RawSourceManifest,
    load_source_manifest,
    source_manifest_path_for,
    write_enrichment_manifest,
    write_source_manifest,
)
from .acquisition.raw_validation import RawPullValidationReport, validate_raw_pull
from .acquisition.rpc import JsonRpcClient
from .acquisition.rpc_providers import (
    RpcProvider,
    RpcProviderName,
    resolve_acquisition_providers,
)
from .acquisition.snapshots import (
    DatasetSnapshotRegistry,
    DatasetSnapshotSummary,
    dataset_root,
    load_snapshot_registry,
    record_snapshot,
    resolve_snapshot_name,
    snapshot_root,
)
from .acquisition.snapshots import (
    activate_snapshot as mark_active_snapshot,
)
from .core.config import (
    BlockSegment,
    ChainConfig,
    ChainName,
    ExperimentConfig,
    ModelConfig,
    ModelFamily,
)
from .core.console import NullReporter, Reporter
from .core.constants import SIMULATION_REPORT_FILENAME, TRAIN_REPORT_FILENAME
from .data.datasets import derive_dataset_geometry
from .data.io import load_enriched_block_frame
from .modeling.artifacts import (
    build_training_artifact_manifest,
    load_training_artifact,
    write_training_artifact,
)
from .modeling.inference import predict_class_offsets
from .modeling.pipeline import TrainingSpec, prepare_inference_dataset, run_training
from .modeling.reporting import (
    SimulationReport,
    TrainingRunReport,
    build_simulation_report,
    build_training_run_report,
    write_json_report,
)
from .modeling.simulation import run_temporal_simulation

__all__ = [
    "SimulationReport",
    "TrainingRunReport",
    "acquire_snapshot",
    "activate_snapshot",
    "list_snapshots",
    "load_config",
    "resolve_artifact_dir",
    "resolve_snapshot_paths",
    "simulate_model",
    "train_model",
]


@dataclass(slots=True)
class BlockPullResult:
    output_dir: Path
    validation: RawPullValidationReport | None
    source_manifest_path: Path | None
    command: str
    completed_chunks: int
    expected_chunks: int | None


@dataclass(slots=True)
class SnapshotPaths:
    snapshot_name: str
    snapshot_root: Path
    raw_history_dir: Path
    raw_evaluation_dir: Path
    enriched_history_dir: Path
    enriched_evaluation_dir: Path


@dataclass(slots=True)
class SnapshotAcquireSegmentResult:
    segment: BlockSegment
    raw: BlockPullResult
    enriched_output_dir: Path
    enriched_source_manifest_path: Path
    enriched_file_count: int


@dataclass(slots=True)
class SnapshotAcquireResult:
    snapshot_name: str
    snapshot_root: Path
    activated: bool
    history: SnapshotAcquireSegmentResult
    evaluation: SnapshotAcquireSegmentResult
    pull_provider: str
    enrich_provider: str


@dataclass(slots=True)
class DatasetSnapshotInfo:
    chain: str
    name: str
    active: bool
    created_at_utc: str
    updated_at_utc: str
    pull_provider: str
    enrich_provider: str
    history_start_timestamp: int
    history_end_timestamp: int
    evaluation_start_timestamp: int
    evaluation_end_timestamp: int


@dataclass(slots=True)
class DatasetSnapshotDetails:
    summary: DatasetSnapshotInfo
    paths: SnapshotPaths
    raw_history_manifest: RawSourceManifest | None
    raw_evaluation_manifest: RawSourceManifest | None
    enriched_history_manifest: EnrichedSourceManifest | None
    enriched_evaluation_manifest: EnrichedSourceManifest | None


@dataclass(slots=True)
class EnrichedDatasetValidation:
    path: Path
    status: Literal["clean", "error"]
    error: str | None = None


@dataclass(slots=True)
class SnapshotValidationResult:
    snapshot_name: str
    history_raw: RawPullValidationReport
    evaluation_raw: RawPullValidationReport
    history_enriched: EnrichedDatasetValidation
    evaluation_enriched: EnrichedDatasetValidation

    @property
    def status(self) -> Literal["clean", "warning", "error"]:
        if "error" in (
            self.history_raw.status,
            self.evaluation_raw.status,
            self.history_enriched.status,
            self.evaluation_enriched.status,
        ):
            return "error"
        if "warning" in (self.history_raw.status, self.evaluation_raw.status):
            return "warning"
        return "clean"


@dataclass(slots=True)
class TrainingModelResult:
    snapshot_name: str
    artifact_dir: Path
    training_report: TrainingRunReport
    simulation_report: SimulationReport | None


@dataclass(slots=True)
class SimulationModelResult:
    snapshot_name: str
    artifact_dir: Path
    report: SimulationReport


def load_config(path: Path) -> ExperimentConfig:
    return ExperimentConfig.load(path)


def _segment_timestamp_range(chain: ChainConfig, segment: BlockSegment) -> TimestampRange:
    return history_range_for_chain(chain) if segment is BlockSegment.HISTORY else evaluation_range()


def _build_training_spec(
    config: ExperimentConfig,
    *,
    chain: ChainConfig,
    family: ModelFamily | str,
    max_delay_seconds: int,
    device: str | None = None,
) -> TrainingSpec:
    model = ModelConfig(family=ModelFamily(family))
    training = config.training if device is None else config.training.model_copy(
        update={"device": device}
    )
    return TrainingSpec(
        chain=chain,
        model=model,
        max_delay_seconds=max_delay_seconds,
        lookback_seconds=config.lookback_seconds,
        target_anchor_count=config.target_anchor_count,
        split=config.split,
        training=training,
    )


def _resolve_chain(
    config: ExperimentConfig,
    chain_name: ChainName | str | None,
) -> ChainConfig:
    if chain_name is None:
        if len(config.chains) != 1:
            raise ValueError("chain_name is required when config contains multiple chains")
        return config.chains[0]
    return config.resolve_chain(chain_name)


def _resolve_max_delay_seconds(config: ExperimentConfig, max_delay_seconds: int | None) -> int:
    if max_delay_seconds is None:
        if len(config.max_delay_seconds) != 1:
            raise ValueError(
                "max_delay_seconds is required when config contains multiple delay values"
            )
        return config.max_delay_seconds[0]
    if max_delay_seconds not in config.max_delay_seconds:
        raise ValueError(f"Unsupported max_delay_seconds for config: {max_delay_seconds}")
    return max_delay_seconds


def resolve_artifact_dir(
    config: ExperimentConfig,
    family: ModelFamily | str,
    chain_name: ChainName | str | None = None,
    max_delay_seconds: int | None = None,
    *,
    run_name: str | None = None,
) -> Path:
    chain = _resolve_chain(config, chain_name)
    delay_seconds = _resolve_max_delay_seconds(config, max_delay_seconds)
    base_dir = (
        config.output_root
        / "runs"
        / chain.name.value
        / f"{ModelFamily(family).value}-{delay_seconds}s"
    )
    return base_dir if run_name is None else base_dir / run_name


def resolve_snapshot_paths(
    config: ExperimentConfig,
    chain_name: ChainName | str | None = None,
    snapshot_name: str | None = None,
) -> SnapshotPaths:
    chain = _resolve_chain(config, chain_name)
    resolved_snapshot = resolve_snapshot_name(config.output_root, chain, snapshot_name)
    root = snapshot_root(config.output_root, chain, resolved_snapshot)
    if not root.is_dir():
        raise ValueError(f"Snapshot does not exist for {chain.name.value}: {resolved_snapshot}")
    return SnapshotPaths(
        snapshot_name=resolved_snapshot,
        snapshot_root=root,
        raw_history_dir=dataset_root(
            config.output_root,
            chain,
            resolved_snapshot,
            dataset_kind="raw",
            segment=BlockSegment.HISTORY,
        ),
        raw_evaluation_dir=dataset_root(
            config.output_root,
            chain,
            resolved_snapshot,
            dataset_kind="raw",
            segment=BlockSegment.EVALUATION,
        ),
        enriched_history_dir=dataset_root(
            config.output_root,
            chain,
            resolved_snapshot,
            dataset_kind="enriched",
            segment=BlockSegment.HISTORY,
        ),
        enriched_evaluation_dir=dataset_root(
            config.output_root,
            chain,
            resolved_snapshot,
            dataset_kind="enriched",
            segment=BlockSegment.EVALUATION,
        ),
    )


def _snapshot_info_from_summary(
    chain: ChainConfig,
    registry: DatasetSnapshotRegistry,
    summary: DatasetSnapshotSummary,
) -> DatasetSnapshotInfo:
    return DatasetSnapshotInfo(
        chain=chain.name.value,
        name=summary.name,
        active=registry.active_snapshot == summary.name,
        created_at_utc=summary.created_at_utc,
        updated_at_utc=summary.updated_at_utc,
        pull_provider=summary.pull_provider,
        enrich_provider=summary.enrich_provider,
        history_start_timestamp=summary.history_start_timestamp,
        history_end_timestamp=summary.history_end_timestamp,
        evaluation_start_timestamp=summary.evaluation_start_timestamp,
        evaluation_end_timestamp=summary.evaluation_end_timestamp,
    )


def list_snapshots(
    config: ExperimentConfig,
    chain_name: ChainName | str | None = None,
) -> list[DatasetSnapshotInfo]:
    chains = [_resolve_chain(config, chain_name)] if chain_name is not None else list(config.chains)
    infos: list[DatasetSnapshotInfo] = []
    for chain in chains:
        registry = load_snapshot_registry(config.output_root, chain)
        infos.extend(
            _snapshot_info_from_summary(chain, registry, summary) for summary in registry.snapshots
        )
    return sorted(infos, key=lambda item: (item.chain, item.name))


def activate_snapshot(
    config: ExperimentConfig,
    snapshot_name: str,
    chain_name: ChainName | str | None = None,
) -> DatasetSnapshotInfo:
    chain = _resolve_chain(config, chain_name)
    registry = mark_active_snapshot(config.output_root, chain, snapshot_name)
    summary = next(item for item in registry.snapshots if item.name == snapshot_name)
    return _snapshot_info_from_summary(chain, registry, summary)


def _read_snapshot_details(
    config: ExperimentConfig,
    chain: ChainConfig,
    snapshot_name: str | None,
) -> DatasetSnapshotDetails:
    paths = resolve_snapshot_paths(config, chain.name, snapshot_name)
    registry = load_snapshot_registry(config.output_root, chain)
    summary = next((item for item in registry.snapshots if item.name == paths.snapshot_name), None)
    if summary is None:
        raise ValueError(f"Snapshot metadata missing for {chain.name.value}: {paths.snapshot_name}")
    return DatasetSnapshotDetails(
        summary=_snapshot_info_from_summary(chain, registry, summary),
        paths=paths,
        raw_history_manifest=load_source_manifest(paths.raw_history_dir),  # pyright: ignore[reportArgumentType]
        raw_evaluation_manifest=load_source_manifest(paths.raw_evaluation_dir),  # pyright: ignore[reportArgumentType]
        enriched_history_manifest=load_source_manifest(paths.enriched_history_dir),  # pyright: ignore[reportArgumentType]
        enriched_evaluation_manifest=load_source_manifest(paths.enriched_evaluation_dir),  # pyright: ignore[reportArgumentType]
    )


def _validate_raw_dataset(
    dataset_path: Path,
    *,
    chain: ChainConfig,
    timestamps: TimestampRange,
) -> RawPullValidationReport:
    try:
        return validate_raw_pull(
            dataset_path,
            expected_chain_name=chain.name.value,
            expected_chain_id=chain.chain_id,
            expected_start_timestamp=timestamps.start,
            expected_end_timestamp=timestamps.end,
        )
    except Exception as exc:
        return RawPullValidationReport(
            dataset_path=dataset_path,
            expected_start_timestamp=timestamps.start,
            expected_end_timestamp=timestamps.end,
            status="error",
            errors=[str(exc)],
        )


def _validate_enriched_dataset(dataset_path: Path) -> EnrichedDatasetValidation:
    try:
        load_enriched_block_frame(dataset_path)
    except Exception as exc:
        return EnrichedDatasetValidation(path=dataset_path, status="error", error=str(exc))
    return EnrichedDatasetValidation(path=dataset_path, status="clean")


def _validate_snapshot(
    config: ExperimentConfig,
    chain: ChainConfig,
    snapshot_name: str | None,
) -> SnapshotValidationResult:
    paths = resolve_snapshot_paths(config, chain.name, snapshot_name)
    return SnapshotValidationResult(
        snapshot_name=paths.snapshot_name,
        history_raw=_validate_raw_dataset(
            paths.raw_history_dir,
            chain=chain,
            timestamps=_segment_timestamp_range(chain, BlockSegment.HISTORY),
        ),
        evaluation_raw=_validate_raw_dataset(
            paths.raw_evaluation_dir,
            chain=chain,
            timestamps=_segment_timestamp_range(chain, BlockSegment.EVALUATION),
        ),
        history_enriched=_validate_enriched_dataset(paths.enriched_history_dir),
        evaluation_enriched=_validate_enriched_dataset(paths.enriched_evaluation_dir),
    )


def _execute_block_pull_to_dir(
    *,
    config: ExperimentConfig,
    config_path: Path | None,
    chain: ChainConfig,
    segment: BlockSegment,
    provider: RpcProvider,
    output_dir: Path,
    dry_run: bool,
    overwrite: bool,
    reporter: Reporter | None = None,
) -> BlockPullResult:
    timestamps = _segment_timestamp_range(chain, segment)
    cryo_result = run_cryo(
        chain,
        config.pull,
        output_dir,
        timestamps,
        provider=provider,
        overwrite=overwrite,
        dry_run=dry_run,
        reporter=reporter,
    )
    validation = None
    source_manifest_path = None
    if not dry_run:
        validation = validate_raw_pull(
            output_dir,
            expected_chain_name=chain.name.value,
            expected_chain_id=chain.chain_id,
            expected_start_timestamp=timestamps.start,
            expected_end_timestamp=timestamps.end,
        )
        source_manifest_path = write_source_manifest(
            output_dir,
            config_path=config_path,
            chain=chain,
            segment=segment,
            timestamps=timestamps,
            provider=provider,
            pull=config.pull,
            overwrite=overwrite,
            validation=validation,
        )
    return BlockPullResult(
        output_dir=output_dir,
        validation=validation,
        source_manifest_path=source_manifest_path,
        command=cryo_result.command,
        completed_chunks=cryo_result.completed_chunks,
        expected_chunks=cryo_result.expected_chunks,
    )


def _enrich_blocks_to_path(
    *,
    chain: ChainConfig,
    input_path: Path,
    output_path: Path,
    provider: RpcProvider,
    batch_size: int,
    max_methods_per_second: float,
    reporter: Reporter | None = None,
) -> list[Path]:
    with JsonRpcClient(provider.url_for(chain.name)) as client:
        return enrich_path(
            input_path,
            output_path,
            fetch_gas_limits=client.get_block_gas_limits,
            batch_size=batch_size,
            max_methods_per_second=max_methods_per_second,
            reporter=reporter,
        )


def _acquire_segment(
    *,
    config: ExperimentConfig,
    config_path: Path | None,
    chain: ChainConfig,
    paths: SnapshotPaths,
    segment: BlockSegment,
    pull_provider: RpcProvider,
    enrich_provider: RpcProvider,
    dry_run: bool,
    overwrite: bool,
    batch_size: int,
    max_methods_per_second: float,
    reporter: Reporter | None = None,
) -> SnapshotAcquireSegmentResult:
    raw_dir = paths.raw_history_dir if segment is BlockSegment.HISTORY else paths.raw_evaluation_dir
    enriched_dir = (
        paths.enriched_history_dir
        if segment is BlockSegment.HISTORY
        else paths.enriched_evaluation_dir
    )
    raw_result = _execute_block_pull_to_dir(
        config=config,
        config_path=config_path,
        chain=chain,
        segment=segment,
        provider=pull_provider,
        output_dir=raw_dir,
        dry_run=dry_run,
        overwrite=overwrite,
        reporter=reporter,
    )
    if raw_result.validation is not None and raw_result.validation.status == "error":
        raise ValueError(f"Cannot enrich {segment.value} dataset with raw validation errors")

    enriched_manifest_path = source_manifest_path_for(enriched_dir)
    enriched_file_count = 0
    if not dry_run:
        written = _enrich_blocks_to_path(
            chain=chain,
            input_path=raw_result.output_dir,
            output_path=enriched_dir,
            provider=enrich_provider,
            batch_size=batch_size,
            max_methods_per_second=max_methods_per_second,
            reporter=reporter,
        )
        enriched_file_count = len(written)
        enriched_manifest_path = write_enrichment_manifest(
            enriched_dir,
            config_path=config_path,
            input_path=raw_result.output_dir,
            chain=chain,
            segment=segment,
            provider=enrich_provider,
            batch_size=batch_size,
            max_methods_per_second=max_methods_per_second,
        )

    return SnapshotAcquireSegmentResult(
        segment=segment,
        raw=raw_result,
        enriched_output_dir=enriched_dir,
        enriched_source_manifest_path=enriched_manifest_path,
        enriched_file_count=enriched_file_count,
    )


def acquire_snapshot(
    config: ExperimentConfig,
    chain_name: ChainName | str | None = None,
    *,
    snapshot_name: str = "working",
    rpc_provider: RpcProviderName | None = None,
    pull_provider: RpcProviderName | None = None,
    enrich_provider: RpcProviderName | None = None,
    dry_run: bool = True,
    overwrite: bool = False,
    activate: bool = True,
    batch_size: int = 100,
    max_methods_per_second: float = 20.0,
    reporter: Reporter | None = None,
    config_path: Path | None = None,
) -> SnapshotAcquireResult:
    chain = _resolve_chain(config, chain_name)
    reporter = reporter or NullReporter()
    paths = SnapshotPaths(
        snapshot_name=snapshot_name,
        snapshot_root=snapshot_root(config.output_root, chain, snapshot_name),
        raw_history_dir=dataset_root(
            config.output_root,
            chain,
            snapshot_name,
            dataset_kind="raw",
            segment=BlockSegment.HISTORY,
        ),
        raw_evaluation_dir=dataset_root(
            config.output_root,
            chain,
            snapshot_name,
            dataset_kind="raw",
            segment=BlockSegment.EVALUATION,
        ),
        enriched_history_dir=dataset_root(
            config.output_root,
            chain,
            snapshot_name,
            dataset_kind="enriched",
            segment=BlockSegment.HISTORY,
        ),
        enriched_evaluation_dir=dataset_root(
            config.output_root,
            chain,
            snapshot_name,
            dataset_kind="enriched",
            segment=BlockSegment.EVALUATION,
        ),
    )
    if paths.snapshot_root.exists() and not overwrite and not dry_run:
        raise ValueError(f"Snapshot already exists for {chain.name.value}: {snapshot_name}")
    if paths.snapshot_root.exists() and overwrite and not dry_run:
        shutil.rmtree(paths.snapshot_root)

    providers = resolve_acquisition_providers(
        rpc_provider,
        pull_provider_name=pull_provider,
        enrich_provider_name=enrich_provider,
        chains=(chain.name,),
    )
    history_result = _acquire_segment(
        config=config,
        config_path=config_path,
        chain=chain,
        paths=paths,
        segment=BlockSegment.HISTORY,
        pull_provider=providers.pull,
        enrich_provider=providers.enrich,
        dry_run=dry_run,
        overwrite=overwrite,
        batch_size=batch_size,
        max_methods_per_second=max_methods_per_second,
        reporter=reporter,
    )
    evaluation_result = _acquire_segment(
        config=config,
        config_path=config_path,
        chain=chain,
        paths=paths,
        segment=BlockSegment.EVALUATION,
        pull_provider=providers.pull,
        enrich_provider=providers.enrich,
        dry_run=dry_run,
        overwrite=overwrite,
        batch_size=batch_size,
        max_methods_per_second=max_methods_per_second,
        reporter=reporter,
    )

    activated = False
    if not dry_run:
        record_snapshot(
            config.output_root,
            chain,
            snapshot_name=snapshot_name,
            pull_provider=providers.pull.name.value,
            enrich_provider=providers.enrich.name.value,
            history_start_timestamp=_segment_timestamp_range(chain, BlockSegment.HISTORY).start,
            history_end_timestamp=_segment_timestamp_range(chain, BlockSegment.HISTORY).end,
            evaluation_start_timestamp=_segment_timestamp_range(
                chain,
                BlockSegment.EVALUATION,
            ).start,
            evaluation_end_timestamp=_segment_timestamp_range(chain, BlockSegment.EVALUATION).end,
        )
        if activate:
            mark_active_snapshot(config.output_root, chain, snapshot_name)
            activated = True

    return SnapshotAcquireResult(
        snapshot_name=snapshot_name,
        snapshot_root=paths.snapshot_root,
        activated=activated,
        history=history_result,
        evaluation=evaluation_result,
        pull_provider=providers.pull.name.value,
        enrich_provider=providers.enrich.name.value,
    )


def _run_training_workflow(
    config: ExperimentConfig,
    history_block_path: Path,
    artifact_dir: Path,
    chain: ChainConfig,
    family: ModelFamily | str,
    max_delay_seconds: int,
    *,
    device: str | None = None,
    reporter: Reporter | None = None,
) -> TrainingRunReport:
    reporter = reporter or NullReporter()
    spec = _build_training_spec(
        config,
        chain=chain,
        family=family,
        max_delay_seconds=max_delay_seconds,
        device=device,
    )
    result = run_training(history_block_path, spec=spec, reporter=reporter)
    manifest = build_training_artifact_manifest(result.prepared, spec=spec)
    write_training_artifact(artifact_dir, manifest=manifest, model=result.model)
    report = build_training_run_report(
        result,
        target_anchor_count=spec.target_anchor_count,
        max_delay_seconds=spec.max_delay_seconds,
        lookback_seconds=spec.lookback_seconds,
        chain_name=spec.chain.name.value,
        family=spec.model.family.value,
        block_time_seconds=spec.chain.block_time_seconds,
        manifest=manifest,
        prepared=result.prepared,
        artifact_dir=artifact_dir,
        history_block_path=history_block_path,
        device_requested=spec.training.device,
    )
    write_json_report(artifact_dir / TRAIN_REPORT_FILENAME, report)
    return report


def _run_simulation_workflow(
    config: ExperimentConfig,
    artifact_dir: Path,
    history_block_path: Path,
    evaluation_block_path: Path,
    *,
    device: str | None = None,
) -> SimulationReport:
    loaded_artifact = load_training_artifact(artifact_dir)
    geometry = derive_dataset_geometry(
        lookback_seconds=loaded_artifact.manifest.lookback_seconds,
        max_delay_seconds=loaded_artifact.manifest.max_delay_seconds,
        block_time_seconds=loaded_artifact.manifest.chain.block_time_seconds,
    )
    history_blocks = load_enriched_block_frame(history_block_path)
    evaluation_blocks = load_enriched_block_frame(evaluation_block_path)
    prepared = prepare_inference_dataset(
        history_blocks,
        evaluation_blocks,
        geometry=geometry,
        scaler=loaded_artifact.manifest.scaler,
    )
    device_name = config.training.device if device is None else device
    predicted_offsets = predict_class_offsets(
        loaded_artifact.model,
        store=prepared.store,
        sample_indices=prepared.sample_indices,
        lookback_steps=prepared.geometry.lookback_steps,
        effective_batch_size=config.training.effective_batch_size,
        device=device_name,
    )
    simulation = run_temporal_simulation(
        prepared.store,
        predicted_offsets,
        sample_indices=prepared.sample_indices,
        window_seconds=config.simulation.window_seconds,
        arrival_rate_per_second=config.simulation.arrival_rate_per_second,
        repetitions=config.simulation.repetitions,
        seed=config.simulation.seed,
    )
    report = build_simulation_report(
        loaded_artifact,
        artifact_dir=artifact_dir,
        history_block_path=history_block_path,
        evaluation_block_path=evaluation_block_path,
        prepared=prepared,
        simulation=simulation,
        window_seconds=config.simulation.window_seconds,
        arrival_rate_per_second=config.simulation.arrival_rate_per_second,
        repetitions=config.simulation.repetitions,
    )
    write_json_report(artifact_dir / SIMULATION_REPORT_FILENAME, report)
    return report


def train_model(
    config: ExperimentConfig,
    family: ModelFamily | str,
    chain_name: ChainName | str | None = None,
    max_delay_seconds: int | None = None,
    *,
    snapshot_name: str | None = None,
    run_name: str | None = None,
    device: str | None = None,
    evaluate: bool = False,
    reporter: Reporter | None = None,
) -> TrainingModelResult:
    chain = _resolve_chain(config, chain_name)
    delay_seconds = _resolve_max_delay_seconds(config, max_delay_seconds)
    paths = resolve_snapshot_paths(config, chain.name, snapshot_name)
    artifact_dir = resolve_artifact_dir(
        config,
        family,
        chain.name,
        delay_seconds,
        run_name=run_name,
    )
    training_report = _run_training_workflow(
        config,
        paths.enriched_history_dir,
        artifact_dir,
        chain,
        family,
        delay_seconds,
        device=device,
        reporter=reporter,
    )
    simulation_report = None
    if evaluate:
        simulation_report = _run_simulation_workflow(
            config,
            artifact_dir,
            paths.enriched_history_dir,
            paths.enriched_evaluation_dir,
            device=device,
        )
    return TrainingModelResult(
        snapshot_name=paths.snapshot_name,
        artifact_dir=artifact_dir,
        training_report=training_report,
        simulation_report=simulation_report,
    )


def simulate_model(
    config: ExperimentConfig,
    family: ModelFamily | str,
    chain_name: ChainName | str | None = None,
    max_delay_seconds: int | None = None,
    *,
    snapshot_name: str | None = None,
    run_name: str | None = None,
    device: str | None = None,
) -> SimulationModelResult:
    chain = _resolve_chain(config, chain_name)
    delay_seconds = _resolve_max_delay_seconds(config, max_delay_seconds)
    paths = resolve_snapshot_paths(config, chain.name, snapshot_name)
    artifact_dir = resolve_artifact_dir(
        config,
        family,
        chain.name,
        delay_seconds,
        run_name=run_name,
    )
    report = _run_simulation_workflow(
        config,
        artifact_dir,
        paths.enriched_history_dir,
        paths.enriched_evaluation_dir,
        device=device,
    )
    return SimulationModelResult(
        snapshot_name=paths.snapshot_name,
        artifact_dir=artifact_dir,
        report=report,
    )
