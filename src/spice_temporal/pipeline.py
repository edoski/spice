"""End-to-end orchestration for one training run."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from spice_temporal.config import ChainConfig, ModelConfig, SplitConfig, TrainingConfig
from spice_temporal.datasets import (
    build_supervised_examples,
    candidate_block_count_for_delay,
    chronological_split,
    lookback_steps_for_seconds,
    max_extra_wait_steps_for_delay,
)
from spice_temporal.features import build_feature_rows
from spice_temporal.io import load_block_records
from spice_temporal.models import build_model
from spice_temporal.normalization import StandardScaler, fit_standard_scaler, transform_examples
from spice_temporal.records import BlockRecord, SupervisedExample
from spice_temporal.torch_datasets import build_class_weights
from spice_temporal.training import EpochMetrics, TrainingResult, evaluate_model, train_model


@dataclass(slots=True)
class PreparedDataset:
    n_blocks: int
    train_examples: list[SupervisedExample]
    validation_examples: list[SupervisedExample]
    test_examples: list[SupervisedExample]
    scaler: StandardScaler
    lookback_steps: int
    max_extra_wait_steps: int
    candidate_block_count: int
    n_features: int
    n_classes: int


@dataclass(slots=True)
class TrainingRunResult:
    prepared: PreparedDataset
    training_result: TrainingResult
    test_metrics: EpochMetrics


def prepare_dataset(
    blocks: list[BlockRecord],
    *,
    chain: ChainConfig,
    max_delay_seconds: int,
    lookback_seconds: int,
    split_config: SplitConfig,
) -> PreparedDataset:
    feature_rows = build_feature_rows(blocks)
    lookback_steps = lookback_steps_for_seconds(lookback_seconds, chain.block_time_seconds)
    max_extra_wait_steps = max_extra_wait_steps_for_delay(
        max_delay_seconds,
        chain.block_time_seconds,
    )
    candidate_block_count = candidate_block_count_for_delay(
        max_delay_seconds,
        chain.block_time_seconds,
    )
    examples = build_supervised_examples(
        feature_rows,
        lookback_steps=lookback_steps,
        candidate_block_count=candidate_block_count,
    )
    split = chronological_split(examples, split_config)
    if not split.train or not split.validation or not split.test:
        raise ValueError("Dataset split produced an empty partition; provide more block history")
    scaler = fit_standard_scaler(split.train)
    train_examples = transform_examples(split.train, scaler)
    validation_examples = transform_examples(split.validation, scaler)
    test_examples = transform_examples(split.test, scaler)
    return PreparedDataset(
        n_blocks=len(blocks),
        train_examples=train_examples,
        validation_examples=validation_examples,
        test_examples=test_examples,
        scaler=scaler,
        lookback_steps=lookback_steps,
        max_extra_wait_steps=max_extra_wait_steps,
        candidate_block_count=candidate_block_count,
        n_features=len(train_examples[0].inputs[0]),
        n_classes=len(train_examples[0].candidate_log_fees),
    )


def run_training(
    block_path: Path,
    *,
    chain: ChainConfig,
    max_delay_seconds: int,
    lookback_seconds: int,
    model_config: ModelConfig,
    training_config: TrainingConfig,
    split_config: SplitConfig,
) -> TrainingRunResult:
    blocks = load_block_records(block_path)
    prepared = prepare_dataset(
        blocks,
        chain=chain,
        max_delay_seconds=max_delay_seconds,
        lookback_seconds=lookback_seconds,
        split_config=split_config,
    )
    model = build_model(prepared.n_features, prepared.n_classes, model_config)
    training_result = train_model(
        model,
        train_examples=prepared.train_examples,
        validation_examples=prepared.validation_examples,
        config=training_config,
    )
    class_weights = build_class_weights(prepared.train_examples, prepared.n_classes)
    test_metrics = evaluate_model(
        model,
        examples=prepared.test_examples,
        training_config=training_config,
        class_weights=class_weights,
    )
    return TrainingRunResult(
        prepared=prepared,
        training_result=training_result,
        test_metrics=test_metrics,
    )
