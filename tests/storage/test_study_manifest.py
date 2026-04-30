from __future__ import annotations

from typing import cast

from spice.config import TuneConfig, WorkflowTask
from spice.corpus.metadata import (
    ChainMetadata,
    DatasetCoverageMetadata,
    DatasetIdentity,
    DatasetManifest,
    DatasetRequestMetadata,
    DatasetValidationMetadata,
    DatasetWindowMetadata,
)
from spice.storage.root_consumer_paths import produced_study_id
from spice.storage.study_manifest import (
    manifest_from_payload,
    manifest_from_tune_config,
    manifest_payload,
)
from spice.storage.workflow_paths import WorkflowIdentity, build_workflow_paths

TEST_DATASET_ID = "cor_9a73b1e88edb488afb1e"


def _corpus_manifest(config: TuneConfig) -> DatasetManifest:
    window = DatasetWindowMetadata(start_timestamp=1, end_timestamp=2)
    return DatasetManifest(
        dataset=DatasetIdentity(id=TEST_DATASET_ID, name=config.dataset.name),
        chain=ChainMetadata(name=config.chain.name, runtime=config.chain.runtime),
        request=DatasetRequestMetadata(history=window, evaluation=window),
        coverage=DatasetCoverageMetadata(history=window, evaluation=window),
        validation=DatasetValidationMetadata(history=None, evaluation=None),
    )


def test_study_manifest_round_trips_through_canonical_definition_payload(
    tmp_path,
    load_workflow_config,
) -> None:
    config = cast(
        TuneConfig,
        load_workflow_config(
            WorkflowTask.TUNE,
            workspace=tmp_path,
            surface="current_row_fee_dynamics",
            study="roundtrip_probe",
        ),
    )

    manifest = manifest_from_tune_config(
        config,
        paths=build_workflow_paths(
            output_root=config.storage.root,
            chain_name=config.chain.name,
            identity=WorkflowIdentity(
                corpus_id=TEST_DATASET_ID,
                study_id=produced_study_id(config),
            ),
        ),
        corpus_manifest=_corpus_manifest(config),
    )
    restored = manifest_from_payload(manifest_payload(manifest))

    assert restored == manifest
