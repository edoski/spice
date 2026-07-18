"""Package-private read closure for legacy study-root manifests."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from ..core.errors import MissingStateError
from .engine import STUDY_ROOT_KIND, create_state_engine, require_root_kind
from .payloads import mapping_payload
from .schema import study_manifest
from .study_manifest_codecs import _decode_study_manifest
from .study_models import StudyManifest


def load_study_manifest(db_path: Path) -> StudyManifest:
    """Load the canonical study manifest that owns persisted study provenance."""

    if not db_path.is_file():
        raise MissingStateError(f"Missing study manifest: {db_path}")
    manifest = _try_load_existing_manifest(db_path)
    if manifest is None:
        raise MissingStateError(f"Missing study manifest: {db_path}")
    return manifest


def try_load_study_manifest(db_path: Path) -> StudyManifest | None:
    if not db_path.is_file():
        return None
    return _try_load_existing_manifest(db_path)


def _try_load_existing_manifest(db_path: Path) -> StudyManifest | None:
    require_root_kind(db_path, STUDY_ROOT_KIND)
    engine = create_state_engine(db_path)
    try:
        with engine.connect() as conn:
            payload = conn.execute(select(study_manifest.c.payload)).scalar_one_or_none()
    finally:
        engine.dispose()
    if payload is None:
        return None
    return _decode_study_manifest(mapping_payload(payload, label=study_manifest.name))
