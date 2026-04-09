"""Training and inference dataset preparation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from spice_temporal.config import ChainConfig, ModelConfig, SplitConfig, TrainingConfig
from spice_temporal.constants import EVALUATION_END_TS, EVALUATION_START_TS
from spice_temporal.contracts import TemporalModel
from spice_temporal.datasets import (
    DatasetGeometry,
    build_supervised_examples,
    chronological_split,
    derive_dataset_geometry,
    filter_examples_by_anchor_window,
    history_context_blocks,
    trim_history_blocks_for_target,
)
from spice_temporal.features import build_feature_rows
from spice_temporal.io import load_block_records
from spice_temporal.models import build_model
from spice_temporal.normalization import StandardScaler, fit_standard_scaler, transform_examples
from spice_temporal.records import BlockRecord, SupervisedExample
from spice_temporal.torch_datasets import build_class_weights
from spice_temporal.training import EpochMetrics, TrainingResult, evaluate_model, train_model


@dataclass(slots=True)
class PreparedTrainingDataset:
    n_blocks_available: int
    n_blocks_used: int
    n_examples_total: int
    train_examples: list[SupervisedExample]
    validation_examples: list[SupervisedExample]
    test_examples: list[SupervisedExample]
    scaler: StandardScaler
    geometry: DatasetGeometry
    n_features: int
    n_classes: int


@dataclass(slots=True)
class PreparedInferenceDataset:
    n_history_context_blocks: int
    n_evaluation_blocks: int
    n_examples_total: int
    examples: list[SupervisedExample]
    geometry: DatasetGeometry
    n_features: int


@dataclass(slots=True)
class TrainingRunResult:
    model: TemporalModel
    prepared: PreparedTrainingDataset
    training_result: TrainingResult
    test_metrics: EpochMetrics


def prepare_training_dataset(
    blocks: list[BlockRecord],
    *,
    chain: ChainConfig,
    max_delay_seconds: int,
    lookback_seconds: int,
    target_anchor_count: int,
    split_config: SplitConfig,
) -> PreparedTrainingDataset:
    geometry = derive_dataset_geometry(
        lookback_seconds=lookback_seconds,
        max_delay_seconds=max_delay_seconds,
        block_time_seconds=chain.block_time_seconds,
    )
    trimmed_blocks = trim_history_blocks_for_target(
        blocks,
        target_anchor_count=target_anchor_count,
        geometry=geometry,
    )
    feature_rows = build_feature_rows(trimmed_blocks)
    examples = build_supervised_examples(
        feature_rows,
        lookback_steps=geometry.lookback_steps,
        candidate_block_count=geometry.candidate_block_count,
    )
    if len(examples) != target_anchor_count:
        raise RuntimeError(
            "Training dataset preparation produced an unexpected number of anchors; "
            f"expected {target_anchor_count}, got {len(examples)}"
        )

    split = chronological_split(examples, split_config)
    if not split.train or not split.validation or not split.test:
        raise ValueError("Dataset split produced an empty partition; provide more block history")

    scaler = fit_standard_scaler(split.train)
    train_examples = transform_examples(split.train, scaler)
    validation_examples = transform_examples(split.validation, scaler)
    test_examples = transform_examples(split.test, scaler)
    return PreparedTrainingDataset(
        n_blocks_available=len(blocks),
        n_blocks_used=len(trimmed_blocks),
        n_examples_total=len(examples),
        train_examples=train_examples,
        validation_examples=validation_examples,
        test_examples=test_examples,
        scaler=scaler,
        geometry=geometry,
        n_features=len(train_examples[0].inputs[0]),
        n_classes=len(train_examples[0].candidate_log_fees),
    )


def prepare_inference_dataset(
    history_blocks: list[BlockRecord],
    evaluation_blocks: list[BlockRecord],
    *,
    geometry: DatasetGeometry,
    scaler: StandardScaler,
) -> PreparedInferenceDataset:
    context_blocks = history_context_blocks(history_blocks, geometry=geometry)
    combined_blocks = [*context_blocks, *evaluation_blocks]
    feature_rows = build_feature_rows(combined_blocks)
    examples = build_supervised_examples(
        feature_rows,
        lookback_steps=geometry.lookback_steps,
        candidate_block_count=geometry.candidate_block_count,
    )
    evaluation_examples = filter_examples_by_anchor_window(
        examples,
        start_timestamp=EVALUATION_START_TS,
        end_timestamp=EVALUATION_END_TS,
    )
    if not evaluation_examples:
        raise ValueError("Evaluation dataset produced no valid inference examples")

    transformed_examples = transform_examples(evaluation_examples, scaler)
    return PreparedInferenceDataset(
        n_history_context_blocks=len(context_blocks),
        n_evaluation_blocks=len(evaluation_blocks),
        n_examples_total=len(transformed_examples),
        examples=transformed_examples,
        geometry=geometry,
        n_features=len(transformed_examples[0].inputs[0]),
    )


def run_training(
    history_block_path: Path,
    *,
    chain: ChainConfig,
    max_delay_seconds: int,
    lookback_seconds: int,
    target_anchor_count: int,
    model_config: ModelConfig,
    training_config: TrainingConfig,
    split_config: SplitConfig,
) -> TrainingRunResult:
    blocks = load_block_records(history_block_path)
    prepared = prepare_training_dataset(
        blocks,
        chain=chain,
        max_delay_seconds=max_delay_seconds,
        lookback_seconds=lookback_seconds,
        target_anchor_count=target_anchor_count,
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
        model=model,
        prepared=prepared,
        training_result=training_result,
        test_metrics=test_metrics,
    )
