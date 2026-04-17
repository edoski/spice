"""Remote storage transfer helpers."""

from __future__ import annotations

import json
import shlex
from pathlib import Path
from uuid import uuid4

from ..core.errors import SpiceOperatorError, StateConflictError
from ..core.files import promote_paths_atomic, remove_path
from ..storage.catalog import CatalogArtifactRecord, CatalogDatasetRecord, CatalogStudyRecord
from ..storage.query import (
    ArtifactSelector,
    DatasetSelector,
    StudySelector,
    resolve_dataset_record,
    resolve_study_record,
)
from ..storage.reindex import reindex_root
from .shell import (
    RemoteExecutionTarget,
    ensure_remote_success,
    resolve_remote_target,
    run_remote_command,
    run_remote_python_snippet,
    run_rsync_from_remote,
    run_rsync_to_remote,
)


def push_dataset_to_remote(
    *,
    storage_root: Path,
    selector: DatasetSelector,
    replace: bool,
) -> CatalogDatasetRecord:
    target = resolve_remote_target()
    record = resolve_dataset_record(storage_root, selector=selector)
    _push_root_to_remote(
        local_root=record.root_path,
        remote_storage_root=target.spec.paths.storage_root,
        destination_root=_remote_dataset_root(target.spec.paths.storage_root, record),
        replace=replace,
        target=target,
    )
    return record


def push_study_to_remote(
    *,
    storage_root: Path,
    selector: StudySelector,
    replace: bool,
) -> CatalogStudyRecord:
    target = resolve_remote_target()
    record = resolve_study_record(storage_root, selector=selector)
    _push_root_to_remote(
        local_root=record.root_path,
        remote_storage_root=target.spec.paths.storage_root,
        destination_root=_remote_study_root(target.spec.paths.storage_root, record),
        replace=replace,
        target=target,
    )
    return record


def pull_artifact_from_remote(
    *,
    storage_root: Path,
    selector: ArtifactSelector,
    replace: bool,
) -> tuple[CatalogArtifactRecord, bool]:
    target = resolve_remote_target()
    record = _resolve_remote_artifact_record(target, selector=selector)
    destination_root = _local_artifact_root(storage_root, record)
    _pull_root_from_remote(
        target=target,
        remote_root=record.root_path,
        local_storage_root=storage_root,
        destination_root=destination_root,
        replace=replace,
    )
    dataset_present = _local_dataset_root(storage_root, record).exists()
    return record, dataset_present


def pull_study_from_remote(
    *,
    storage_root: Path,
    selector: StudySelector,
    replace: bool,
) -> CatalogStudyRecord:
    target = resolve_remote_target()
    record = _resolve_remote_study_record(target, selector=selector)
    _pull_root_from_remote(
        target=target,
        remote_root=record.root_path,
        local_storage_root=storage_root,
        destination_root=_local_study_root(storage_root, record),
        replace=replace,
    )
    return record


def _push_root_to_remote(
    *,
    local_root: Path,
    remote_storage_root: Path,
    destination_root: Path,
    replace: bool,
    target: RemoteExecutionTarget,
) -> None:
    staged_root = destination_root.parent / f".{destination_root.name}.incoming.{uuid4().hex}"
    try:
        _prepare_remote_stage(
            target,
            destination_root=destination_root,
            staged_root=staged_root,
            replace=replace,
        )
        run_rsync_to_remote(target, source_root=local_root, destination_root=staged_root)
        _finalize_remote_stage(
            target,
            remote_storage_root=remote_storage_root,
            destination_root=destination_root,
            staged_root=staged_root,
            replace=replace,
        )
    except Exception:
        _cleanup_remote_path(target, staged_root)
        raise


def _pull_root_from_remote(
    *,
    target: RemoteExecutionTarget,
    remote_root: Path,
    local_storage_root: Path,
    destination_root: Path,
    replace: bool,
) -> None:
    staged_root = destination_root.parent / f".{destination_root.name}.incoming.{uuid4().hex}"
    if destination_root.exists() and not replace:
        raise StateConflictError(f"Destination already exists: {destination_root}")
    staged_root.parent.mkdir(parents=True, exist_ok=True)
    remove_path(staged_root)
    staged_root.mkdir(parents=True, exist_ok=True)
    try:
        run_rsync_from_remote(target, source_root=remote_root, destination_root=staged_root)
        promote_paths_atomic([(destination_root, staged_root)])
        reindex_root(local_storage_root, root_path=destination_root)
    except Exception:
        remove_path(staged_root)
        raise


def _prepare_remote_stage(
    target: RemoteExecutionTarget,
    *,
    destination_root: Path,
    staged_root: Path,
    replace: bool,
) -> None:
    code = "\n".join(
        [
            "from pathlib import Path",
            "from spice.core.errors import StateConflictError",
            f"destination_root = Path({str(destination_root)!r})",
            f"staged_root = Path({str(staged_root)!r})",
            f"replace = {replace!r}",
            "if destination_root.exists() and not replace:",
            "    raise StateConflictError(f'Destination already exists: {destination_root}')",
            "staged_root.parent.mkdir(parents=True, exist_ok=True)",
            "if staged_root.exists():",
            "    import shutil",
            "    shutil.rmtree(staged_root)",
            "staged_root.mkdir(parents=True, exist_ok=True)",
        ]
    )
    ensure_remote_success(
        run_remote_python_snippet(target, _wrap_python_snippet(code)),
        action=f"prepare remote stage {destination_root}",
    )


def _finalize_remote_stage(
    target: RemoteExecutionTarget,
    *,
    remote_storage_root: Path,
    destination_root: Path,
    staged_root: Path,
    replace: bool,
) -> None:
    code = "\n".join(
        [
            "from pathlib import Path",
            "from spice.core.errors import StateConflictError",
            "from spice.core.files import promote_paths_atomic",
            "from spice.storage.reindex import reindex_root",
            f"storage_root = Path({str(remote_storage_root)!r})",
            f"destination_root = Path({str(destination_root)!r})",
            f"staged_root = Path({str(staged_root)!r})",
            f"replace = {replace!r}",
            "if destination_root.exists() and not replace:",
            "    raise StateConflictError(f'Destination already exists: {destination_root}')",
            "promote_paths_atomic([(destination_root, staged_root)])",
            "reindex_root(storage_root, root_path=destination_root)",
        ]
    )
    ensure_remote_success(
        run_remote_python_snippet(target, _wrap_python_snippet(code)),
        action=f"finalize remote transfer {destination_root}",
    )


def _cleanup_remote_path(target: RemoteExecutionTarget, path: Path) -> None:
    run_remote_command(target, f"rm -rf {shlex.quote(path.as_posix())}")


def _resolve_remote_study_record(
    target: RemoteExecutionTarget,
    *,
    selector: StudySelector,
) -> CatalogStudyRecord:
    payload = _resolve_remote_record_payload(
        target,
        selector_type="StudySelector",
        resolve_fn="resolve_study_record",
        selector_payload={
            "chain_name": selector.chain_name,
            "dataset_name": selector.dataset_name,
            "feature_set_id": selector.feature_set_id,
            "prediction_id": selector.prediction_id,
            "model_id": selector.model_id,
            "problem_id": selector.problem_id,
            "study_name": selector.study_name,
        },
    )
    return CatalogStudyRecord(
        study_id=str(payload["study_id"]),
        study_name=str(payload["study_name"]),
        dataset_id=str(payload["dataset_id"]),
        dataset_name=str(payload["dataset_name"]),
        chain_name=str(payload["chain_name"]),
        feature_set_id=str(payload["feature_set_id"]),
        prediction_id=str(payload["prediction_id"]),
        model_id=str(payload["model_id"]),
        problem_id=str(payload["problem_id"]),
        root_path=Path(str(payload["root_path"])),
        state_db_path=Path(str(payload["state_db_path"])),
    )


def _resolve_remote_artifact_record(
    target: RemoteExecutionTarget,
    *,
    selector: ArtifactSelector,
) -> CatalogArtifactRecord:
    payload = _resolve_remote_record_payload(
        target,
        selector_type="ArtifactSelector",
        resolve_fn="resolve_artifact_record",
        selector_payload={
            "chain_name": selector.chain_name,
            "dataset_name": selector.dataset_name,
            "feature_set_id": selector.feature_set_id,
            "prediction_id": selector.prediction_id,
            "model_id": selector.model_id,
            "problem_id": selector.problem_id,
            "variant": selector.variant,
            "study_name": selector.study_name,
        },
    )
    return CatalogArtifactRecord(
        artifact_id=str(payload["artifact_id"]),
        dataset_id=str(payload["dataset_id"]),
        dataset_name=str(payload["dataset_name"]),
        chain_name=str(payload["chain_name"]),
        feature_set_id=str(payload["feature_set_id"]),
        prediction_id=str(payload["prediction_id"]),
        model_id=str(payload["model_id"]),
        problem_id=str(payload["problem_id"]),
        variant=str(payload["variant"]),
        study_id=None if payload["study_id"] is None else str(payload["study_id"]),
        study_name=None if payload["study_name"] is None else str(payload["study_name"]),
        root_path=Path(str(payload["root_path"])),
        state_db_path=Path(str(payload["state_db_path"])),
    )


def _resolve_remote_record_payload(
    target: RemoteExecutionTarget,
    *,
    selector_type: str,
    resolve_fn: str,
    selector_payload: dict[str, object | None],
) -> dict[str, object | None]:
    code = "\n".join(
        [
            "from pathlib import Path",
            "import json",
            (
                "from spice.storage.query import "
                f"{selector_type}, {resolve_fn}"
            ),
            f"storage_root = Path({str(target.spec.paths.storage_root)!r})",
            f"selector_payload = json.loads({json.dumps(selector_payload)!r})",
            f"record = {resolve_fn}(storage_root, selector={selector_type}(**selector_payload))",
            "from dataclasses import asdict",
            "payload = asdict(record)",
            "print(json.dumps({key: (str(value) if isinstance(value, Path) else value) "
            "for key, value in payload.items()}))",
        ]
    )
    result = ensure_remote_success(
        run_remote_python_snippet(target, _wrap_python_snippet(code)),
        action=f"resolve remote {selector_type}",
    )
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise SpiceOperatorError("remote selector payload must be a mapping")
    return payload


def _wrap_python_snippet(code: str) -> str:
    return "\n".join(
        [
            "try:",
            *(f"    {line}" for line in code.splitlines()),
            "except Exception as exc:",
            "    raise SystemExit(str(exc)) from exc",
            "",
        ]
    )


def _remote_dataset_root(remote_storage_root: Path, record: CatalogDatasetRecord) -> Path:
    return remote_storage_root / "corpora" / record.chain_name / record.dataset_id


def _remote_study_root(remote_storage_root: Path, record: CatalogStudyRecord) -> Path:
    return remote_storage_root / "studies" / record.chain_name / record.study_id


def _local_study_root(storage_root: Path, record: CatalogStudyRecord) -> Path:
    return storage_root / "studies" / record.chain_name / record.study_id


def _local_artifact_root(storage_root: Path, record: CatalogArtifactRecord) -> Path:
    return storage_root / "artifacts" / record.chain_name / record.artifact_id


def _local_dataset_root(storage_root: Path, record: CatalogArtifactRecord) -> Path:
    return storage_root / "corpora" / record.chain_name / record.dataset_id
