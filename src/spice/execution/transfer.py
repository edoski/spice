"""Remote storage transfer orchestration."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import fields
from pathlib import Path
from typing import Any, TypeVar, cast

from ..core.errors import SpiceOperatorError
from ..storage.catalog import CatalogArtifactRecord, CatalogDatasetRecord, CatalogStudyRecord
from ..storage.catalog.index import (
    resolve_dataset_record,
    resolve_study_record,
)
from ..storage.engine import ARTIFACT_ROOT_KIND, DATASET_ROOT_KIND, STUDY_ROOT_KIND, RootKind
from ..storage.layout import artifact_root_path, corpus_root_path, study_root_path
from ..storage.lifecycle import (
    cleanup_root_stage,
    prepare_root_stage,
    promote_root_stage,
    staged_root_path,
)
from ..storage.selectors import DatasetSelector, StudySelector
from .session import (
    ExecutionSession,
    ExecutionTarget,
)

RecordT = TypeVar("RecordT", CatalogDatasetRecord, CatalogStudyRecord)
RemoteRecordT = TypeVar("RemoteRecordT", CatalogStudyRecord, CatalogArtifactRecord)


def push_dataset_to_cluster(
    *,
    storage_root: Path,
    session: ExecutionSession,
    dataset_id: str,
    replace: bool,
) -> CatalogDatasetRecord:
    return _push_record_to_cluster(
        storage_root=storage_root,
        selector=DatasetSelector(dataset_id=dataset_id),
        resolve_record=lambda root, selected: resolve_dataset_record(
            root,
            selector=cast(DatasetSelector, selected),
        ),
        destination_root=_cluster_dataset_root,
        expected_root_kind=DATASET_ROOT_KIND,
        session=session,
        replace=replace,
    )


def push_study_to_cluster(
    *,
    storage_root: Path,
    session: ExecutionSession,
    study_id: str,
    replace: bool,
) -> CatalogStudyRecord:
    return _push_record_to_cluster(
        storage_root=storage_root,
        selector=StudySelector(study_id=study_id),
        resolve_record=lambda root, selected: resolve_study_record(
            root,
            selector=cast(StudySelector, selected),
        ),
        destination_root=_cluster_study_root,
        expected_root_kind=STUDY_ROOT_KIND,
        session=session,
        replace=replace,
    )


def pull_artifact_from_cluster(
    *,
    storage_root: Path,
    session: ExecutionSession,
    artifact_id: str,
    replace: bool,
) -> tuple[CatalogArtifactRecord, bool]:
    target = session.target
    record = _resolve_cluster_artifact_record(session, artifact_id=artifact_id)
    destination_root = _local_artifact_root(storage_root, record)
    _pull_root_from_cluster(
        session=session,
        target=target,
        cluster_root=record.root_path,
        local_storage_root=storage_root,
        destination_root=destination_root,
        expected_root_kind=ARTIFACT_ROOT_KIND,
        replace=replace,
    )
    dataset_present = _local_dataset_root(storage_root, record).exists()
    return record, dataset_present


def pull_study_from_cluster(
    *,
    storage_root: Path,
    session: ExecutionSession,
    study_id: str,
    replace: bool,
) -> CatalogStudyRecord:
    target = session.target
    record = _resolve_cluster_study_record(session, study_id=study_id)
    _pull_root_from_cluster(
        session=session,
        target=target,
        cluster_root=record.root_path,
        local_storage_root=storage_root,
        destination_root=_local_study_root(storage_root, record),
        expected_root_kind=STUDY_ROOT_KIND,
        replace=replace,
    )
    return record


def _push_root_to_cluster(
    *,
    local_root: Path,
    cluster_storage_root: Path,
    destination_root: Path,
    expected_root_kind: RootKind,
    replace: bool,
    session: ExecutionSession,
    target: ExecutionTarget,
) -> None:
    staged_root = staged_root_path(destination_root, purpose="incoming")
    try:
        _prepare_cluster_stage(
            session,
            destination_root=destination_root,
            staged_root=staged_root,
            replace=replace,
        )
        session.rsync_to(
            source_root=local_root,
            destination_root=staged_root,
        )
        _finalize_cluster_stage(
            session,
            cluster_storage_root=cluster_storage_root,
            destination_root=destination_root,
            staged_root=staged_root,
            expected_root_kind=expected_root_kind,
            replace=replace,
        )
    except Exception:
        _cleanup_cluster_path(session, staged_root)
        raise


def _push_record_to_cluster(
    *,
    storage_root: Path,
    selector: object,
    resolve_record: Callable[[Path, object], RecordT],
    destination_root: Callable[[Path, RecordT], Path],
    expected_root_kind: RootKind,
    session: ExecutionSession,
    replace: bool,
) -> RecordT:
    target = session.target
    record = resolve_record(storage_root, selector)
    _push_root_to_cluster(
        local_root=record.root_path,
        cluster_storage_root=target.spec.paths.storage_root,
        destination_root=destination_root(target.spec.paths.storage_root, record),
        expected_root_kind=expected_root_kind,
        replace=replace,
        session=session,
        target=target,
    )
    return record


def _pull_root_from_cluster(
    *,
    session: ExecutionSession,
    target: ExecutionTarget,
    cluster_root: Path,
    local_storage_root: Path,
    destination_root: Path,
    expected_root_kind: RootKind,
    replace: bool,
) -> None:
    staged_root = prepare_root_stage(
        destination_root=destination_root,
        replace=replace,
        purpose="incoming",
    )
    try:
        session.rsync_from(
            source_root=cluster_root,
            destination_root=staged_root,
        )
        promote_root_stage(
            storage_root=local_storage_root,
            destination_root=destination_root,
            staged_root=staged_root,
            expected_root_kind=expected_root_kind,
            replace=replace,
        )
    except Exception:
        cleanup_root_stage(staged_root)
        raise


def _prepare_cluster_stage(
    session: ExecutionSession,
    *,
    destination_root: Path,
    staged_root: Path,
    replace: bool,
) -> None:
    session.run_module(
        "spice.storage.sync_cli",
        [
            "prepare-stage",
            "--destination-root",
            str(destination_root),
            "--staged-root",
            str(staged_root),
            *(["--replace"] if replace else []),
        ],
        check_action=f"prepare stage {destination_root}",
    )


def _finalize_cluster_stage(
    session: ExecutionSession,
    *,
    cluster_storage_root: Path,
    destination_root: Path,
    staged_root: Path,
    expected_root_kind: RootKind,
    replace: bool,
) -> None:
    session.run_module(
        "spice.storage.sync_cli",
        [
            "finalize-stage",
            "--storage-root",
            str(cluster_storage_root),
            "--destination-root",
            str(destination_root),
            "--staged-root",
            str(staged_root),
            "--expected-root-kind",
            expected_root_kind.value,
            *(["--replace"] if replace else []),
        ],
        check_action=f"finalize transfer {destination_root}",
    )


def _cleanup_cluster_path(session: ExecutionSession, path: Path) -> None:
    session.run_module(
        "spice.storage.sync_cli",
        ["cleanup-stage", "--staged-root", str(path)],
        check_action=f"cleanup stage {path}",
    )


def _resolve_cluster_study_record(
    session: ExecutionSession,
    *,
    study_id: str,
) -> CatalogStudyRecord:
    return _resolve_cluster_record(
        session,
        command="resolve-study-record",
        action_label=f"study {study_id}",
        id_args=["--study-id", study_id],
        record_type=CatalogStudyRecord,
    )


def _resolve_cluster_artifact_record(
    session: ExecutionSession,
    *,
    artifact_id: str,
) -> CatalogArtifactRecord:
    return _resolve_cluster_record(
        session,
        command="resolve-artifact-record",
        action_label=f"artifact {artifact_id}",
        id_args=["--artifact-id", artifact_id],
        record_type=CatalogArtifactRecord,
        nullable_fields=frozenset({"study_id", "study_name"}),
    )


def _resolve_cluster_record(
    session: ExecutionSession,
    *,
    command: str,
    action_label: str,
    id_args: list[str],
    record_type: type[RemoteRecordT],
    nullable_fields: frozenset[str] = frozenset(),
) -> RemoteRecordT:
    payload = _resolve_cluster_record_payload(
        session,
        command=command,
        action_label=action_label,
        id_args=id_args,
    )
    record_payload: dict[str, object] = {}
    for field in fields(record_type):
        value = payload[field.name]
        if field.name in {"root_path", "state_db_path"}:
            record_payload[field.name] = Path(str(value))
        elif field.name in nullable_fields and value is None:
            record_payload[field.name] = None
        else:
            record_payload[field.name] = str(value)
    return cast(RemoteRecordT, record_type(**cast(dict[str, Any], record_payload)))


def _resolve_cluster_record_payload(
    session: ExecutionSession,
    *,
    command: str,
    action_label: str,
    id_args: list[str],
) -> dict[str, object | None]:
    result = session.run_module(
        "spice.storage.sync_cli",
        [
            command,
            "--storage-root",
            str(session.target.spec.paths.storage_root),
            *id_args,
        ],
        check_action=f"resolve {action_label}",
    )
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise SpiceOperatorError("resolved record payload must be a mapping")
    return payload


def _cluster_dataset_root(cluster_storage_root: Path, record: CatalogDatasetRecord) -> Path:
    return corpus_root_path(
        cluster_storage_root,
        chain_name=record.chain_name,
        corpus_id=record.dataset_id,
    )


def _cluster_study_root(cluster_storage_root: Path, record: CatalogStudyRecord) -> Path:
    return study_root_path(
        cluster_storage_root,
        chain_name=record.chain_name,
        study_id=record.study_id,
    )


def _local_study_root(storage_root: Path, record: CatalogStudyRecord) -> Path:
    return study_root_path(storage_root, chain_name=record.chain_name, study_id=record.study_id)


def _local_artifact_root(storage_root: Path, record: CatalogArtifactRecord) -> Path:
    return artifact_root_path(
        storage_root,
        chain_name=record.chain_name,
        artifact_id=record.artifact_id,
    )


def _local_dataset_root(storage_root: Path, record: CatalogArtifactRecord) -> Path:
    return corpus_root_path(storage_root, chain_name=record.chain_name, corpus_id=record.dataset_id)
