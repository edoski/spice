"""Artifact-root inspection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..core.rendering import metric_bundle_string, window_metric_fields
from ..features import FeaturePrerequisites
from ..modeling.artifacts import TrainingArtifactManifest
from ..modeling.results import LoadedSimulationSummary, LoadedTrainingSummary, TrainingEpochRecord
from ..modeling.simulation import SimulationRunSummary
from .artifact import (
    list_simulation_runs,
    list_training_epochs,
    load_artifact_manifest,
    load_simulation_summary,
    load_training_summary,
)
from .catalog import CatalogArtifactRecord


@dataclass(frozen=True, slots=True)
class ArtifactRootDescription:
    manifest: TrainingArtifactManifest
    training: LoadedTrainingSummary | None = None
    simulation: LoadedSimulationSummary | None = None
    epochs: list[TrainingEpochRecord] | None = None
    runs: list[SimulationRunSummary] | None = None


def artifact_list_sections(
    records: list[CatalogArtifactRecord],
) -> list[tuple[str, list[tuple[str, str]]]]:
    return [
        (
            "artifacts",
            [
                (
                    record.artifact_id,
                    (
                        f"chain={record.chain_name} "
                        f"dataset={record.dataset_name} "
                        f"feature_set={record.feature_set_id} "
                        f"prediction={record.prediction_id} "
                        f"model={record.model_id} "
                        f"problem={record.problem_id} "
                        f"variant={record.variant}"
                        + ("" if record.study_name is None else f" study={record.study_name}")
                    ),
                )
                for record in records
            ],
        )
    ]


def describe_artifact_root(
    root_db_path: Path,
    *,
    detail: str | None = None,
) -> ArtifactRootDescription:
    training = load_training_summary(root_db_path)
    simulation = load_simulation_summary(root_db_path)
    return ArtifactRootDescription(
        manifest=(
            training.manifest
            if training is not None
            else simulation.manifest
            if simulation is not None
            else load_artifact_manifest(root_db_path)
        ),
        training=training,
        simulation=simulation,
        epochs=list_training_epochs(root_db_path) if detail == "epochs" else None,
        runs=list_simulation_runs(root_db_path) if detail == "runs" else None,
    )


def artifact_sections(
    description: ArtifactRootDescription,
) -> list[tuple[str, list[tuple[str, str]]]]:
    manifest = description.manifest
    sections = [
        (
            "artifact",
            [
                ("artifact id", manifest.artifact_id),
                ("prediction", manifest.prediction_id),
                ("dataset", manifest.dataset_name),
                ("dataset id", manifest.dataset_id),
                ("chain", manifest.chain.name),
                ("problem", manifest.problem_id),
                ("feature set", manifest.feature_set_id),
                ("feature family", manifest.feature_family_id),
                ("model", manifest.model.id),
                ("variant", manifest.variant.value),
                ("study", manifest.study.name if manifest.study is not None else "n/a"),
                ("study id", manifest.study_id or "n/a"),
                ("capability", f"{manifest.max_delay_seconds}s"),
                ("lookback", f"{manifest.lookback_seconds}s"),
                (
                    "feature prerequisites",
                    feature_prerequisites_string(manifest.feature_prerequisites),
                ),
                ("max slots", str(manifest.max_candidate_slots)),
            ],
        ),
    ]
    if description.training is not None:
        training = description.training
        runtime = training.runtime
        sections.append(
            (
                "training",
                [
                    ("best epoch", str(runtime.best_epoch)),
                    ("representation", training.manifest.representation_id),
                    ("storage mode", runtime.storage_mode_id),
                    ("batch planner", runtime.batch_planner_id),
                    (
                        "split",
                        " ".join(
                            [
                                f"train={runtime.split_sizes.train_samples}",
                                f"validation={runtime.split_sizes.validation_samples}",
                                f"test={runtime.split_sizes.test_samples}",
                            ]
                        ),
                    ),
                    (
                        "validation metrics",
                        metric_bundle_string(
                            training.manifest.training_metric_descriptors,
                            runtime.best_validation_metrics.values,
                        ),
                    ),
                    (
                        "test metrics",
                        metric_bundle_string(
                            training.manifest.training_metric_descriptors,
                            runtime.test_metrics.values,
                        ),
                    ),
                ],
            )
        )
    if description.simulation is not None:
        simulation = description.simulation
        runtime = simulation.runtime
        sections.append(
            (
                "simulation",
                [
                    ("requested", f"{runtime.delay_seconds}s"),
                    ("window", f"{runtime.simulation_window_seconds}s"),
                    ("repetitions", str(runtime.repetitions)),
                    ("events", str(runtime.total_events)),
                    (
                        "metrics",
                        metric_bundle_string(
                            simulation.manifest.simulation_metric_descriptors,
                            runtime.metrics.values,
                        ),
                    ),
                ],
            )
        )
        if runtime.window_metrics:
            sections.append(
                (
                    "simulation windows",
                    window_metric_fields(
                        simulation.manifest.simulation_metric_descriptors,
                        runtime.window_metrics,
                    ),
                )
            )
    if description.epochs:
        sections.append(
            (
                "epochs",
                [(f"epoch {record.epoch}", epoch_string(record)) for record in description.epochs],
            )
        )
    if description.runs:
        sections.append(
            (
                "runs",
                [
                    (f"run {index}", simulation_run_string(run))
                    for index, run in enumerate(description.runs, start=1)
                ],
            )
        )
    return sections


def feature_prerequisites_string(prerequisites: FeaturePrerequisites) -> str:
    return f"history={prerequisites.history_seconds}s warmup={prerequisites.warmup_rows} rows"


def epoch_string(record: TrainingEpochRecord) -> str:
    return (
        f"train={metric_bundle_string([], record.train_metrics.values)} "
        f"val={metric_bundle_string([], record.validation_metrics.values)}"
    )


def simulation_run_string(run: SimulationRunSummary) -> str:
    return f"events={run.n_events} metrics={metric_bundle_string([], run.metrics)}"
