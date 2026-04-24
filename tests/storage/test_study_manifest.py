from __future__ import annotations

from typing import cast

from spice.config import TuneConfig, WorkflowTask
from spice.storage.study_manifest import (
    manifest_from_payload,
    manifest_from_tune_config,
    manifest_payload,
)


def test_study_manifest_round_trips_through_canonical_request_payload(
    tmp_path,
    load_workflow_config,
) -> None:
    config = cast(
        TuneConfig,
        load_workflow_config(
            WorkflowTask.TUNE,
            workspace=tmp_path,
            surface="same_block_closed",
            study="roundtrip_probe",
        ),
    )

    manifest = manifest_from_tune_config(config)
    restored = manifest_from_payload(manifest_payload(manifest))

    assert restored == manifest
