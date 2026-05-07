"""Storage transfer transaction orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from ..storage.catalog.codecs import decode_remote_catalog_record
from ..storage.catalog.index import ReindexedCatalogRoot, resolve_catalog_record_by_id
from ..storage.catalog.materialization import materialize_catalog_root
from ..storage.catalog.records import CatalogRecord
from ..storage.engine import RootKind
from ..storage.lifecycle import (
    cleanup_root_stage,
    prepare_root_stage,
    promote_root_stage,
    staged_root_path,
)
from .session import ExecutionSession, open_execution_session


@dataclass(frozen=True, slots=True)
class TransferredRoot:
    root_kind: RootKind
    source_record: CatalogRecord
    destination_record: CatalogRecord
    source_root: Path
    destination_root: Path


class TransferAdapter(Protocol):
    def prepare_stage(
        self,
        *,
        destination_root: Path,
        replace: bool,
    ) -> Path: ...

    def promote_stage(
        self,
        *,
        destination_root: Path,
        staged_root: Path,
        root_kind: RootKind,
        replace: bool,
    ) -> ReindexedCatalogRoot: ...

    def cleanup_stage(self, staged_root: Path) -> None: ...


@dataclass(frozen=True, slots=True)
class LocalStorageTransferAdapter:
    storage_root: Path

    def prepare_stage(
        self,
        *,
        destination_root: Path,
        replace: bool,
    ) -> Path:
        return prepare_root_stage(
            destination_root=destination_root,
            replace=replace,
            purpose="incoming",
        )

    def promote_stage(
        self,
        *,
        destination_root: Path,
        staged_root: Path,
        root_kind: RootKind,
        replace: bool,
    ) -> ReindexedCatalogRoot:
        return promote_root_stage(
            storage_root=self.storage_root,
            destination_root=destination_root,
            staged_root=staged_root,
            expected_root_kind=root_kind,
            replace=replace,
        )

    def cleanup_stage(self, staged_root: Path) -> None:
        cleanup_root_stage(staged_root)


@dataclass(frozen=True, slots=True)
class RemoteStorageTransferAdapter:
    session: ExecutionSession

    @property
    def storage_root(self) -> Path:
        return self.session.target.spec.paths.storage_root

    def prepare_stage(
        self,
        *,
        destination_root: Path,
        replace: bool,
    ) -> Path:
        staged_root = staged_root_path(destination_root, purpose="incoming")
        self.session.run_module(
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
        return staged_root

    def promote_stage(
        self,
        *,
        destination_root: Path,
        staged_root: Path,
        root_kind: RootKind,
        replace: bool,
    ) -> ReindexedCatalogRoot:
        result = self.session.run_module(
            "spice.storage.sync_cli",
            [
                "finalize-stage",
                "--storage-root",
                str(self.storage_root),
                "--destination-root",
                str(destination_root),
                "--staged-root",
                str(staged_root),
                "--root-kind",
                root_kind.value,
                *(["--replace"] if replace else []),
            ],
            check_action=f"finalize transfer {destination_root}",
        )
        return ReindexedCatalogRoot(
            root_kind=root_kind,
            record=decode_remote_catalog_record(
                result.stdout,
                expected_root_kind=root_kind,
            ),
        )

    def cleanup_stage(self, staged_root: Path) -> None:
        self.session.run_module(
            "spice.storage.sync_cli",
            ["cleanup-stage", "--staged-root", str(staged_root)],
            check_action=f"cleanup stage {staged_root}",
        )

    def resolve_record(
        self,
        *,
        root_kind: RootKind,
        root_id: str,
    ) -> CatalogRecord:
        result = self.session.run_module(
            "spice.storage.sync_cli",
            [
                "resolve-record",
                "--storage-root",
                str(self.storage_root),
                "--root-kind",
                root_kind.value,
                "--root-id",
                root_id,
            ],
            check_action=f"resolve {root_kind.value} {root_id}",
        )
        return decode_remote_catalog_record(
            result.stdout,
            expected_root_kind=root_kind,
        )


@dataclass(slots=True)
class StorageTransferTransaction:
    local_storage_root: Path
    session: ExecutionSession
    _remote_adapter: RemoteStorageTransferAdapter = field(init=False)
    _local_adapter: LocalStorageTransferAdapter = field(init=False)
    _pull_cache: dict[tuple[RootKind, str], TransferredRoot] = field(
        default_factory=dict,
        init=False,
    )

    def __post_init__(self) -> None:
        self._remote_adapter = RemoteStorageTransferAdapter(self.session)
        self._local_adapter = LocalStorageTransferAdapter(self.local_storage_root)

    def push_root(
        self,
        root_kind: RootKind,
        root_id: str,
        *,
        replace: bool = False,
    ) -> TransferredRoot:
        record = resolve_catalog_record_by_id(
            self.local_storage_root,
            root_kind=root_kind,
            root_id=root_id,
        )
        source = materialize_catalog_root(self.local_storage_root, record)
        destination = materialize_catalog_root(
            self._remote_adapter.storage_root,
            record,
        )
        promoted = _execute_transfer(
            adapter=self._remote_adapter,
            destination_root=destination.root_path,
            root_kind=root_kind,
            replace=replace,
            rsync=lambda staged_root: self.session.rsync_to(
                source_root=source.root_path,
                destination_root=staged_root,
            ),
        )
        return TransferredRoot(
            root_kind=root_kind,
            source_record=record,
            destination_record=promoted.record,
            source_root=source.root_path,
            destination_root=destination.root_path,
        )

    def pull_root(
        self,
        root_kind: RootKind,
        root_id: str,
        *,
        replace: bool = True,
    ) -> TransferredRoot:
        cache_key = (root_kind, root_id)
        cached = self._pull_cache.get(cache_key)
        if cached is not None:
            return cached
        source_record = self._remote_adapter.resolve_record(
            root_kind=root_kind,
            root_id=root_id,
        )
        source = materialize_catalog_root(self._remote_adapter.storage_root, source_record)
        destination = materialize_catalog_root(self.local_storage_root, source_record)
        promoted = _execute_transfer(
            adapter=self._local_adapter,
            destination_root=destination.root_path,
            root_kind=root_kind,
            replace=replace,
            rsync=lambda staged_root: self.session.rsync_from(
                source_root=source.root_path,
                destination_root=staged_root,
            ),
        )
        transferred = TransferredRoot(
            root_kind=root_kind,
            source_record=source_record,
            destination_record=promoted.record,
            source_root=source.root_path,
            destination_root=destination.root_path,
        )
        self._pull_cache[cache_key] = transferred
        return transferred


def open_storage_transfer_transaction(
    target_name: str,
    *,
    local_storage_root: Path,
) -> StorageTransferTransaction:
    return StorageTransferTransaction(
        local_storage_root=local_storage_root,
        session=open_execution_session(target_name),
    )


def _execute_transfer(
    *,
    adapter: TransferAdapter,
    destination_root: Path,
    root_kind: RootKind,
    replace: bool,
    rsync: Callable[[Path], None],
) -> ReindexedCatalogRoot:
    staged_root = adapter.prepare_stage(
        destination_root=destination_root,
        replace=replace,
    )
    try:
        rsync(staged_root)
        return adapter.promote_stage(
            destination_root=destination_root,
            staged_root=staged_root,
            root_kind=root_kind,
            replace=replace,
        )
    except Exception as exc:
        _cleanup_preserving_primary(adapter, staged_root, exc)
        raise


def _cleanup_preserving_primary(
    adapter: TransferAdapter,
    staged_root: Path,
    primary: BaseException,
) -> None:
    try:
        adapter.cleanup_stage(staged_root)
    except Exception as cleanup_error:
        primary.add_note(f"cleanup failed: {cleanup_error}")
