from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from spice.config import TuneConfig, WorkflowTask
from spice.core.errors import MissingStateError
from spice.storage.study_manifest import (
    load_study_manifest,
    manifest_from_payload,
    manifest_from_tune_config,
    manifest_payload,
    try_load_study_manifest,
)


def test_try_load_study_manifest_is_read_only_for_missing_db(tmp_path: Path) -> None:
    db_path = tmp_path / "studies" / "ethereum" / "study-1" / ".spice" / "state.sqlite"

    assert try_load_study_manifest(db_path) is None
    assert not db_path.exists()


def test_load_study_manifest_fails_cleanly_for_missing_db(tmp_path: Path) -> None:
    db_path = tmp_path / "studies" / "ethereum" / "study-1" / ".spice" / "state.sqlite"

    with pytest.raises(MissingStateError, match="Missing study manifest"):
        load_study_manifest(db_path)
    assert not db_path.exists()


def test_study_manifest_round_trips_through_canonical_request_payload(
    tmp_path: Path,
    load_workflow_config,
) -> None:
    config = cast(
        TuneConfig,
        load_workflow_config(
            WorkflowTask.TUNE,
            workspace=tmp_path,
            preset="icdcs_2026_professor",
            study="roundtrip_probe",
        ),
    )

    manifest = manifest_from_tune_config(config)
    restored = manifest_from_payload(manifest_payload(manifest))

    assert restored == manifest
