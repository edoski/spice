"""Training workflow."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from ..config import ArtifactVariant, TrainConfig
from ..core.errors import ConfigResolutionError
from ..core.files import promote_paths_atomic, prune_empty_directories, remove_path
from ..core.rendering import metric_string
from ..core.reporting import Reporter
from ..modeling.persisted_training import run_persisted_training
from ..modeling.pipeline import build_training_spec
from ..modeling.summary import training_result_fields
from ..modeling.training import TrainingEpochProgress
from ..modeling.tuning import apply_study_best_params
from ..storage.catalog import upsert_artifact_record
from ..storage.engine import ARTIFACT_ROOT_KIND
from ..storage.layout import resolve_workflow_paths
from ._shared import abort_cleanup, managed_workflow


def _build_staged_artifact_root(artifact_root: Path) -> Path:
    return artifact_root.parent / f".{artifact_root.name}.staging.{uuid4().hex}"


def _cleanup_staged_artifact_root(staged_root: Path, *, prune_stop_at: Path) -> None:
    remove_path(staged_root)
    prune_empty_directories(staged_root.parent, stop_at=prune_stop_at)


def _workflow_facts(config: TrainConfig) -> list[tuple[str, str]]:
    facts = [
        ("dataset", config.dataset.name),
        ("chain", config.chain.name),
        ("problem", config.problem.id),
        ("prediction", config.prediction.id),
        ("model", config.model.id),
        ("variant", config.artifact.variant.value),
    ]
    if config.artifact.variant is ArtifactVariant.TUNED:
        facts.append(("study", config.study.name))
    return facts


def _fit_epoch_message(
    progress: TrainingEpochProgress,
    *,
    primary_metric_id: str,
) -> str:
    fields = [f"epoch={progress.epoch}/{progress.max_epochs}"]
    if progress.objective_metric_id in progress.objective_metrics.values:
        fields.append(
            f"objective.{progress.objective_metric_id}="
            f"{metric_string(progress.objective_metrics.values[progress.objective_metric_id])}"
        )
    if primary_metric_id in progress.validation_metrics.values:
        fields.append(
            f"validation.{primary_metric_id}="
            f"{metric_string(progress.validation_metrics.values[primary_metric_id])}"
        )
    fields.append(f"best_epoch={progress.best_epoch}")
    fields.append(
        f"best.{progress.objective_metric_id}={metric_string(progress.best_objective_value)}"
    )
    return "fit " + " ".join(fields)


def run(config: TrainConfig, *, reporter: Reporter | None = None) -> None:
    with managed_workflow(reporter=reporter) as active_reporter:
        active_config = config
        if config.artifact.variant is ArtifactVariant.TUNED:
            active_config = apply_study_best_params(config)
        paths = resolve_workflow_paths(active_config)
        active_reporter.header("train", _workflow_facts(active_config))
        spec = build_training_spec(active_config)
        artifact_dir = paths.artifact_root
        history_block_path = paths.history_dir
        if artifact_dir is None:
            raise ConfigResolutionError("training workflow requires artifact output paths")
        staged_artifact_root = _build_staged_artifact_root(artifact_dir)
        prune_stop_at = artifact_dir.parent.parent
        with abort_cleanup(
            active_reporter,
            label="train",
            cleanup=lambda: _cleanup_staged_artifact_root(
                staged_artifact_root,
                prune_stop_at=prune_stop_at,
            ),
        ):
            _cleanup_staged_artifact_root(
                staged_artifact_root,
                prune_stop_at=prune_stop_at,
            )
            persisted = run_persisted_training(
                history_block_path,
                spec=spec,
                artifact_dir=staged_artifact_root,
                state_root_kind=ARTIFACT_ROOT_KIND,
                on_prepare_complete=lambda prepared: active_reporter.milestone(
                    f"prepare rows={prepared.n_rows_used} samples={prepared.sample_count}"
                ),
                on_fit_start=lambda: active_reporter.milestone(
                    f"fit started epochs={spec.training.max_epochs}"
                ),
                on_epoch_end=lambda progress: active_reporter.milestone(
                    _fit_epoch_message(
                        progress,
                        primary_metric_id=spec.prediction_contract.primary_metric_id,
                    )
                ),
                on_early_stop=lambda epoch, best_epoch: active_reporter.milestone(
                    f"fit early_stop epoch={epoch} best_epoch={best_epoch}"
                ),
            )
            artifact_root = paths.artifact_root
            artifact_state_db = paths.artifact_state_db
            artifact_id = paths.artifact_id
            if artifact_root is None or artifact_state_db is None or artifact_id is None:
                raise ConfigResolutionError("training workflow requires artifact output paths")
            promote_paths_atomic([(artifact_root, staged_artifact_root)])
            upsert_artifact_record(
                paths.catalog_db,
                artifact_id=artifact_id,
                dataset_id=paths.corpus_id,
                dataset_name=active_config.dataset.name,
                chain_name=active_config.chain.name,
                feature_set_id=active_config.feature_set.id,
                prediction_id=active_config.prediction.id,
                model_id=active_config.model.id,
                problem_id=active_config.problem.id,
                variant=active_config.artifact.variant.value,
                study_id=paths.study_id,
                study_name=(
                    active_config.study.name
                    if active_config.artifact.variant is ArtifactVariant.TUNED
                    else None
                ),
                root_path=artifact_root,
                state_db_path=artifact_state_db,
            )
        active_reporter.result(
            "train",
            training_result_fields(
                persisted.summary,
                artifact_dir=artifact_root,
            ),
        )
