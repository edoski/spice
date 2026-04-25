"""Training workflow."""

from __future__ import annotations

from typing import cast

from ..config.models import ArtifactVariant, TrainConfig
from ..core.errors import ConfigResolutionError
from ..core.rendering import metric_string
from ..core.reporting import Reporter
from ..corpus.coverage import training_coverage_requirement, validate_corpus_coverage
from ..modeling.persisted_training import run_persisted_training
from ..modeling.pipeline import build_training_spec
from ..modeling.summary import training_result_fields
from ..modeling.training import TrainingEpochProgress
from ..modeling.tuning import apply_study_best_params
from ..storage.corpus import load_dataset_manifest
from ..storage.engine import ARTIFACT_ROOT_KIND
from ..storage.layout import resolve_workflow_paths
from ..storage.staging import staged_root


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
    active_reporter = reporter or Reporter()
    active_config: TrainConfig = config
    study_id: str | None = None
    if config.artifact.variant is ArtifactVariant.TUNED:
        applied = apply_study_best_params(config)
        active_config = cast(TrainConfig, applied.config)
        study_id = applied.study_id
    paths = resolve_workflow_paths(active_config, study_id=study_id)
    active_reporter.header("train", _workflow_facts(active_config))
    spec = build_training_spec(active_config, paths=paths)
    validate_corpus_coverage(
        load_dataset_manifest(paths.corpus_state_db),
        contract=spec.problem_contract,
        feature_contract=spec.feature_contract,
        requirement=training_coverage_requirement(spec.problem_contract),
    )
    artifact_dir = paths.artifact_root
    history_block_path = paths.history_dir
    if artifact_dir is None:
        raise ConfigResolutionError("training workflow requires artifact output paths")
    with staged_root(
        storage_root=paths.output_root,
        destination_root=artifact_dir,
        expected_root_kind=ARTIFACT_ROOT_KIND,
        purpose="staging",
        prune_stop_at=artifact_dir.parent.parent,
    ) as artifact_stage:
        persisted = run_persisted_training(
            history_block_path,
            spec=spec,
            artifact_dir=artifact_stage.staged_root,
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
        artifact_stage.promote()
    active_reporter.result(
        "train",
        training_result_fields(
            persisted.summary,
            artifact_dir=artifact_dir,
        ),
    )
