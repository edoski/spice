"""Typed training and simulation summary envelopes."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from ..config import ArtifactVariant, ModelConfig, StudyConfig
from ..temporal.scaling import ScalerStats
from .objective import EpochMetrics, WindowMetricSummary
from .pipeline import PreparedInferenceDataset, PreparedTrainingDataset, TrainingRunResult
from .simulation import SimulationRunSummary, SimulationSummary


@dataclass(frozen=True, slots=True)
class ArtifactChainMetadata:
    name: str


@dataclass(frozen=True, slots=True)
class TrainingArtifactManifest:
    artifact_id: str
    objective_id: str
    chain: ArtifactChainMetadata
    dataset_id: str
    dataset_name: str
    task_id: str
    variant: ArtifactVariant
    study: StudyConfig | None
    study_id: str | None
    max_supported_delay_seconds: int
    lookback_seconds: int
    sample_count: int
    feature_history_seconds: int
    max_candidate_slots: int
    feature_set_id: str
    feature_names: list[str]
    feature_graph_fingerprint: str
    model: ModelConfig
    scaler: ScalerStats

    @property
    def n_features(self) -> int:
        return len(self.feature_names)


@dataclass(frozen=True, slots=True)
class SplitSizes:
    train_samples: int
    validation_samples: int
    test_samples: int


@dataclass(frozen=True, slots=True)
class TrainingSummary:
    artifact_id: str
    objective_id: str
    chain: str
    dataset_id: str
    dataset_name: str
    variant: ArtifactVariant
    study: StudyConfig | None
    study_id: str | None
    model_id: str
    task_id: str
    max_supported_delay_seconds: int
    lookback_seconds: int
    feature_history_seconds: int
    sample_count: int
    max_candidate_slots: int
    n_rows_available: int
    n_rows_used: int
    split_sizes: SplitSizes
    best_epoch: int
    resolved_device: str
    resolved_precision: str
    compiled: bool
    best_validation_metrics: EpochMetrics
    test_metrics: EpochMetrics


@dataclass(frozen=True, slots=True)
class TrainingEpochRecord:
    epoch: int
    train_metrics: EpochMetrics
    validation_metrics: EpochMetrics


@dataclass(frozen=True, slots=True)
class SimulationSummaryRecord:
    artifact_id: str
    objective_id: str
    chain: str
    dataset_id: str
    dataset_name: str
    variant: ArtifactVariant
    study: StudyConfig | None
    study_id: str | None
    model_id: str
    task_id: str
    max_supported_delay_seconds: int
    requested_delay_seconds: int
    lookback_seconds: int
    feature_history_seconds: int
    simulation_window_seconds: int
    arrival_rate_per_second: float
    repetitions: int
    n_history_rows: int
    n_evaluation_rows: int
    sample_count: int
    max_candidate_slots: int
    profit_over_baseline: float
    cost_over_optimum: float
    baseline_cost_over_optimum: float
    realized_fee_sum: float
    baseline_fee_sum: float
    optimum_fee_sum: float
    window_profit_over_baseline: WindowMetricSummary
    window_cost_over_optimum: WindowMetricSummary
    window_baseline_cost_over_optimum: WindowMetricSummary
    total_events: int
    runs: list[SimulationRunSummary]


def iter_epoch_records(result: TrainingRunResult) -> Iterator[TrainingEpochRecord]:
    for index, (train_metrics, validation_metrics) in enumerate(
        zip(
            result.training_result.train_history,
            result.training_result.validation_history,
            strict=True,
        ),
        start=1,
    ):
        yield TrainingEpochRecord(
            epoch=index,
            train_metrics=train_metrics,
            validation_metrics=validation_metrics,
        )


def build_training_summary(
    result: TrainingRunResult,
    *,
    chain_name: str,
    dataset_id: str,
    model_id: str,
    manifest: TrainingArtifactManifest,
    prepared: PreparedTrainingDataset,
    best_validation_metrics: EpochMetrics,
    test_metrics: EpochMetrics,
) -> TrainingSummary:
    return TrainingSummary(
        artifact_id=manifest.artifact_id,
        objective_id=manifest.objective_id,
        chain=chain_name,
        dataset_id=dataset_id,
        dataset_name=manifest.dataset_name,
        variant=manifest.variant,
        study=manifest.study,
        study_id=manifest.study_id,
        model_id=model_id,
        task_id=manifest.task_id,
        max_supported_delay_seconds=manifest.max_supported_delay_seconds,
        lookback_seconds=manifest.lookback_seconds,
        feature_history_seconds=manifest.feature_history_seconds,
        sample_count=manifest.sample_count,
        max_candidate_slots=manifest.max_candidate_slots,
        n_rows_available=prepared.n_rows_available,
        n_rows_used=prepared.n_rows_used,
        split_sizes=SplitSizes(
            train_samples=int(prepared.split_indices.train.shape[0]),
            validation_samples=int(prepared.split_indices.validation.shape[0]),
            test_samples=int(prepared.split_indices.test.shape[0]),
        ),
        best_epoch=result.training_result.best_epoch,
        resolved_device=result.training_result.resolved_device,
        resolved_precision=result.training_result.resolved_precision,
        compiled=result.training_result.compiled,
        best_validation_metrics=best_validation_metrics,
        test_metrics=test_metrics,
    )


def build_simulation_summary_record(
    manifest: TrainingArtifactManifest,
    *,
    prepared: PreparedInferenceDataset,
    simulation: SimulationSummary,
    requested_delay_seconds: int,
    window_seconds: int,
    arrival_rate_per_second: float,
    repetitions: int,
) -> SimulationSummaryRecord:
    return SimulationSummaryRecord(
        artifact_id=manifest.artifact_id,
        objective_id=manifest.objective_id,
        chain=manifest.chain.name,
        dataset_id=manifest.dataset_id,
        dataset_name=manifest.dataset_name,
        variant=manifest.variant,
        study=manifest.study,
        study_id=manifest.study_id,
        model_id=manifest.model.id,
        task_id=manifest.task_id,
        max_supported_delay_seconds=manifest.max_supported_delay_seconds,
        requested_delay_seconds=requested_delay_seconds,
        lookback_seconds=manifest.lookback_seconds,
        feature_history_seconds=manifest.feature_history_seconds,
        simulation_window_seconds=window_seconds,
        arrival_rate_per_second=arrival_rate_per_second,
        repetitions=repetitions,
        n_history_rows=prepared.n_history_rows,
        n_evaluation_rows=prepared.n_evaluation_rows,
        sample_count=prepared.sample_count,
        max_candidate_slots=manifest.max_candidate_slots,
        profit_over_baseline=simulation.profit_over_baseline,
        cost_over_optimum=simulation.cost_over_optimum,
        baseline_cost_over_optimum=simulation.baseline_cost_over_optimum,
        realized_fee_sum=simulation.realized_fee_sum,
        baseline_fee_sum=simulation.baseline_fee_sum,
        optimum_fee_sum=simulation.optimum_fee_sum,
        window_profit_over_baseline=simulation.window_profit_over_baseline,
        window_cost_over_optimum=simulation.window_cost_over_optimum,
        window_baseline_cost_over_optimum=simulation.window_baseline_cost_over_optimum,
        total_events=simulation.total_events,
        runs=list(simulation.runs),
    )
