# pyright: strict

"""Corpus-root SQLite persistence."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from ..config.models import ChainRuntimeSpec
from ..core.errors import MissingStateError, StateLayoutError
from ..corpus.metadata import (
    AcquireRunFacts,
    AcquireRunRecord,
    AcquisitionConfigSnapshot,
    BlockRangeMetadata,
    ChainMetadata,
    CompactValidationReport,
    DatasetAcquisitionRuntimeMetadata,
    DatasetCoverageMetadata,
    DatasetIdentity,
    DatasetManifest,
    DatasetRequestMetadata,
    DatasetValidationMetadata,
    DatasetWindowMetadata,
    ProviderMetadata,
    TimestampRangeMetadata,
)
from .engine import (
    DATASET_ROOT_KIND,
    create_state_engine,
    ensure_state_db,
    require_root_kind,
    touch_meta,
)
from .payloads import (
    PayloadCodec,
    SequencePayloadStore,
    SingletonPayloadStore,
    decode_payload,
    int_list_payload,
    int_payload,
    mapping_payload,
    optional_int_payload,
    string_payload,
)
from .schema import DATASET_TABLES, acquire_runs, dataset_manifest

_DATASET_MANIFEST_STORE = SingletonPayloadStore(
    table=dataset_manifest,
    codec=PayloadCodec(
        encode=lambda value: _dataset_manifest_payload(value),
        decode=lambda payload: _dataset_manifest_from_payload(payload),
    ),
)
_ACQUIRE_RUN_STORE = SequencePayloadStore(
    table=acquire_runs,
    codec=PayloadCodec(
        encode=lambda value: _acquire_run_payload(value),
        decode=lambda payload: _acquire_run_from_payload(payload),
    ),
)


def write_dataset_state(
    db_path: Path,
    *,
    manifest: DatasetManifest,
    acquire_run: AcquireRunRecord,
) -> None:
    """Persist the dataset manifest once and append one acquire-run delta record."""

    ensure_state_db(db_path, root_kind=DATASET_ROOT_KIND, tables=DATASET_TABLES)
    engine = create_state_engine(db_path)
    try:
        with engine.begin() as conn:
            _DATASET_MANIFEST_STORE.upsert(conn, manifest)
            _ACQUIRE_RUN_STORE.append(conn, acquire_run, recorded_at=_now_timestamp())
            touch_meta(conn, root_kind=DATASET_ROOT_KIND)
    finally:
        engine.dispose()


def load_dataset_manifest(db_path: Path) -> DatasetManifest:
    """Load the canonical dataset manifest that owns corpus provenance."""

    if not db_path.is_file():
        raise MissingStateError(f"Missing dataset manifest: {db_path}")
    require_root_kind(db_path, DATASET_ROOT_KIND)
    engine = create_state_engine(db_path)
    try:
        with engine.connect() as conn:
            manifest = _DATASET_MANIFEST_STORE.load(conn)
        if manifest is None:
            raise MissingStateError(f"Missing dataset manifest: {db_path}")
        return manifest
    finally:
        engine.dispose()


def list_acquire_runs(db_path: Path) -> list[AcquireRunRecord]:
    """List acquire-run deltas newest first without duplicating manifest provenance."""

    if not db_path.is_file():
        return []
    require_root_kind(db_path, DATASET_ROOT_KIND)
    engine = create_state_engine(db_path)
    try:
        with engine.connect() as conn:
            return _ACQUIRE_RUN_STORE.list(conn, order_by=acquire_runs.c.run_id.desc())
    finally:
        engine.dispose()


def _dataset_manifest_payload(manifest: DatasetManifest) -> dict[str, object]:
    return {
        "dataset": {"id": manifest.dataset.id, "name": manifest.dataset.name},
        "chain": {
            "name": manifest.chain.name,
            "runtime": manifest.chain.runtime.model_dump(mode="json"),
        },
        "request": {
            "history": asdict(manifest.request.history),
            "evaluation": asdict(manifest.request.evaluation),
        },
        "coverage": {
            "history": asdict(manifest.coverage.history),
            "evaluation": asdict(manifest.coverage.evaluation),
        },
        "validation": {
            "history": _validation_payload(manifest.validation.history),
            "evaluation": _validation_payload(manifest.validation.evaluation),
        },
    }


def _dataset_manifest_from_payload(payload: dict[str, object]) -> DatasetManifest:
    return decode_payload(
        "dataset manifest",
        lambda: _decode_dataset_manifest(payload),
    )


def _decode_dataset_manifest(payload: dict[str, object]) -> DatasetManifest:
    dataset = mapping_payload(payload["dataset"], label="dataset")
    chain = mapping_payload(payload["chain"], label="chain")
    request = mapping_payload(payload["request"], label="request")
    coverage = mapping_payload(payload["coverage"], label="coverage")
    validation = mapping_payload(payload["validation"], label="validation")
    return DatasetManifest(
        dataset=DatasetIdentity(
            id=string_payload(dataset["id"], label="dataset.id"),
            name=string_payload(dataset["name"], label="dataset.name"),
        ),
        chain=ChainMetadata(
            name=string_payload(chain["name"], label="chain.name"),
            runtime=_chain_runtime_from_payload(chain),
        ),
        request=DatasetRequestMetadata(
            history=_window_from_payload(request["history"]),
            evaluation=_window_from_payload(request["evaluation"]),
        ),
        coverage=DatasetCoverageMetadata(
            history=_window_from_payload(coverage["history"]),
            evaluation=_window_from_payload(coverage["evaluation"]),
        ),
        validation=DatasetValidationMetadata(
            history=_validation_from_payload(validation["history"]),
            evaluation=_validation_from_payload(validation["evaluation"]),
        ),
    )


def _chain_runtime_from_payload(chain: dict[str, object]) -> ChainRuntimeSpec:
    runtime_payload = chain.get("runtime")
    if runtime_payload is None:
        raise StateLayoutError("chain.runtime is required")
    return ChainRuntimeSpec.model_validate(
        mapping_payload(runtime_payload, label="chain.runtime")
    )


def _window_from_payload(payload: object) -> DatasetWindowMetadata:
    mapping = mapping_payload(payload, label="window")
    return DatasetWindowMetadata(
        start_timestamp=int_payload(mapping["start_timestamp"], label="window.start_timestamp"),
        end_timestamp=int_payload(mapping["end_timestamp"], label="window.end_timestamp"),
    )


def _acquire_run_payload(run: AcquireRunRecord) -> dict[str, object]:
    return {
        "provider": {
            "name": run.provider.name,
            "reference": run.provider.reference,
            "endpoint_fingerprint": run.provider.endpoint_fingerprint,
        },
        "facts": {
            "requested_history_window_seconds": run.facts.requested_history_window_seconds,
            "resolved_capability_samples": run.facts.resolved_capability_samples,
        },
        "settings": asdict(run.settings),
        "runtime": asdict(run.runtime),
    }


def _acquire_run_from_payload(payload: dict[str, object]) -> AcquireRunRecord:
    return decode_payload("acquire run", lambda: _decode_acquire_run(payload))


def _decode_acquire_run(payload: dict[str, object]) -> AcquireRunRecord:
    provider = mapping_payload(payload["provider"], label="provider")
    facts = mapping_payload(payload["facts"], label="facts")
    settings = mapping_payload(payload["settings"], label="settings")
    runtime = mapping_payload(payload["runtime"], label="runtime")
    return AcquireRunRecord(
        provider=ProviderMetadata(
            name=string_payload(provider["name"], label="provider.name"),
            reference=string_payload(provider["reference"], label="provider.reference"),
            endpoint_fingerprint=string_payload(
                provider["endpoint_fingerprint"],
                label="provider.endpoint_fingerprint",
            ),
        ),
        facts=AcquireRunFacts(
            requested_history_window_seconds=int_payload(
                facts["requested_history_window_seconds"],
                label="facts.requested_history_window_seconds",
            ),
            resolved_capability_samples=int_payload(
                facts["resolved_capability_samples"],
                label="facts.resolved_capability_samples",
            ),
        ),
        settings=AcquisitionConfigSnapshot(
            chunk_size=int_payload(settings["chunk_size"], label="settings.chunk_size"),
            rpc_batch_size=int_payload(
                settings["rpc_batch_size"], label="settings.rpc_batch_size"
            ),
            rpc_concurrency=int_payload(
                settings["rpc_concurrency"], label="settings.rpc_concurrency"
            ),
            rpc_min_batch_size=int_payload(
                settings["rpc_min_batch_size"], label="settings.rpc_min_batch_size"
            ),
            rpc_concurrency_rungs=int_list_payload(
                settings["rpc_concurrency_rungs"],
                label="settings.rpc_concurrency_rungs",
            ),
        ),
        runtime=DatasetAcquisitionRuntimeMetadata(
            configured_batch_size=int_payload(
                runtime["configured_batch_size"],
                label="runtime.configured_batch_size",
            ),
            final_batch_size=int_payload(
                runtime["final_batch_size"], label="runtime.final_batch_size"
            ),
            min_batch_size=int_payload(runtime["min_batch_size"], label="runtime.min_batch_size"),
            configured_concurrency=int_payload(
                runtime["configured_concurrency"],
                label="runtime.configured_concurrency",
            ),
            final_concurrency=int_payload(
                runtime["final_concurrency"], label="runtime.final_concurrency"
            ),
            concurrency_rungs=int_list_payload(
                runtime["concurrency_rungs"], label="runtime.concurrency_rungs"
            ),
            oversize_error_count=int_payload(
                runtime["oversize_error_count"], label="runtime.oversize_error_count"
            ),
            transient_error_count=int_payload(
                runtime["transient_error_count"], label="runtime.transient_error_count"
            ),
            oversize_backoffs=int_payload(
                runtime["oversize_backoffs"], label="runtime.oversize_backoffs"
            ),
            transient_backoffs=int_payload(
                runtime["transient_backoffs"], label="runtime.transient_backoffs"
            ),
            concurrency_recoveries=int_payload(
                runtime["concurrency_recoveries"], label="runtime.concurrency_recoveries"
            ),
        ),
    )


def _validation_payload(report: CompactValidationReport) -> dict[str, object]:
    return asdict(report)


def _validation_from_payload(payload: object) -> CompactValidationReport:
    mapping = mapping_payload(payload, label="validation")
    block_range = mapping_payload(mapping["block_range"], label="validation.block_range")
    timestamp_range = mapping_payload(
        mapping["timestamp_range"], label="validation.timestamp_range"
    )
    return CompactValidationReport(
        status=str(mapping["status"]),
        rows=int_payload(mapping["rows"], label="validation.rows"),
        block_range=BlockRangeMetadata(
            first=optional_int_payload(
                block_range.get("first"),
                label="validation.block_range.first",
            ),
            last=optional_int_payload(
                block_range.get("last"),
                label="validation.block_range.last",
            ),
        ),
        timestamp_range=TimestampRangeMetadata(
            first=optional_int_payload(
                timestamp_range.get("first"),
                label="validation.timestamp_range.first",
            ),
            last=optional_int_payload(
                timestamp_range.get("last"),
                label="validation.timestamp_range.last",
            ),
        ),
        issues=_issues_payload(mapping.get("issues")),
    )


def _issues_payload(payload: object) -> dict[str, object] | None:
    if payload is None:
        return None
    return mapping_payload(payload, label="validation.issues")


def _now_timestamp() -> int:
    from time import time

    return int(time())
