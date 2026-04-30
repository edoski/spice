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
from spice.storage.study_optuna import open_tuning_study
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


def test_tuning_objective_controls_study_direction(
    tmp_path,
    load_workflow_config,
    model_workflow_override,
    tune_override,
) -> None:
    override = model_workflow_override() | tune_override()
    override["tuning"] = {
        "trial_count": 2,
        "timeout_seconds": None,
        "sampler_seed": 2026,
        "enable_pruning": False,
    }
    override["objective"] = {
        "id": "validation",
        "metric_id": "offset_accuracy",
        "direction": "maximize",
    }
    config = cast(
        TuneConfig,
        load_workflow_config(
            WorkflowTask.TUNE,
            workspace=tmp_path,
            surface="current_row_fee_dynamics",
            override=override,
        ),
    )

    paths = build_workflow_paths(
        output_root=config.storage.root,
        chain_name=config.chain.name,
        identity=WorkflowIdentity(
            corpus_id=TEST_DATASET_ID,
            study_id=produced_study_id(config),
        ),
    )
    assert paths.study_state_db is not None
    access = open_tuning_study(
        paths.study_state_db,
        config=config,
        paths=paths,
        corpus_manifest=_corpus_manifest(config),
    )

    assert access.study.direction.name == "MAXIMIZE"
    assert access.manifest.objective.metric_id == "offset_accuracy"
