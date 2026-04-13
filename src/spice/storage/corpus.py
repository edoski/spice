"""Corpus-root SQLAlchemy persistence."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import cast

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import RowMapping

from ..corpus.metadata import (
    AcquireRunRecord,
    AcquisitionConfigSnapshot,
    BlockRangeMetadata,
    ChainMetadata,
    CompactValidationReport,
    DatasetAcquisitionRuntimeMetadata,
    DatasetCoverageMetadata,
    DatasetIdentity,
    DatasetRequestMetadata,
    DatasetSummary,
    DatasetValidationMetadata,
    DatasetWindowMetadata,
    ProblemContractSnapshot,
    ProviderMetadata,
    TimestampRangeMetadata,
)
from .engine import DATASET_ROOT_KIND, create_state_engine, ensure_state_db, touch_meta
from .schema import DATASET_TABLES, acquire_runs, dataset_summary


def write_dataset_state(
    db_path: Path,
    *,
    summary: DatasetSummary,
    acquire_run: AcquireRunRecord,
) -> None:
    ensure_state_db(db_path, root_kind=DATASET_ROOT_KIND, tables=DATASET_TABLES)
    engine = create_state_engine(db_path)
    try:
        with engine.begin() as conn:
            summary_values = {
                "singleton": 1,
                "dataset_id": summary.dataset.id,
                "dataset_name": summary.dataset.name,
                "chain_name": summary.chain.name,
                "chain_id": summary.chain.chain_id,
                "provider_name": summary.provider.name,
                "provider_reference": summary.provider.reference,
                "provider_endpoint_fingerprint": summary.provider.endpoint_fingerprint,
                "history_request_start_timestamp": summary.request.history.start_timestamp,
                "history_request_end_timestamp": summary.request.history.end_timestamp,
                "evaluation_request_start_timestamp": summary.request.evaluation.start_timestamp,
                "evaluation_request_end_timestamp": summary.request.evaluation.end_timestamp,
                "history_coverage_start_timestamp": summary.coverage.history.start_timestamp,
                "history_coverage_end_timestamp": summary.coverage.history.end_timestamp,
                "evaluation_coverage_start_timestamp": summary.coverage.evaluation.start_timestamp,
                "evaluation_coverage_end_timestamp": summary.coverage.evaluation.end_timestamp,
                "history_validation": _validation_payload(summary.validation.history),
                "evaluation_validation": _validation_payload(summary.validation.evaluation),
            }
            statement = sqlite_insert(dataset_summary).values(**summary_values)
            conn.execute(
                statement.on_conflict_do_update(
                    index_elements=[dataset_summary.c.singleton],
                    set_={
                        key: value
                        for key, value in summary_values.items()
                        if key != "singleton"
                    },
                )
            )
            conn.execute(
                acquire_runs.insert().values(
                    provider_name=acquire_run.provider.name,
                    provider_reference=acquire_run.provider.reference,
                    provider_endpoint_fingerprint=acquire_run.provider.endpoint_fingerprint,
                    problem_id=acquire_run.problem.problem_id,
                    feature_set_id=acquire_run.problem.feature_set_id,
                    lookback_seconds=acquire_run.problem.lookback_seconds,
                    sample_count=acquire_run.problem.sample_count,
                    max_supported_delay_seconds=acquire_run.problem.max_supported_delay_seconds,
                    feature_history_seconds=acquire_run.problem.feature_history_seconds,
                    required_history_seconds=acquire_run.problem.required_history_seconds,
                    acquired_history_window_seconds=acquire_run.problem.acquired_history_window_seconds,
                    valid_anchor_samples=acquire_run.problem.valid_anchor_samples,
                    chunk_size=acquire_run.settings.chunk_size,
                    rpc_batch_size=acquire_run.settings.rpc_batch_size,
                    rpc_concurrency=acquire_run.settings.rpc_concurrency,
                    rpc_min_batch_size=acquire_run.settings.rpc_min_batch_size,
                    rpc_concurrency_rungs=acquire_run.settings.rpc_concurrency_rungs,
                    configured_batch_size=acquire_run.runtime.configured_batch_size,
                    final_batch_size=acquire_run.runtime.final_batch_size,
                    min_batch_size=acquire_run.runtime.min_batch_size,
                    configured_concurrency=acquire_run.runtime.configured_concurrency,
                    final_concurrency=acquire_run.runtime.final_concurrency,
                    concurrency_rungs=acquire_run.runtime.concurrency_rungs,
                    oversize_error_count=acquire_run.runtime.oversize_error_count,
                    transient_error_count=acquire_run.runtime.transient_error_count,
                    oversize_backoffs=acquire_run.runtime.oversize_backoffs,
                    transient_backoffs=acquire_run.runtime.transient_backoffs,
                    concurrency_recoveries=acquire_run.runtime.concurrency_recoveries,
                    recorded_at=_now_timestamp(),
                )
            )
            touch_meta(conn, root_kind=DATASET_ROOT_KIND)
    finally:
        engine.dispose()


def load_dataset_summary(db_path: Path) -> DatasetSummary:
    engine = create_state_engine(db_path)
    try:
        with engine.connect() as conn:
            row = conn.execute(select(dataset_summary)).mappings().first()
        if row is None:
            raise ValueError(f"Missing dataset summary: {db_path}")
        return DatasetSummary(
            dataset=DatasetIdentity(
                id=_row_str(row, "dataset_id"),
                name=_row_str(row, "dataset_name"),
            ),
            chain=ChainMetadata(
                name=_row_str(row, "chain_name"),
                chain_id=_row_int(row, "chain_id"),
            ),
            provider=ProviderMetadata(
                name=_row_str(row, "provider_name"),
                reference=_row_str(row, "provider_reference"),
                endpoint_fingerprint=_row_str(row, "provider_endpoint_fingerprint"),
            ),
            request=DatasetRequestMetadata(
                history=DatasetWindowMetadata(
                    start_timestamp=_row_int(row, "history_request_start_timestamp"),
                    end_timestamp=_row_int(row, "history_request_end_timestamp"),
                ),
                evaluation=DatasetWindowMetadata(
                    start_timestamp=_row_int(row, "evaluation_request_start_timestamp"),
                    end_timestamp=_row_int(row, "evaluation_request_end_timestamp"),
                ),
            ),
            coverage=DatasetCoverageMetadata(
                history=DatasetWindowMetadata(
                    start_timestamp=_row_int(row, "history_coverage_start_timestamp"),
                    end_timestamp=_row_int(row, "history_coverage_end_timestamp"),
                ),
                evaluation=DatasetWindowMetadata(
                    start_timestamp=_row_int(row, "evaluation_coverage_start_timestamp"),
                    end_timestamp=_row_int(row, "evaluation_coverage_end_timestamp"),
                ),
            ),
            validation=DatasetValidationMetadata(
                history=_validation_from_payload(row["history_validation"]),
                evaluation=_validation_from_payload(row["evaluation_validation"]),
            ),
        )
    finally:
        engine.dispose()


def list_acquire_runs(db_path: Path) -> list[AcquireRunRecord]:
    engine = create_state_engine(db_path)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                select(acquire_runs).order_by(acquire_runs.c.run_id.desc())
            ).mappings().all()
        return [_acquire_run_from_row(row) for row in rows]
    finally:
        engine.dispose()


def _validation_payload(report: CompactValidationReport) -> dict[str, object]:
    return asdict(report)


def _validation_from_payload(payload: object) -> CompactValidationReport:
    if not isinstance(payload, dict):
        raise TypeError("Validation payload must be a mapping")
    block_range = cast(dict[str, object], payload["block_range"])
    timestamp_range = cast(dict[str, object], payload["timestamp_range"])
    if not isinstance(block_range, dict) or not isinstance(timestamp_range, dict):
        raise TypeError("Validation payload ranges must be mappings")
    return CompactValidationReport(
        status=str(payload["status"]),
        rows=_int_value(payload["rows"]),
        block_range=BlockRangeMetadata(
            first=_optional_int(block_range.get("first")),
            last=_optional_int(block_range.get("last")),
        ),
        timestamp_range=TimestampRangeMetadata(
            first=_optional_int(timestamp_range.get("first")),
            last=_optional_int(timestamp_range.get("last")),
        ),
        issues=_issues_payload(payload.get("issues")),
    )


def _issues_payload(payload: object) -> dict[str, object] | None:
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise TypeError("Validation issues payload must be a mapping")
    return dict(payload)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return _int_value(value)


def _int_value(value: object) -> int:
    return int(cast(int | float | str | bytes, value))


def _int_list_value(values: object) -> list[int]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise TypeError("Expected list payload")
    return [_int_value(value) for value in values]


def _row_value(row: RowMapping, key: str) -> object:
    return row[key]


def _row_str(row: RowMapping, key: str) -> str:
    return str(_row_value(row, key))


def _row_int(row: RowMapping, key: str) -> int:
    return _int_value(_row_value(row, key))


def _now_timestamp() -> int:
    from time import time

    return int(time())


def _acquire_run_from_row(row: RowMapping) -> AcquireRunRecord:
    return AcquireRunRecord(
        provider=ProviderMetadata(
            name=_row_str(row, "provider_name"),
            reference=_row_str(row, "provider_reference"),
            endpoint_fingerprint=_row_str(row, "provider_endpoint_fingerprint"),
        ),
        problem=ProblemContractSnapshot(
            problem_id=_row_str(row, "problem_id"),
            feature_set_id=_row_str(row, "feature_set_id"),
            lookback_seconds=_row_int(row, "lookback_seconds"),
            sample_count=_row_int(row, "sample_count"),
            max_supported_delay_seconds=_row_int(row, "max_supported_delay_seconds"),
            feature_history_seconds=_row_int(row, "feature_history_seconds"),
            required_history_seconds=_row_int(row, "required_history_seconds"),
            acquired_history_window_seconds=_row_int(row, "acquired_history_window_seconds"),
            valid_anchor_samples=_row_int(row, "valid_anchor_samples"),
        ),
        settings=AcquisitionConfigSnapshot(
            chunk_size=_row_int(row, "chunk_size"),
            rpc_batch_size=_row_int(row, "rpc_batch_size"),
            rpc_concurrency=_row_int(row, "rpc_concurrency"),
            rpc_min_batch_size=_row_int(row, "rpc_min_batch_size"),
            rpc_concurrency_rungs=_int_list_value(_row_value(row, "rpc_concurrency_rungs")),
        ),
        runtime=DatasetAcquisitionRuntimeMetadata(
            configured_batch_size=_row_int(row, "configured_batch_size"),
            final_batch_size=_row_int(row, "final_batch_size"),
            min_batch_size=_row_int(row, "min_batch_size"),
            configured_concurrency=_row_int(row, "configured_concurrency"),
            final_concurrency=_row_int(row, "final_concurrency"),
            concurrency_rungs=_int_list_value(_row_value(row, "concurrency_rungs")),
            oversize_error_count=_row_int(row, "oversize_error_count"),
            transient_error_count=_row_int(row, "transient_error_count"),
            oversize_backoffs=_row_int(row, "oversize_backoffs"),
            transient_backoffs=_row_int(row, "transient_backoffs"),
            concurrency_recoveries=_row_int(row, "concurrency_recoveries"),
        ),
    )
