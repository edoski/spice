"""Typed state payload codecs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from ..config import ArtifactVariant, StudyConfig
from ..data.normalization import ScalerStats
from ..modeling.objective import EpochMetrics, WindowMetricSummary
from ..modeling.registry import coerce_model_config

if TYPE_CHECKING:
    from ..modeling.artifacts import TrainingArtifactManifest
    from ..modeling.reporting import (
        SimulationSummaryRecord,
        TrainingEpochRecord,
        TrainingSummary,
    )
    from ..modeling.simulation import SimulationRunSummary


def mapping_payload(payload: object) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        raise TypeError("Expected mapping payload")
    return dict(payload)


def string_list_payload(payload: object) -> list[str]:
    if not isinstance(payload, list):
        raise TypeError("Expected list payload")
    return [str(value) for value in payload]


def int_list_payload(payload: object) -> list[int]:
    if not isinstance(payload, list):
        raise TypeError("Expected list payload")
    return [int(value) for value in payload]


def study_config_from_name(study_name: object) -> StudyConfig | None:
    if study_name is None:
        return None
    return StudyConfig(name=str(study_name))


def epoch_metrics_values(metrics: EpochMetrics) -> dict[str, float]:
    return {
        "objective_loss": metrics.objective_loss,
        "exact_optimum_hit_rate": metrics.exact_optimum_hit_rate,
        "cost_over_optimum": metrics.cost_over_optimum,
        "profit_over_baseline": metrics.profit_over_baseline,
    }


def epoch_metrics_from_payload(payload: object) -> EpochMetrics:
    mapping = mapping_payload(payload)
    return EpochMetrics(
        objective_loss=float(mapping["objective_loss"]),
        exact_optimum_hit_rate=float(mapping["exact_optimum_hit_rate"]),
        cost_over_optimum=float(mapping["cost_over_optimum"]),
        profit_over_baseline=float(mapping["profit_over_baseline"]),
    )


def window_metric_values(summary: WindowMetricSummary) -> dict[str, float]:
    return {
        "mean": summary.mean,
        "std": summary.std,
    }


def window_metric_from_payload(payload: object) -> WindowMetricSummary:
    mapping = mapping_payload(payload)
    return WindowMetricSummary(
        mean=float(mapping["mean"]),
        std=float(mapping["std"]),
    )


def artifact_manifest_values(manifest: TrainingArtifactManifest) -> dict[str, object]:
    return {
        "singleton": 1,
        "artifact_id": manifest.artifact_id,
        "objective_id": manifest.objective_id,
        "chain_name": manifest.chain.name,
        "dataset_id": manifest.dataset_id,
        "dataset_name": manifest.dataset_name,
        "task_id": manifest.task_id,
        "variant": manifest.variant.value,
        "study_id": manifest.study_id,
        "study_name": None if manifest.study is None else manifest.study.name,
        "model_id": manifest.model.id,
        "max_supported_delay_seconds": manifest.max_supported_delay_seconds,
        "lookback_seconds": manifest.lookback_seconds,
        "sample_count": manifest.sample_count,
        "feature_history_seconds": manifest.feature_history_seconds,
        "max_candidate_slots": manifest.max_candidate_slots,
        "feature_set_id": manifest.feature_set_id,
        "feature_names": list(manifest.feature_names),
        "feature_graph_fingerprint": manifest.feature_graph_fingerprint,
        "model": manifest.model.model_dump(mode="json", exclude_none=True),
        "scaler": manifest.scaler.model_dump(mode="json", exclude_none=True),
    }


def artifact_manifest_from_row(row: Mapping[str, object]) -> TrainingArtifactManifest:
    from ..modeling.artifacts import ArtifactChainMetadata, TrainingArtifactManifest

    return TrainingArtifactManifest(
        artifact_id=str(row["artifact_id"]),
        objective_id=str(row["objective_id"]),
        chain=ArtifactChainMetadata(name=str(row["chain_name"])),
        dataset_id=str(row["dataset_id"]),
        dataset_name=str(row["dataset_name"]),
        task_id=str(row["task_id"]),
        variant=ArtifactVariant(str(row["variant"])),
        study=study_config_from_name(row["study_name"]),
        study_id=None if row["study_id"] is None else str(row["study_id"]),
        max_supported_delay_seconds=int(row["max_supported_delay_seconds"]),
        lookback_seconds=int(row["lookback_seconds"]),
        sample_count=int(row["sample_count"]),
        feature_history_seconds=int(row["feature_history_seconds"]),
        max_candidate_slots=int(row["max_candidate_slots"]),
        feature_set_id=str(row["feature_set_id"]),
        feature_names=string_list_payload(row["feature_names"]),
        feature_graph_fingerprint=str(row["feature_graph_fingerprint"]),
        model=coerce_model_config(mapping_payload(row["model"])),
        scaler=ScalerStats.model_validate(mapping_payload(row["scaler"])),
    )


def training_summary_values(summary: TrainingSummary) -> dict[str, object]:
    return {
        "singleton": 1,
        "artifact_id": summary.artifact_id,
        "objective_id": summary.objective_id,
        "chain_name": summary.chain,
        "dataset_id": summary.dataset_id,
        "dataset_name": summary.dataset_name,
        "variant": summary.variant.value,
        "study_id": summary.study_id,
        "study_name": None if summary.study is None else summary.study.name,
        "model_id": summary.model_id,
        "task_id": summary.task_id,
        "max_supported_delay_seconds": summary.max_supported_delay_seconds,
        "lookback_seconds": summary.lookback_seconds,
        "feature_history_seconds": summary.feature_history_seconds,
        "sample_count": summary.sample_count,
        "max_candidate_slots": summary.max_candidate_slots,
        "n_rows_available": summary.n_rows_available,
        "n_rows_used": summary.n_rows_used,
        "train_samples": summary.split_sizes.train_samples,
        "validation_samples": summary.split_sizes.validation_samples,
        "test_samples": summary.split_sizes.test_samples,
        "best_epoch": summary.best_epoch,
        "resolved_device": summary.resolved_device,
        "resolved_precision": summary.resolved_precision,
        "compiled": summary.compiled,
        "best_validation_metrics": epoch_metrics_values(summary.best_validation_metrics),
        "test_metrics": epoch_metrics_values(summary.test_metrics),
    }


def training_summary_from_row(row: Mapping[str, object]) -> TrainingSummary:
    from ..modeling.reporting import SplitSizes, TrainingSummary

    return TrainingSummary(
        artifact_id=str(row["artifact_id"]),
        objective_id=str(row["objective_id"]),
        chain=str(row["chain_name"]),
        dataset_id=str(row["dataset_id"]),
        dataset_name=str(row["dataset_name"]),
        variant=ArtifactVariant(str(row["variant"])),
        study=study_config_from_name(row["study_name"]),
        study_id=None if row["study_id"] is None else str(row["study_id"]),
        model_id=str(row["model_id"]),
        task_id=str(row["task_id"]),
        max_supported_delay_seconds=int(row["max_supported_delay_seconds"]),
        lookback_seconds=int(row["lookback_seconds"]),
        feature_history_seconds=int(row["feature_history_seconds"]),
        sample_count=int(row["sample_count"]),
        max_candidate_slots=int(row["max_candidate_slots"]),
        n_rows_available=int(row["n_rows_available"]),
        n_rows_used=int(row["n_rows_used"]),
        split_sizes=SplitSizes(
            train_samples=int(row["train_samples"]),
            validation_samples=int(row["validation_samples"]),
            test_samples=int(row["test_samples"]),
        ),
        best_epoch=int(row["best_epoch"]),
        resolved_device=str(row["resolved_device"]),
        resolved_precision=str(row["resolved_precision"]),
        compiled=bool(row["compiled"]),
        best_validation_metrics=epoch_metrics_from_payload(row["best_validation_metrics"]),
        test_metrics=epoch_metrics_from_payload(row["test_metrics"]),
    )


def training_epoch_values(record: TrainingEpochRecord) -> dict[str, object]:
    return {
        "epoch": record.epoch,
        "train_metrics": epoch_metrics_values(record.train_metrics),
        "validation_metrics": epoch_metrics_values(record.validation_metrics),
    }


def training_epoch_from_row(row: Mapping[str, object]) -> TrainingEpochRecord:
    from ..modeling.reporting import TrainingEpochRecord

    return TrainingEpochRecord(
        epoch=int(row["epoch"]),
        train_metrics=epoch_metrics_from_payload(row["train_metrics"]),
        validation_metrics=epoch_metrics_from_payload(row["validation_metrics"]),
    )


def simulation_summary_values(summary: SimulationSummaryRecord) -> dict[str, object]:
    return {
        "singleton": 1,
        "artifact_id": summary.artifact_id,
        "objective_id": summary.objective_id,
        "chain_name": summary.chain,
        "dataset_id": summary.dataset_id,
        "dataset_name": summary.dataset_name,
        "variant": summary.variant.value,
        "study_id": summary.study_id,
        "study_name": None if summary.study is None else summary.study.name,
        "model_id": summary.model_id,
        "task_id": summary.task_id,
        "max_supported_delay_seconds": summary.max_supported_delay_seconds,
        "requested_delay_seconds": summary.requested_delay_seconds,
        "lookback_seconds": summary.lookback_seconds,
        "feature_history_seconds": summary.feature_history_seconds,
        "simulation_window_seconds": summary.simulation_window_seconds,
        "arrival_rate_per_second": summary.arrival_rate_per_second,
        "repetitions": summary.repetitions,
        "n_history_rows": summary.n_history_rows,
        "n_evaluation_rows": summary.n_evaluation_rows,
        "sample_count": summary.sample_count,
        "max_candidate_slots": summary.max_candidate_slots,
        "profit_over_baseline": summary.profit_over_baseline,
        "cost_over_optimum": summary.cost_over_optimum,
        "baseline_cost_over_optimum": summary.baseline_cost_over_optimum,
        "realized_fee_sum": summary.realized_fee_sum,
        "baseline_fee_sum": summary.baseline_fee_sum,
        "optimum_fee_sum": summary.optimum_fee_sum,
        "window_profit_over_baseline": window_metric_values(summary.window_profit_over_baseline),
        "window_cost_over_optimum": window_metric_values(summary.window_cost_over_optimum),
        "window_baseline_cost_over_optimum": window_metric_values(
            summary.window_baseline_cost_over_optimum
        ),
        "total_events": summary.total_events,
    }


def simulation_summary_from_row(
    row: Mapping[str, object],
    *,
    runs: list[SimulationRunSummary],
) -> SimulationSummaryRecord:
    from ..modeling.reporting import SimulationSummaryRecord

    return SimulationSummaryRecord(
        artifact_id=str(row["artifact_id"]),
        objective_id=str(row["objective_id"]),
        chain=str(row["chain_name"]),
        dataset_id=str(row["dataset_id"]),
        dataset_name=str(row["dataset_name"]),
        variant=ArtifactVariant(str(row["variant"])),
        study=study_config_from_name(row["study_name"]),
        study_id=None if row["study_id"] is None else str(row["study_id"]),
        model_id=str(row["model_id"]),
        task_id=str(row["task_id"]),
        max_supported_delay_seconds=int(row["max_supported_delay_seconds"]),
        requested_delay_seconds=int(row["requested_delay_seconds"]),
        lookback_seconds=int(row["lookback_seconds"]),
        feature_history_seconds=int(row["feature_history_seconds"]),
        simulation_window_seconds=int(row["simulation_window_seconds"]),
        arrival_rate_per_second=float(row["arrival_rate_per_second"]),
        repetitions=int(row["repetitions"]),
        n_history_rows=int(row["n_history_rows"]),
        n_evaluation_rows=int(row["n_evaluation_rows"]),
        sample_count=int(row["sample_count"]),
        max_candidate_slots=int(row["max_candidate_slots"]),
        profit_over_baseline=float(row["profit_over_baseline"]),
        cost_over_optimum=float(row["cost_over_optimum"]),
        baseline_cost_over_optimum=float(row["baseline_cost_over_optimum"]),
        realized_fee_sum=float(row["realized_fee_sum"]),
        baseline_fee_sum=float(row["baseline_fee_sum"]),
        optimum_fee_sum=float(row["optimum_fee_sum"]),
        window_profit_over_baseline=window_metric_from_payload(
            row["window_profit_over_baseline"]
        ),
        window_cost_over_optimum=window_metric_from_payload(row["window_cost_over_optimum"]),
        window_baseline_cost_over_optimum=window_metric_from_payload(
            row["window_baseline_cost_over_optimum"]
        ),
        total_events=int(row["total_events"]),
        runs=runs,
    )


def simulation_run_values(run: SimulationRunSummary, *, ordinal: int) -> dict[str, object]:
    return {
        "ordinal": ordinal,
        "window_start_timestamp": run.window_start_timestamp,
        "window_end_timestamp": run.window_end_timestamp,
        "n_arrivals": run.n_arrivals,
        "n_events": run.n_events,
        "profit_over_baseline": run.profit_over_baseline,
        "cost_over_optimum": run.cost_over_optimum,
        "baseline_cost_over_optimum": run.baseline_cost_over_optimum,
        "realized_fee_sum": run.realized_fee_sum,
        "baseline_fee_sum": run.baseline_fee_sum,
        "optimum_fee_sum": run.optimum_fee_sum,
    }


def simulation_run_from_row(row: Mapping[str, object]) -> SimulationRunSummary:
    from ..modeling.simulation import SimulationRunSummary

    return SimulationRunSummary(
        window_start_timestamp=float(row["window_start_timestamp"]),
        window_end_timestamp=float(row["window_end_timestamp"]),
        n_arrivals=int(row["n_arrivals"]),
        n_events=int(row["n_events"]),
        profit_over_baseline=float(row["profit_over_baseline"]),
        cost_over_optimum=float(row["cost_over_optimum"]),
        baseline_cost_over_optimum=float(row["baseline_cost_over_optimum"]),
        realized_fee_sum=float(row["realized_fee_sum"]),
        baseline_fee_sum=float(row["baseline_fee_sum"]),
        optimum_fee_sum=float(row["optimum_fee_sum"]),
    )
