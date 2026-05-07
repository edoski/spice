# pyright: strict

"""Typed acquisition metadata builders."""

from __future__ import annotations

from collections.abc import Iterable
from hashlib import sha256
from pathlib import Path
from typing import cast

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from ..acquisition import AcquisitionRuntimeSnapshot, BlockPullPlan
from ..config.models import AcquireConfig, ChainRuntimeSpec
from ..corpus.io import iter_block_files
from ..corpus.validation import BlockDatasetValidationReport


class CorpusMetadataRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class DatasetIdentity(CorpusMetadataRecord):
    id: str
    name: str


class ChainMetadata(CorpusMetadataRecord):
    name: str
    runtime: ChainRuntimeSpec

    @property
    def chain_id(self) -> int:
        return self.runtime.chain_id


class ProviderMetadata(CorpusMetadataRecord):
    name: str
    reference: str
    endpoint_fingerprint: str


class SplitRequestMetadata(CorpusMetadataRecord):
    start_timestamp: int
    end_timestamp: int
    start_block: int
    end_block: int


class CompactValidationReport(CorpusMetadataRecord):
    status: str
    issues: dict[str, object] | None = None


class SplitCoverageMetadata(CorpusMetadataRecord):
    first_timestamp: int | None
    last_timestamp: int | None
    first_block: int | None
    last_block: int | None
    rows: int


class SplitMaterializationMetadata(CorpusMetadataRecord):
    outcome: str
    file_count: int


class CorpusSplitManifest(CorpusMetadataRecord):
    kind: str
    request: SplitRequestMetadata
    coverage: SplitCoverageMetadata
    validation: CompactValidationReport
    materialization: SplitMaterializationMetadata


class CorpusSplitManifests(CorpusMetadataRecord):
    history: CorpusSplitManifest
    evaluation: CorpusSplitManifest


class CorpusAcquisitionSourceRequirements(CorpusMetadataRecord):
    required_columns: frozenset[str]
    optional_enrichments: frozenset[str]
    temporal_unit: str
    ordering_key: str
    partition_key: str | None

    @field_validator("required_columns", "optional_enrichments", mode="before")
    @classmethod
    def _coerce_string_set(cls, value: object) -> object:
        raw_items: object
        if isinstance(value, frozenset):
            raw_items = cast(object, value)
        elif isinstance(value, (list, set, tuple)):
            raw_items = cast(object, value)
        else:
            return value
        iterable = cast(Iterable[object], raw_items)
        items: list[str] = []
        for item in iterable:
            if not isinstance(item, str):
                return cast(object, value)
            items.append(item)
        return frozenset(items)

    @field_serializer("required_columns", "optional_enrichments")
    def _serialize_string_set(self, value: frozenset[str]) -> list[str]:
        return sorted(value)


class DatasetManifest(CorpusMetadataRecord):
    dataset: DatasetIdentity
    chain: ChainMetadata
    splits: CorpusSplitManifests
    source_requirements: CorpusAcquisitionSourceRequirements


class AcquisitionConfigSnapshot(CorpusMetadataRecord):
    chunk_size: int
    rpc_batch_size: int
    rpc_concurrency: int
    rpc_min_batch_size: int
    rpc_concurrency_rungs: list[int]


class AcquireRunFacts(CorpusMetadataRecord):
    requested_history_window_seconds: int
    resolved_capability_samples: int


class DatasetAcquisitionRuntimeMetadata(CorpusMetadataRecord):
    configured_batch_size: int
    final_batch_size: int
    min_batch_size: int
    configured_concurrency: int
    final_concurrency: int
    concurrency_rungs: list[int]
    oversize_error_count: int
    transient_error_count: int
    oversize_backoffs: int
    transient_backoffs: int
    concurrency_recoveries: int


class AcquireRunRecord(CorpusMetadataRecord):
    provider: ProviderMetadata
    settings: AcquisitionConfigSnapshot
    runtime: DatasetAcquisitionRuntimeMetadata
    facts: AcquireRunFacts


def has_block_files(path: Path) -> bool:
    try:
        return bool(iter_block_files(path))
    except ValueError:
        return False


def provider_metadata(config: AcquireConfig) -> ProviderMetadata:
    return ProviderMetadata(
        name=config.rpc_endpoint.provider_name,
        reference=config.rpc_endpoint.reference,
        endpoint_fingerprint=sha256(config.rpc_endpoint.url.encode("utf-8")).hexdigest()[:16],
    )


def compact_validation_report(report: BlockDatasetValidationReport) -> CompactValidationReport:
    issue_counts: dict[str, int] = {}
    for name in (
        "gap_count",
        "duplicate_count",
        "below_start_count",
        "above_end_count",
    ):
        value = getattr(report, name, 0)
        if value:
            issue_counts[name.removesuffix("_count")] = int(value)

    issues: dict[str, object] | None = None
    if issue_counts or report.errors:
        issues = {
            **issue_counts,
            **({"errors": report.errors} if report.errors else {}),
        }
    return CompactValidationReport(
        status=report.status,
        issues=issues,
    )


def split_manifest(
    *,
    kind: str,
    plan: BlockPullPlan,
    validation: BlockDatasetValidationReport,
    outcome: str,
    file_count: int,
) -> CorpusSplitManifest:
    return CorpusSplitManifest(
        kind=kind,
        request=SplitRequestMetadata(
            start_timestamp=plan.window.start,
            end_timestamp=plan.window.end,
            start_block=plan.block_range.start,
            end_block=plan.block_range.end,
        ),
        coverage=SplitCoverageMetadata(
            first_timestamp=validation.first_timestamp,
            last_timestamp=validation.last_timestamp,
            first_block=validation.first_block_number,
            last_block=validation.last_block_number,
            rows=validation.row_count,
        ),
        validation=compact_validation_report(validation),
        materialization=SplitMaterializationMetadata(
            outcome=outcome,
            file_count=file_count,
        ),
    )


def acquisition_settings(config: AcquireConfig) -> AcquisitionConfigSnapshot:
    return AcquisitionConfigSnapshot(
        chunk_size=config.acquisition.chunk_size,
        rpc_batch_size=config.acquisition.rpc.batch_size,
        rpc_concurrency=config.acquisition.rpc.concurrency,
        rpc_min_batch_size=config.acquisition.rpc.min_batch_size,
        rpc_concurrency_rungs=list(config.acquisition.rpc.concurrency_rungs),
    )


def acquisition_runtime_metadata(
    runtime: AcquisitionRuntimeSnapshot,
) -> DatasetAcquisitionRuntimeMetadata:
    return DatasetAcquisitionRuntimeMetadata(
        configured_batch_size=runtime.configured_batch_size,
        final_batch_size=runtime.final_batch_size,
        min_batch_size=runtime.min_batch_size,
        configured_concurrency=runtime.configured_concurrency,
        final_concurrency=runtime.final_concurrency,
        concurrency_rungs=list(runtime.concurrency_rungs),
        oversize_error_count=runtime.oversize_error_count,
        transient_error_count=runtime.transient_error_count,
        oversize_backoffs=runtime.oversize_backoffs,
        transient_backoffs=runtime.transient_backoffs,
        concurrency_recoveries=runtime.concurrency_recoveries,
    )


def build_dataset_manifest(
    *,
    config: AcquireConfig,
    dataset_id: str,
    history_plan: BlockPullPlan,
    evaluation_plan: BlockPullPlan,
    history_validation: BlockDatasetValidationReport,
    evaluation_validation: BlockDatasetValidationReport,
    history_outcome: str,
    evaluation_outcome: str,
    history_file_count: int,
    evaluation_file_count: int,
    source_requirements: CorpusAcquisitionSourceRequirements,
) -> DatasetManifest:
    return DatasetManifest(
        dataset=DatasetIdentity(
            id=dataset_id,
            name=config.dataset.name,
        ),
        chain=ChainMetadata(
            name=config.chain.name,
            runtime=config.chain.runtime,
        ),
        splits=CorpusSplitManifests(
            history=split_manifest(
                kind="history",
                plan=history_plan,
                validation=history_validation,
                outcome=history_outcome,
                file_count=history_file_count,
            ),
            evaluation=split_manifest(
                kind="evaluation",
                plan=evaluation_plan,
                validation=evaluation_validation,
                outcome=evaluation_outcome,
                file_count=evaluation_file_count,
            ),
        ),
        source_requirements=source_requirements,
    )


def build_acquire_run_record(
    *,
    config: AcquireConfig,
    provider: ProviderMetadata,
    acquisition_runtime: AcquisitionRuntimeSnapshot,
    requested_history_window_seconds: int,
    resolved_capability_samples: int,
) -> AcquireRunRecord:
    return AcquireRunRecord(
        provider=provider,
        settings=acquisition_settings(config),
        runtime=acquisition_runtime_metadata(acquisition_runtime),
        facts=AcquireRunFacts(
            requested_history_window_seconds=requested_history_window_seconds,
            resolved_capability_samples=resolved_capability_samples,
        ),
    )
