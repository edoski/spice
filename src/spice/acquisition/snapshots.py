"""Dataset snapshot storage and metadata helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..core.config import BlockSegment, ChainConfig
from ..core.constants import SOURCE_MANIFEST_DIRNAME


class SnapshotModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DatasetSnapshotSummary(SnapshotModel):
    name: str
    created_at_utc: str
    updated_at_utc: str
    pull_provider: str
    enrich_provider: str
    history_start_timestamp: int
    history_end_timestamp: int
    evaluation_start_timestamp: int
    evaluation_end_timestamp: int


class DatasetSnapshotRegistry(SnapshotModel):
    kind: Literal["dataset_snapshot_registry"] = "dataset_snapshot_registry"
    chain: str
    active_snapshot: str | None = None
    snapshots: list[DatasetSnapshotSummary] = Field(default_factory=list)


def _now_utc_isoformat() -> str:
    return datetime.now(UTC).isoformat()


def snapshot_chain_root(output_root: Path, chain: ChainConfig) -> Path:
    return output_root / "datasets" / chain.name.value


def snapshot_root(output_root: Path, chain: ChainConfig, snapshot_name: str) -> Path:
    return snapshot_chain_root(output_root, chain) / snapshot_name


def dataset_root(
    output_root: Path,
    chain: ChainConfig,
    snapshot_name: str,
    *,
    dataset_kind: str,
    segment: BlockSegment,
) -> Path:
    return snapshot_root(output_root, chain, snapshot_name) / dataset_kind / segment.value


def snapshot_registry_path(output_root: Path, chain: ChainConfig) -> Path:
    return snapshot_chain_root(output_root, chain) / SOURCE_MANIFEST_DIRNAME / "snapshots.json"


def load_snapshot_registry(output_root: Path, chain: ChainConfig) -> DatasetSnapshotRegistry:
    path = snapshot_registry_path(output_root, chain)
    if not path.is_file():
        return DatasetSnapshotRegistry(chain=chain.name.value)
    return DatasetSnapshotRegistry.model_validate_json(path.read_text(encoding="utf-8"))


def write_snapshot_registry(
    output_root: Path,
    chain: ChainConfig,
    registry: DatasetSnapshotRegistry,
) -> Path:
    path = snapshot_registry_path(output_root, chain)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(registry.model_dump_json(indent=2), encoding="utf-8")
    return path


def record_snapshot(
    output_root: Path,
    chain: ChainConfig,
    *,
    snapshot_name: str,
    pull_provider: str,
    enrich_provider: str,
    history_start_timestamp: int,
    history_end_timestamp: int,
    evaluation_start_timestamp: int,
    evaluation_end_timestamp: int,
) -> DatasetSnapshotRegistry:
    registry = load_snapshot_registry(output_root, chain)
    now = _now_utc_isoformat()
    existing = next((item for item in registry.snapshots if item.name == snapshot_name), None)
    if existing is None:
        summary = DatasetSnapshotSummary(
            name=snapshot_name,
            created_at_utc=now,
            updated_at_utc=now,
            pull_provider=pull_provider,
            enrich_provider=enrich_provider,
            history_start_timestamp=history_start_timestamp,
            history_end_timestamp=history_end_timestamp,
            evaluation_start_timestamp=evaluation_start_timestamp,
            evaluation_end_timestamp=evaluation_end_timestamp,
        )
        snapshots = [*registry.snapshots, summary]
    else:
        snapshots = [
            item
            if item.name != snapshot_name
            else item.model_copy(
                update={
                    "updated_at_utc": now,
                    "pull_provider": pull_provider,
                    "enrich_provider": enrich_provider,
                    "history_start_timestamp": history_start_timestamp,
                    "history_end_timestamp": history_end_timestamp,
                    "evaluation_start_timestamp": evaluation_start_timestamp,
                    "evaluation_end_timestamp": evaluation_end_timestamp,
                }
            )
            for item in registry.snapshots
        ]
    updated = registry.model_copy(
        update={"snapshots": sorted(snapshots, key=lambda item: item.name)}
    )
    write_snapshot_registry(output_root, chain, updated)
    return updated


def activate_snapshot(
    output_root: Path,
    chain: ChainConfig,
    snapshot_name: str,
) -> DatasetSnapshotRegistry:
    registry = load_snapshot_registry(output_root, chain)
    if not any(item.name == snapshot_name for item in registry.snapshots):
        raise ValueError(f"Unknown snapshot for {chain.name.value}: {snapshot_name}")
    updated = registry.model_copy(update={"active_snapshot": snapshot_name})
    write_snapshot_registry(output_root, chain, updated)
    return updated


def resolve_snapshot_name(
    output_root: Path,
    chain: ChainConfig,
    snapshot_name: str | None,
) -> str:
    if snapshot_name is not None:
        return snapshot_name
    registry = load_snapshot_registry(output_root, chain)
    if registry.active_snapshot is None:
        raise ValueError(f"No active snapshot configured for {chain.name.value}")
    return registry.active_snapshot
