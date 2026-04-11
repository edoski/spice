from __future__ import annotations

from pathlib import Path

from spice.core.constants import ARTIFACT_MANIFEST_FILENAME, MODEL_STATE_FILENAME
from spice.modeling.artifacts import load_training_artifact
from spice.modeling.execution import run_persisted_training
from spice.modeling.pipeline import TrainingSpec
from spice.modeling.reporting import TrainingRunReport
from tests.support import base_overrides, compose_experiment, make_history_rows, write_dataset_dir


def test_run_persisted_training_writes_canonical_training_outputs(tmp_path) -> None:
    config = compose_experiment("train", overrides=base_overrides(tmp_path))
    history_dir = Path(config.paths.enriched_history_dir)
    artifact_dir = Path(config.paths.artifact_root)
    report_path = Path(config.paths.train_report_path)
    write_dataset_dir(history_dir, make_history_rows())

    persisted = run_persisted_training(
        history_dir,
        spec=TrainingSpec(
            chain=config.chain,
            dataset_id=config.dataset.id,
            model=config.model,
            max_delay_seconds=config.dataset.temporal.max_delay_seconds,
            lookback_seconds=config.dataset.temporal.lookback_seconds,
            anchor_count=config.dataset.sampling.anchor_count,
            split=config.split,
            training=config.training,
        ),
        artifact_dir=artifact_dir,
        report_path=report_path,
    )

    loaded = load_training_artifact(artifact_dir)
    report = TrainingRunReport.model_validate_json(report_path.read_text(encoding="utf-8"))

    assert persisted.artifact_dir == artifact_dir
    assert persisted.report_path == report_path
    assert artifact_dir / ARTIFACT_MANIFEST_FILENAME in persisted.artifact_paths
    assert artifact_dir / MODEL_STATE_FILENAME in persisted.artifact_paths
    assert report_path in persisted.artifact_paths
    assert loaded.manifest.dataset_id == config.dataset.id
    assert loaded.manifest.model.family == config.model.family
    assert report.dataset_id == config.dataset.id
    assert report.artifact_dir == str(artifact_dir)
    assert report.best_epoch == persisted.training_run.training_result.best_epoch
