"""Typed state payload codecs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, cast

from sqlalchemy.engine import RowMapping

from ..config import ArtifactVariant, StudyConfig
from ..temporal.scaling import ScalerStats
from .families.registry import coerce_model_config
from .objective import EpochMetrics, WindowMetricSummary

if TYPE_CHECKING:
    from .artifacts import TrainingArtifactManifest
    from .results import (
        SimulationSummaryRecord,
        TrainingEpochRecord,
        TrainingSummary,
    )
    from .simulation import SimulationRunSummary


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


def _row_value(row: RowMapping, key: str) -> object:
    return row[key]


def _row_optional_str(row: RowMapping, key: str) -> str | None:
    value = _row_value(row, key)
    if value is None:
        return None
    return str(value)


def _row_str(row: RowMapping, key: str) -> str:
    return str(_row_value(row, key))


def _row_int(row: RowMapping, key: str) -> int:
    return _int_value(_row_value(row, key))


def _row_float(row: RowMapping, key: str) -> float:
    return _float_value(_row_value(row, key))


def _int_value(value: object) -> int:
    return int(cast(int | float | str | bytes, value))


def _float_value(value: object) -> float:
    return float(cast(int | float | str | bytes, value))


def _payload_float(mapping: dict[str, object], key: str) -> float:
    return _float_value(mapping[key])


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
        objective_loss=_payload_float(mapping, "objective_loss"),
        exact_optimum_hit_rate=_payload_float(mapping, "exact_optimum_hit_rate"),
        cost_over_optimum=_payload_float(mapping, "cost_over_optimum"),
        profit_over_baseline=_payload_float(mapping, "profit_over_baseline"),
    )


def window_metric_values(summary: WindowMetricSummary) -> dict[str, float]:
    return {
        "mean": summary.mean,
        "std": summary.std,
    }


def window_metric_from_payload(payload: object) -> WindowMetricSummary:
    mapping = mapping_payload(payload)
    return WindowMetricSummary(
        mean=_payload_float(mapping, "mean"),
        std=_payload_float(mapping, "std"),
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


def artifact_manifest_from_row(row: RowMapping) -> TrainingArtifactManifest:
    from .results import ArtifactChainMetadata, TrainingArtifactManifest

    return TrainingArtifactManifest(
        artifact_id=_row_str(row, "artifact_id"),
        objective_id=_row_str(row, "objective_id"),
        chain=ArtifactChainMetadata(name=_row_str(row, "chain_name")),
        dataset_id=_row_str(row, "dataset_id"),
        dataset_name=_row_str(row, "dataset_name"),
        task_id=_row_str(row, "task_id"),
        variant=ArtifactVariant(_row_str(row, "variant")),
        study=study_config_from_name(_row_value(row, "study_name")),
        study_id=_row_optional_str(row, "study_id"),
        max_supported_delay_seconds=_row_int(row, "max_supported_delay_seconds"),
        lookback_seconds=_row_int(row, "lookback_seconds"),
        sample_count=_row_int(row, "sample_count"),
        feature_history_seconds=_row_int(row, "feature_history_seconds"),
        max_candidate_slots=_row_int(row, "max_candidate_slots"),
        feature_set_id=_row_str(row, "feature_set_id"),
        feature_names=string_list_payload(_row_value(row, "feature_names")),
        feature_graph_fingerprint=_row_str(row, "feature_graph_fingerprint"),
        model=coerce_model_config(mapping_payload(_row_value(row, "model"))),
        scaler=ScalerStats.model_validate(mapping_payload(_row_value(row, "scaler"))),
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


def training_summary_from_row(row: RowMapping) -> TrainingSummary:
    from .results import SplitSizes, TrainingSummary

    return TrainingSummary(
        artifact_id=_row_str(row, "artifact_id"),
        objective_id=_row_str(row, "objective_id"),
        chain=_row_str(row, "chain_name"),
        dataset_id=_row_str(row, "dataset_id"),
        dataset_name=_row_str(row, "dataset_name"),
        variant=ArtifactVariant(_row_str(row, "variant")),
        study=study_config_from_name(_row_value(row, "study_name")),
        study_id=_row_optional_str(row, "study_id"),
        model_id=_row_str(row, "model_id"),
        task_id=_row_str(row, "task_id"),
        max_supported_delay_seconds=_row_int(row, "max_supported_delay_seconds"),
        lookback_seconds=_row_int(row, "lookback_seconds"),
        feature_history_seconds=_row_int(row, "feature_history_seconds"),
        sample_count=_row_int(row, "sample_count"),
        max_candidate_slots=_row_int(row, "max_candidate_slots"),
        n_rows_available=_row_int(row, "n_rows_available"),
        n_rows_used=_row_int(row, "n_rows_used"),
        split_sizes=SplitSizes(
            train_samples=_row_int(row, "train_samples"),
            validation_samples=_row_int(row, "validation_samples"),
            test_samples=_row_int(row, "test_samples"),
        ),
        best_epoch=_row_int(row, "best_epoch"),
        resolved_device=_row_str(row, "resolved_device"),
        resolved_precision=_row_str(row, "resolved_precision"),
        compiled=bool(_row_value(row, "compiled")),
        best_validation_metrics=epoch_metrics_from_payload(
            _row_value(row, "best_validation_metrics")
        ),
        test_metrics=epoch_metrics_from_payload(_row_value(row, "test_metrics")),
    )


def training_epoch_values(record: TrainingEpochRecord) -> dict[str, object]:
    return {
        "epoch": record.epoch,
        "train_metrics": epoch_metrics_values(record.train_metrics),
        "validation_metrics": epoch_metrics_values(record.validation_metrics),
    }


def training_epoch_from_row(row: RowMapping) -> TrainingEpochRecord:
    from .results import TrainingEpochRecord

    return TrainingEpochRecord(
        epoch=_row_int(row, "epoch"),
        train_metrics=epoch_metrics_from_payload(_row_value(row, "train_metrics")),
        validation_metrics=epoch_metrics_from_payload(_row_value(row, "validation_metrics")),
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
    row: RowMapping,
    *,
    runs: list[SimulationRunSummary],
) -> SimulationSummaryRecord:
    from .results import SimulationSummaryRecord

    return SimulationSummaryRecord(
        artifact_id=_row_str(row, "artifact_id"),
        objective_id=_row_str(row, "objective_id"),
        chain=_row_str(row, "chain_name"),
        dataset_id=_row_str(row, "dataset_id"),
        dataset_name=_row_str(row, "dataset_name"),
        variant=ArtifactVariant(_row_str(row, "variant")),
        study=study_config_from_name(_row_value(row, "study_name")),
        study_id=_row_optional_str(row, "study_id"),
        model_id=_row_str(row, "model_id"),
        task_id=_row_str(row, "task_id"),
        max_supported_delay_seconds=_row_int(row, "max_supported_delay_seconds"),
        requested_delay_seconds=_row_int(row, "requested_delay_seconds"),
        lookback_seconds=_row_int(row, "lookback_seconds"),
        feature_history_seconds=_row_int(row, "feature_history_seconds"),
        simulation_window_seconds=_row_int(row, "simulation_window_seconds"),
        arrival_rate_per_second=_row_float(row, "arrival_rate_per_second"),
        repetitions=_row_int(row, "repetitions"),
        n_history_rows=_row_int(row, "n_history_rows"),
        n_evaluation_rows=_row_int(row, "n_evaluation_rows"),
        sample_count=_row_int(row, "sample_count"),
        max_candidate_slots=_row_int(row, "max_candidate_slots"),
        profit_over_baseline=_row_float(row, "profit_over_baseline"),
        cost_over_optimum=_row_float(row, "cost_over_optimum"),
        baseline_cost_over_optimum=_row_float(row, "baseline_cost_over_optimum"),
        realized_fee_sum=_row_float(row, "realized_fee_sum"),
        baseline_fee_sum=_row_float(row, "baseline_fee_sum"),
        optimum_fee_sum=_row_float(row, "optimum_fee_sum"),
        window_profit_over_baseline=window_metric_from_payload(
            _row_value(row, "window_profit_over_baseline")
        ),
        window_cost_over_optimum=window_metric_from_payload(
            _row_value(row, "window_cost_over_optimum")
        ),
        window_baseline_cost_over_optimum=window_metric_from_payload(
            _row_value(row, "window_baseline_cost_over_optimum")
        ),
        total_events=_row_int(row, "total_events"),
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


def simulation_run_from_row(row: RowMapping) -> SimulationRunSummary:
    from .simulation import SimulationRunSummary

    return SimulationRunSummary(
        window_start_timestamp=_row_float(row, "window_start_timestamp"),
        window_end_timestamp=_row_float(row, "window_end_timestamp"),
        n_arrivals=_row_int(row, "n_arrivals"),
        n_events=_row_int(row, "n_events"),
        profit_over_baseline=_row_float(row, "profit_over_baseline"),
        cost_over_optimum=_row_float(row, "cost_over_optimum"),
        baseline_cost_over_optimum=_row_float(row, "baseline_cost_over_optimum"),
        realized_fee_sum=_row_float(row, "realized_fee_sum"),
        baseline_fee_sum=_row_float(row, "baseline_fee_sum"),
        optimum_fee_sum=_row_float(row, "optimum_fee_sum"),
    )
