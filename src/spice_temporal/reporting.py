"""Structured report artifacts for training runs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from spice_temporal.config import ChainConfig, ModelFamily
from spice_temporal.pipeline import TrainingRunResult


@dataclass(slots=True)
class SplitSizes:
    train_examples: int
    validation_examples: int
    test_examples: int


@dataclass(slots=True)
class TestMetricsReport:
    total_loss: float
    accuracy: float
    mean_cost_over_optimum: float
    mean_profit_over_baseline: float


@dataclass(slots=True)
class TrainingRunReport:
    input_path: str
    chain: str
    family: ModelFamily
    max_delay_seconds: int
    device_requested: str
    lookback_seconds: int
    block_time_seconds: float
    max_extra_wait_steps: int
    n_blocks: int
    lookback_steps: int
    candidate_block_count: int
    n_features: int
    n_classes: int
    split_sizes: SplitSizes
    best_epoch: int
    test_metrics: TestMetricsReport


def build_training_run_report(
    result: TrainingRunResult,
    *,
    block_path: Path,
    chain: ChainConfig,
    family: ModelFamily,
    max_delay_seconds: int,
    device_requested: str,
    lookback_seconds: int,
) -> TrainingRunReport:
    prepared = result.prepared
    metrics = result.test_metrics
    return TrainingRunReport(
        input_path=str(block_path),
        chain=chain.name,
        family=family,
        max_delay_seconds=max_delay_seconds,
        device_requested=device_requested,
        lookback_seconds=lookback_seconds,
        block_time_seconds=chain.block_time_seconds,
        max_extra_wait_steps=prepared.max_extra_wait_steps,
        n_blocks=prepared.n_blocks,
        lookback_steps=prepared.lookback_steps,
        candidate_block_count=prepared.candidate_block_count,
        n_features=prepared.n_features,
        n_classes=prepared.n_classes,
        split_sizes=SplitSizes(
            train_examples=len(prepared.train_examples),
            validation_examples=len(prepared.validation_examples),
            test_examples=len(prepared.test_examples),
        ),
        best_epoch=result.training_result.best_epoch,
        test_metrics=TestMetricsReport(
            total_loss=metrics.total_loss,
            accuracy=metrics.accuracy,
            mean_cost_over_optimum=metrics.mean_cost_over_optimum,
            mean_profit_over_baseline=metrics.mean_profit_over_baseline,
        ),
    )


def write_training_run_report(path: Path, report: TrainingRunReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(asdict(report), handle, ensure_ascii=True, indent=2)
