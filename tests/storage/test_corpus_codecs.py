from __future__ import annotations

from copy import deepcopy
from typing import cast

import pytest

from spice.config.models import ChainRuntimeSpec
from spice.core.errors import StateLayoutError
from spice.corpus.metadata import (
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
from spice.storage.corpus_codecs import (
    acquire_run_from_payload,
    acquire_run_payload,
    dataset_manifest_from_payload,
    dataset_manifest_payload,
)


def _validation_report() -> CompactValidationReport:
    return CompactValidationReport(
        status="ok",
        rows=12,
        block_range=BlockRangeMetadata(first=100, last=111),
        timestamp_range=TimestampRangeMetadata(first=1_000, last=1_132),
        issues=None,
    )


def _dataset_manifest() -> DatasetManifest:
    history = DatasetWindowMetadata(start_timestamp=1_000, end_timestamp=1_132)
    evaluation = DatasetWindowMetadata(start_timestamp=1_144, end_timestamp=1_276)
    return DatasetManifest(
        dataset=DatasetIdentity(id="cor_test", name="icdcs_2026"),
        chain=ChainMetadata(
            name="ethereum",
            runtime=ChainRuntimeSpec(
                chain_id=1,
                uses_poa_extra_data=False,
                nominal_block_time_seconds=12.0,
            ),
        ),
        request=DatasetRequestMetadata(history=history, evaluation=evaluation),
        coverage=DatasetCoverageMetadata(history=history, evaluation=evaluation),
        validation=DatasetValidationMetadata(
            history=_validation_report(),
            evaluation=_validation_report(),
        ),
    )


def _acquire_run() -> AcquireRunRecord:
    return AcquireRunRecord(
        provider=ProviderMetadata(
            name="publicnode",
            reference="ethereum",
            endpoint_fingerprint="abcdef0123456789",
        ),
        facts=AcquireRunFacts(
            requested_history_window_seconds=86400,
            resolved_capability_samples=1000,
        ),
        settings=AcquisitionConfigSnapshot(
            chunk_size=5000,
            rpc_batch_size=100,
            rpc_concurrency=8,
            rpc_min_batch_size=10,
            rpc_concurrency_rungs=[8, 4, 2],
        ),
        runtime=DatasetAcquisitionRuntimeMetadata(
            configured_batch_size=100,
            final_batch_size=50,
            min_batch_size=10,
            configured_concurrency=8,
            final_concurrency=4,
            concurrency_rungs=[8, 4, 2],
            oversize_error_count=1,
            transient_error_count=2,
            oversize_backoffs=3,
            transient_backoffs=4,
            concurrency_recoveries=5,
        ),
    )


def test_dataset_manifest_payload_round_trips() -> None:
    manifest = _dataset_manifest()

    assert dataset_manifest_from_payload(dataset_manifest_payload(manifest)) == manifest


def test_dataset_manifest_payload_rejects_extra_and_loose_scalars() -> None:
    payload = dataset_manifest_payload(_dataset_manifest())
    payload["extra"] = "nope"

    with pytest.raises(StateLayoutError, match="Invalid dataset manifest payload"):
        dataset_manifest_from_payload(payload)

    payload = dataset_manifest_payload(_dataset_manifest())
    history = cast(dict[str, object], cast(dict[str, object], payload["request"])["history"])
    history["start_timestamp"] = "1000"

    with pytest.raises(StateLayoutError, match="Invalid dataset manifest payload"):
        dataset_manifest_from_payload(payload)


def test_dataset_manifest_payload_rejects_non_string_validation_status() -> None:
    payload = dataset_manifest_payload(_dataset_manifest())
    validation = cast(dict[str, object], payload["validation"])
    history = cast(dict[str, object], validation["history"])
    history["status"] = True

    with pytest.raises(StateLayoutError, match="Invalid dataset manifest payload"):
        dataset_manifest_from_payload(payload)


def test_acquire_run_payload_round_trips() -> None:
    run = _acquire_run()

    assert acquire_run_from_payload(acquire_run_payload(run)) == run


def test_acquire_run_payload_rejects_extra_and_loose_scalars() -> None:
    payload = acquire_run_payload(_acquire_run())
    settings = cast(dict[str, object], payload["settings"])
    settings["rpc_batch_size"] = "100"

    with pytest.raises(StateLayoutError, match="Invalid acquire run payload"):
        acquire_run_from_payload(payload)

    payload = deepcopy(acquire_run_payload(_acquire_run()))
    runtime = cast(dict[str, object], payload["runtime"])
    runtime["extra"] = "nope"

    with pytest.raises(StateLayoutError, match="Invalid acquire run payload"):
        acquire_run_from_payload(payload)
