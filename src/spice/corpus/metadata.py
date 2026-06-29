# pyright: strict

"""Typed acquisition metadata builders."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from hashlib import sha256
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from ..acquisition import AcquisitionRuntimeSnapshot, BlockPullPlan
from ..config.models import AcquireConfig, ChainRuntimeSpec
from ..corpus.validation import BlockDatasetValidationReport, ValidationStatus

SplitKindValue = Literal["blocks"]
SplitMaterializationOutcomeValue = Literal["created", "reused", "extended", "rebuilt"]


def _coerce_int_tuple(value: object) -> object:
    if isinstance(value, list):
        return tuple(cast(list[object], value))
    return value


class CorpusMetadataRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class CorpusIdentity(CorpusMetadataRecord):
    id: str
    name: str


class ChainMetadata(CorpusMetadataRecord):
    name: str
    runtime: ChainRuntimeSpec

    @field_validator("runtime", mode="before")
    @classmethod
    def _coerce_runtime(_cls, value: object) -> object:
        if isinstance(value, ChainRuntimeSpec):
            return value
        if isinstance(value, Mapping):
            return ChainRuntimeSpec.model_validate(
                dict(cast(Mapping[str, object], value)),
                strict=True,
            )
        return value

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
    status: ValidationStatus
    issues: dict[str, object] | None = None


class SplitCoverageMetadata(CorpusMetadataRecord):
    first_timestamp: int | None
    last_timestamp: int | None
    first_block: int | None
    last_block: int | None
    rows: int


class SplitMaterializationMetadata(CorpusMetadataRecord):
    outcome: SplitMaterializationOutcomeValue
    file_count: int


class CorpusSplitManifest(CorpusMetadataRecord):
    kind: SplitKindValue
    request: SplitRequestMetadata
    coverage: SplitCoverageMetadata
    validation: CompactValidationReport
    materialization: SplitMaterializationMetadata


class CorpusAcquisitionSourceRequirements(CorpusMetadataRecord):
    required_columns: frozenset[str]
    optional_enrichments: frozenset[str]
    temporal_unit: str
    ordering_key: str
    partition_key: str | None

    @field_validator("required_columns", "optional_enrichments", mode="before")
    @classmethod
    def _coerce_string_set(_cls, value: object) -> object:
        if isinstance(value, frozenset):
            raw_items = cast(Iterable[object], value)
        elif isinstance(value, (list, set, tuple)):
            raw_items = cast(Iterable[object], value)
        else:
            return value
        items: list[str] = []
        for item in raw_items:
            if not isinstance(item, str):
                return cast(object, value)
            items.append(item)
        return frozenset(items)

    @field_serializer("required_columns", "optional_enrichments")
    def _serialize_string_set(self, value: frozenset[str]) -> list[str]:
        return sorted(value)

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json")
        return sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


class CorpusManifest(CorpusMetadataRecord):
    corpus: CorpusIdentity
    chain: ChainMetadata
    blocks: CorpusSplitManifest
    source_requirements: CorpusAcquisitionSourceRequirements


class AcquisitionConfigSnapshot(CorpusMetadataRecord):
    chunk_size: int
    rpc_batch_size: int
    rpc_concurrency: int
    rpc_min_batch_size: int
    rpc_concurrency_rungs: tuple[int, ...]

    @field_validator("rpc_concurrency_rungs", mode="before")
    @classmethod
    def _coerce_rpc_concurrency_rungs(_cls, value: object) -> object:
        return _coerce_int_tuple(value)


class AcquireRunFacts(CorpusMetadataRecord):
    requested_window_seconds: int


class CorpusAcquisitionRuntimeMetadata(CorpusMetadataRecord):
    configured_batch_size: int
    final_batch_size: int
    min_batch_size: int
    configured_concurrency: int
    final_concurrency: int
    concurrency_rungs: tuple[int, ...]
    oversize_error_count: int
    transient_error_count: int
    oversize_backoffs: int
    transient_backoffs: int
    concurrency_recoveries: int

    @field_validator("concurrency_rungs", mode="before")
    @classmethod
    def _coerce_concurrency_rungs(_cls, value: object) -> object:
        return _coerce_int_tuple(value)


class AcquireRunRecord(CorpusMetadataRecord):
    provider: ProviderMetadata
    settings: AcquisitionConfigSnapshot
    runtime: CorpusAcquisitionRuntimeMetadata
    facts: AcquireRunFacts


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
    kind: SplitKindValue,
    plan: BlockPullPlan,
    validation: BlockDatasetValidationReport,
    outcome: SplitMaterializationOutcomeValue,
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
        rpc_concurrency_rungs=tuple(config.acquisition.rpc.concurrency_rungs),
    )


def acquisition_runtime_metadata(
    runtime: AcquisitionRuntimeSnapshot,
) -> CorpusAcquisitionRuntimeMetadata:
    return CorpusAcquisitionRuntimeMetadata(
        configured_batch_size=runtime.configured_batch_size,
        final_batch_size=runtime.final_batch_size,
        min_batch_size=runtime.min_batch_size,
        configured_concurrency=runtime.configured_concurrency,
        final_concurrency=runtime.final_concurrency,
        concurrency_rungs=tuple(runtime.concurrency_rungs),
        oversize_error_count=runtime.oversize_error_count,
        transient_error_count=runtime.transient_error_count,
        oversize_backoffs=runtime.oversize_backoffs,
        transient_backoffs=runtime.transient_backoffs,
        concurrency_recoveries=runtime.concurrency_recoveries,
    )


def build_dataset_manifest(
    *,
    config: AcquireConfig,
    corpus_id: str,
    blocks_plan: BlockPullPlan,
    blocks_validation: BlockDatasetValidationReport,
    blocks_outcome: SplitMaterializationOutcomeValue,
    blocks_file_count: int,
    source_requirements: CorpusAcquisitionSourceRequirements,
) -> CorpusManifest:
    return CorpusManifest(
        corpus=CorpusIdentity(
            id=corpus_id,
            name=config.corpus.name,
        ),
        chain=ChainMetadata(
            name=config.chain.name,
            runtime=config.chain.runtime,
        ),
        blocks=split_manifest(
            kind="blocks",
            plan=blocks_plan,
            validation=blocks_validation,
            outcome=blocks_outcome,
            file_count=blocks_file_count,
        ),
        source_requirements=source_requirements,
    )


def build_acquire_run_record(
    *,
    config: AcquireConfig,
    provider: ProviderMetadata,
    acquisition_runtime: AcquisitionRuntimeSnapshot,
    requested_window_seconds: int,
) -> AcquireRunRecord:
    return AcquireRunRecord(
        provider=provider,
        settings=acquisition_settings(config),
        runtime=acquisition_runtime_metadata(acquisition_runtime),
        facts=AcquireRunFacts(
            requested_window_seconds=requested_window_seconds,
        ),
    )
