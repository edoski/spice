"""Storage-root staging and commit helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from ..core.errors import StateConflictError
from ..core.files import (
    prune_empty_directories,
    remove_path,
    replace_path_atomic,
    replace_paths_atomic,
)
from .engine import RootKind, require_root_kind, state_db_path
from .roots import reindex_root


@dataclass(slots=True)
class RootStage:
    storage_root: Path
    destination_root: Path
    staged_root: Path
    expected_root_kind: RootKind
    replace: bool
    _promoted: bool = False

    def promote(self) -> RootKind:
        root_kind = promote_root_stage(
            storage_root=self.storage_root,
            destination_root=self.destination_root,
            staged_root=self.staged_root,
            expected_root_kind=self.expected_root_kind,
            replace=self.replace,
        )
        self._promoted = True
        return root_kind


@dataclass(slots=True)
class PartialRootCommit:
    storage_root: Path
    root_path: Path
    promotions: list[tuple[Path, Path]] = field(default_factory=list)

    def add(self, target: Path, source: Path | None) -> None:
        if source is not None:
            self.promotions.append((target, source))

    def commit(self) -> RootKind:
        if self.promotions:
            replace_paths_atomic(self.promotions, replace=True)
        return reindex_root(self.storage_root, root_path=self.root_path)


def staged_root_path(destination_root: Path, *, purpose: str = "staging") -> Path:
    return destination_root.parent / f".{destination_root.name}.{purpose}.{uuid4().hex}"


def prepare_root_stage(
    *,
    destination_root: Path,
    staged_root: Path | None = None,
    replace: bool,
    purpose: str = "staging",
) -> Path:
    if destination_root.exists() and not replace:
        raise StateConflictError(f"Destination already exists: {destination_root}")
    resolved = staged_root or staged_root_path(destination_root, purpose=purpose)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    remove_path(resolved)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def cleanup_root_stage(staged_root: Path, *, prune_stop_at: Path | None = None) -> None:
    remove_path(staged_root)
    prune_empty_directories(staged_root.parent, stop_at=prune_stop_at)


def promote_root_stage(
    *,
    storage_root: Path,
    destination_root: Path,
    staged_root: Path,
    expected_root_kind: RootKind,
    replace: bool,
) -> RootKind:
    require_root_kind(state_db_path(staged_root), expected_root_kind)
    replace_path_atomic(destination_root, staged_root, replace=replace)
    return reindex_root(storage_root, root_path=destination_root)


@contextmanager
def staged_root(
    *,
    storage_root: Path,
    destination_root: Path,
    expected_root_kind: RootKind,
    replace: bool = True,
    purpose: str = "staging",
    prune_stop_at: Path | None = None,
) -> Iterator[RootStage]:
    stage_path = prepare_root_stage(
        destination_root=destination_root,
        replace=replace,
        purpose=purpose,
    )
    stage = RootStage(
        storage_root=storage_root,
        destination_root=destination_root,
        staged_root=stage_path,
        expected_root_kind=expected_root_kind,
        replace=replace,
    )
    try:
        yield stage
    finally:
        if not stage._promoted:
            cleanup_root_stage(stage_path, prune_stop_at=prune_stop_at)
