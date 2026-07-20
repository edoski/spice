"""Resolved evaluation facts and canonical scientific reduction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast
from uuid import UUID

import polars as pl

from ..addresses import evaluation_json_path, evaluation_observations_path
from ..config import (
    BaselineSource,
    EvaluateRequest,
    ExperimentSemantics,
    Method,
    TrainingDefinition,
    TrainingSource,
)
from ..corpus import Corpus, load_corpus
from ..modeling import load_artifact
from ..study import training_definition_from_method

_OBSERVATION_SCHEMA = pl.Schema(
    {
        "origin_block": pl.Int64,
        "origin_timestamp": pl.Int64,
        "selected_action_k": pl.Int64,
        "earliest_hindsight_action_k": pl.Int64,
        "classification_loss_contribution": pl.Float64,
        "predicted_hindsight_minimum_base_fee_z": pl.Float32,
        "previous_closed_parent_base_fee_per_gas": pl.Int64,
        "closed_parent_base_fee_per_gas": pl.Int64,
        "immediate_k0_base_fee_per_gas": pl.Int64,
        "selected_target_base_fee_per_gas": pl.Int64,
        "hindsight_minimum_base_fee_per_gas": pl.Int64,
        "selected_action_wait_seconds": pl.Int64,
        "full_horizon_elapsed_seconds": pl.Int64,
    }
)

_RESULT_SCHEMA = pl.Schema(
    {
        "evaluation_id": pl.String,
        "eligible_origin_count": pl.Int64,
        "earliest_hindsight_label_correct_count": pl.Int64,
        "earliest_hindsight_label_cross_entropy_loss_sum": pl.Float64,
        "hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss_sum": pl.Float64,
        "hindsight_minimum_base_fee_per_gas_within_k_natural_log_absolute_error_sum": pl.Float64,
        "hindsight_minimum_base_fee_per_gas_within_k_natural_log_squared_error_sum": pl.Float64,
        "earliest_hindsight_label_cross_entropy_loss": pl.Float64,
        "hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss": pl.Float64,
        "hindsight_minimum_base_fee_per_gas_within_k_natural_log_mae": pl.Float64,
        "hindsight_minimum_base_fee_per_gas_within_k_natural_log_mse": pl.Float64,
        "multitask_total_loss": pl.Float64,
        "earliest_hindsight_label_accuracy": pl.Float64,
        "earliest_hindsight_label_macro_f1": pl.Float64,
        "immediate_k0_base_fee_per_gas_sum": pl.Float64,
        "finite_target_base_fee_per_gas_savings_sum": pl.Float64,
        "finite_target_base_fee_per_gas_hindsight_opportunity_sum": pl.Float64,
        "finite_target_base_fee_per_gas_hindsight_regret_sum": pl.Float64,
        "finite_target_base_fee_per_gas_savings_ratio_vs_immediate_k0": pl.Float64,
        "finite_target_base_fee_per_gas_hindsight_opportunity_ratio_vs_immediate_k0": pl.Float64,
        "finite_target_base_fee_per_gas_hindsight_regret_ratio_vs_immediate_k0": pl.Float64,
        "signed_captured_hindsight_opportunity_ratio": pl.Float64,
        "target_base_fee_per_gas_savings_fraction_vs_immediate_k0_sum": pl.Float64,
        "target_base_fee_per_gas_savings_fraction_vs_immediate_k0_defined_origin_count": pl.Int64,
        (
            "target_base_fee_per_gas_savings_fraction_vs_immediate_k0_"
            "zero_denominator_exclusion_count"
        ): pl.Int64,
        "mean_origin_target_base_fee_per_gas_savings_fraction_vs_immediate_k0": pl.Float64,
        (
            "selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_sum"
        ): pl.Float64,
        (
            "selected_target_base_fee_per_gas_increase_fraction_vs_"
            "hindsight_best_within_k_defined_origin_count"
        ): pl.Int64,
        (
            "selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_"
            "zero_denominator_exclusion_count"
        ): pl.Int64,
        (
            "mean_origin_selected_target_base_fee_per_gas_increase_fraction_"
            "vs_hindsight_best_within_k"
        ): pl.Float64,
        (
            "immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_sum"
        ): pl.Float64,
        (
            "immediate_k0_base_fee_per_gas_increase_fraction_vs_"
            "hindsight_best_within_k_defined_origin_count"
        ): pl.Int64,
        (
            "immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_"
            "zero_denominator_exclusion_count"
        ): pl.Int64,
        (
            "mean_origin_immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k"
        ): pl.Float64,
        "harmful_action_count": pl.Int64,
        "harmful_action_rate": pl.Float64,
        "selected_action_count_by_k": pl.List(pl.Int64),
        "extra_wait_block_opportunities_vs_immediate_k0_sum": pl.Float64,
        "mean_extra_wait_block_opportunities_vs_immediate_k0": pl.Float64,
        "selected_action_wait_seconds_sum": pl.Float64,
        "mean_selected_action_wait_seconds": pl.Float64,
        "full_horizon_elapsed_seconds_sum": pl.Float64,
        "mean_full_horizon_elapsed_seconds": pl.Float64,
    }
)
_RESULT_COLUMNS = tuple(_RESULT_SCHEMA.names())
_FLOAT_RESULT_COLUMNS = tuple(name for name, dtype in _RESULT_SCHEMA.items() if dtype == pl.Float64)


@dataclass(frozen=True, slots=True)
class ResolvedEvaluation:
    """Trusted facts needed by evaluation evidence consumers."""

    request: EvaluateRequest
    training_source: TrainingSource
    training_definition: TrainingDefinition
    corpus: Corpus
    observations: pl.LazyFrame
    reduction: pl.DataFrame
    trainable_parameter_count: int


@dataclass(frozen=True, slots=True)
class _ArtifactResolution:
    training_source: TrainingSource
    training_definition: TrainingDefinition
    target_mean: float
    target_standard_deviation: float
    trainable_parameter_count: int


@dataclass(frozen=True, slots=True)
class _ReductionResolution:
    request: EvaluateRequest
    training_source: TrainingSource
    training_definition: TrainingDefinition
    observations: pl.LazyFrame
    reduction: pl.DataFrame
    trainable_parameter_count: int


def reduce_evaluation(storage_root: Path, evaluation_id: UUID) -> pl.DataFrame:
    """Reduce one canonical evaluation to one fixed scientific-facts row."""

    return _resolve_reduction(storage_root, evaluation_id, {}).reduction


def resolve_evaluations(
    storage_root: Path,
    evaluation_ids: tuple[UUID, ...],
) -> tuple[ResolvedEvaluation, ...]:
    """Resolve ordered evaluation IDs into trusted shared evidence state."""

    artifacts: dict[UUID, _ArtifactResolution] = {}
    corpora: dict[UUID, Corpus] = {}
    evaluations: dict[UUID, ResolvedEvaluation] = {}
    resolved: list[ResolvedEvaluation] = []
    for evaluation_id in evaluation_ids:
        evaluation = evaluations.get(evaluation_id)
        if evaluation is None:
            reduction = _resolve_reduction(storage_root, evaluation_id, artifacts)
            corpus_id = reduction.request.corpus_id
            corpus = corpora.get(corpus_id)
            if corpus is None:
                corpus = load_corpus(storage_root, corpus_id)
                corpora[corpus_id] = corpus
            evaluation = ResolvedEvaluation(
                request=reduction.request,
                training_source=reduction.training_source,
                training_definition=reduction.training_definition,
                corpus=corpus,
                observations=reduction.observations,
                reduction=reduction.reduction,
                trainable_parameter_count=reduction.trainable_parameter_count,
            )
            evaluations[evaluation_id] = evaluation
        resolved.append(evaluation)
    return tuple(resolved)


def _resolve_reduction(
    storage_root: Path,
    evaluation_id: UUID,
    artifacts: dict[UUID, _ArtifactResolution],
) -> _ReductionResolution:
    request = EvaluateRequest.model_validate_json(
        evaluation_json_path(storage_root, evaluation_id).read_text(encoding="utf-8"),
        strict=True,
    )
    if request.evaluation_id != evaluation_id:
        raise ValueError("evaluation request ID must match the requested evaluation")

    artifact = artifacts.get(request.artifact_id)
    if artifact is None:
        artifact = _resolve_artifact(storage_root, request.artifact_id)
        artifacts[request.artifact_id] = artifact
    source = artifact.training_source
    if source.corpus_id != request.corpus_id:
        raise ValueError("artifact source Corpus must match the evaluation Corpus")
    definition = artifact.training_definition
    experiment = definition.experiment
    if request.window.role == "validation":
        if request.window != experiment.validation_window:
            raise ValueError("validation window must match the artifact experiment")
    elif (
        experiment.validation_window.last_parent_block + experiment.horizon_blocks
        >= request.window.first_parent_block
    ):
        raise ValueError("testing window must follow complete validation outcomes")

    observations_path = evaluation_observations_path(storage_root, evaluation_id)
    if pl.read_parquet_schema(observations_path) != _OBSERVATION_SCHEMA:
        raise ValueError("observations must have the canonical ordered schema")
    observations = pl.scan_parquet(observations_path)
    reduction = _reduce_observations(
        evaluation_id,
        request,
        experiment,
        artifact.target_mean,
        artifact.target_standard_deviation,
        observations,
    )
    return _ReductionResolution(
        request=request,
        training_source=source,
        training_definition=definition,
        observations=observations,
        reduction=reduction,
        trainable_parameter_count=artifact.trainable_parameter_count,
    )


def _resolve_artifact(storage_root: Path, artifact_id: UUID) -> _ArtifactResolution:
    association, model = load_artifact(storage_root, artifact_id)
    source = association.request.source
    definition = (
        source.training_definition
        if isinstance(source, BaselineSource)
        else training_definition_from_method(source.experiment, cast(Method, association.method))
    )
    trainable_parameter_count = sum(
        parameter.numel() for parameter in model.parameters() if parameter.requires_grad
    )
    return _ArtifactResolution(
        training_source=source,
        training_definition=definition,
        target_mean=association.target_state.mean,
        target_standard_deviation=association.target_state.standard_deviation,
        trainable_parameter_count=trainable_parameter_count,
    )


def _reduce_observations(
    evaluation_id: UUID,
    request: EvaluateRequest,
    experiment: ExperimentSemantics,
    target_mean: float,
    target_standard_deviation: float,
    observations: pl.LazyFrame,
) -> pl.DataFrame:

    expected_origin_count = request.window.last_parent_block - request.window.first_parent_block + 1
    horizon_blocks = experiment.horizon_blocks
    loss_definition = experiment.loss

    immediate_fee = pl.col("immediate_k0_base_fee_per_gas")
    selected_fee = pl.col("selected_target_base_fee_per_gas")
    hindsight_fee = pl.col("hindsight_minimum_base_fee_per_gas")
    target_log = hindsight_fee.cast(pl.Float64).log()
    target_z = (
        (target_log - pl.lit(target_mean, dtype=pl.Float64))
        / pl.lit(target_standard_deviation, dtype=pl.Float64)
    ).cast(pl.Float32)
    predicted_z = pl.col("predicted_hindsight_minimum_base_fee_z")
    error = predicted_z - pl.col("_target_z")
    absolute_error = error.abs()
    half = pl.lit(0.5, dtype=pl.Float32)
    threshold = pl.lit(loss_definition.regression_threshold, dtype=pl.Float32)
    regression_scale = pl.lit(loss_definition.regression_scale, dtype=pl.Float32)
    smooth_l1 = (
        pl.when(absolute_error < threshold)
        .then(half * error * error / threshold)
        .otherwise(absolute_error - half * threshold)
        * regression_scale
    )
    predicted_log = pl.lit(target_mean, dtype=pl.Float64) + pl.lit(
        target_standard_deviation,
        dtype=pl.Float64,
    ) * predicted_z.cast(pl.Float64)

    per_origin = observations.with_columns(
        (immediate_fee - selected_fee).alias("_savings"),
        (immediate_fee - hindsight_fee).alias("_opportunity"),
        (selected_fee - hindsight_fee).alias("_regret"),
        (selected_fee > immediate_fee).alias("_harmful"),
        target_z.alias("_target_z"),
        (predicted_log - target_log).alias("_log_error"),
    ).with_columns(smooth_l1.alias("_smooth_l1"))

    selected_action_count_by_k: list[pl.Expr] = []
    f1_by_k: list[pl.Expr] = []
    active_by_k: list[pl.Expr] = []
    for action_k in range(horizon_blocks):
        support = (pl.col("earliest_hindsight_action_k") == action_k).sum().cast(pl.Int64)
        prediction = (pl.col("selected_action_k") == action_k).sum().cast(pl.Int64)
        true_positive = (
            (
                (pl.col("selected_action_k") == action_k)
                & (pl.col("earliest_hindsight_action_k") == action_k)
            )
            .sum()
            .cast(pl.Int64)
        )
        selected_action_count_by_k.append(prediction)
        denominator = support + prediction
        active = denominator > 0
        active_by_k.append(active.cast(pl.Int64))
        f1_by_k.append(
            pl.when(active)
            .then(pl.lit(2.0) * true_positive.cast(pl.Float64) / denominator.cast(pl.Float64))
            .otherwise(pl.lit(0.0))
        )

    no_nulls = (
        pl.sum_horizontal([pl.col(name).null_count() for name in _OBSERVATION_SCHEMA.names()]) == 0
    )
    expected_origins = pl.int_range(0, pl.len(), dtype=pl.Int64) + pl.lit(
        request.window.first_parent_block,
        dtype=pl.Int64,
    )
    valid_inputs = pl.all_horizontal(
        pl.len() == expected_origin_count,
        no_nulls,
        (pl.col("origin_block") == expected_origins).all(),
        (pl.col("origin_timestamp") >= 0).all(),
        pl.col("classification_loss_contribution").is_finite().all(),
        (pl.col("classification_loss_contribution") >= 0.0).all(),
        predicted_z.is_finite().all(),
        (pl.col("selected_action_k") >= 0).all(),
        (pl.col("selected_action_k") < horizon_blocks).all(),
        (pl.col("earliest_hindsight_action_k") >= 0).all(),
        (pl.col("earliest_hindsight_action_k") < horizon_blocks).all(),
        (pl.col("previous_closed_parent_base_fee_per_gas") > 0).all(),
        (pl.col("closed_parent_base_fee_per_gas") > 0).all(),
        (immediate_fee > 0).all(),
        (selected_fee > 0).all(),
        (hindsight_fee > 0).all(),
        (hindsight_fee <= immediate_fee).all(),
        (hindsight_fee <= selected_fee).all(),
        (pl.col("selected_action_wait_seconds") >= 0).all(),
        (pl.col("full_horizon_elapsed_seconds") >= 0).all(),
        ((pl.col("selected_action_k") != 0) | (pl.col("selected_action_wait_seconds") == 0)).all(),
        (pl.col("selected_action_wait_seconds") <= pl.col("full_horizon_elapsed_seconds")).all(),
    )

    totals = per_origin.select(
        pl.lit(str(evaluation_id)).alias("evaluation_id"),
        pl.len().cast(pl.Int64).alias("eligible_origin_count"),
        (pl.col("selected_action_k") == pl.col("earliest_hindsight_action_k"))
        .sum()
        .cast(pl.Int64)
        .alias("earliest_hindsight_label_correct_count"),
        pl.col("classification_loss_contribution")
        .sum()
        .alias("earliest_hindsight_label_cross_entropy_loss_sum"),
        pl.col("_smooth_l1")
        .cast(pl.Float64)
        .sum()
        .alias("hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss_sum"),
        pl.col("_log_error")
        .abs()
        .sum()
        .alias("hindsight_minimum_base_fee_per_gas_within_k_natural_log_absolute_error_sum"),
        (pl.col("_log_error") * pl.col("_log_error"))
        .sum()
        .alias("hindsight_minimum_base_fee_per_gas_within_k_natural_log_squared_error_sum"),
        immediate_fee.cast(pl.Float64).sum().alias("immediate_k0_base_fee_per_gas_sum"),
        pl.col("_savings")
        .cast(pl.Float64)
        .sum()
        .alias("finite_target_base_fee_per_gas_savings_sum"),
        pl.col("_opportunity")
        .cast(pl.Float64)
        .sum()
        .alias("finite_target_base_fee_per_gas_hindsight_opportunity_sum"),
        pl.col("_regret")
        .cast(pl.Float64)
        .sum()
        .alias("finite_target_base_fee_per_gas_hindsight_regret_sum"),
        pl.col("_opportunity").sum().alias("_exact_opportunity_sum"),
        (pl.col("_savings").cast(pl.Float64) / immediate_fee.cast(pl.Float64))
        .sum()
        .alias("target_base_fee_per_gas_savings_fraction_vs_immediate_k0_sum"),
        pl.len()
        .cast(pl.Int64)
        .alias("target_base_fee_per_gas_savings_fraction_vs_immediate_k0_defined_origin_count"),
        pl.lit(0, dtype=pl.Int64).alias(
            "target_base_fee_per_gas_savings_fraction_vs_immediate_k0_zero_denominator_exclusion_count"
        ),
        (pl.col("_regret").cast(pl.Float64) / hindsight_fee.cast(pl.Float64))
        .sum()
        .alias("selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_sum"),
        pl.len()
        .cast(pl.Int64)
        .alias(
            "selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_defined_origin_count"
        ),
        pl.lit(0, dtype=pl.Int64).alias(
            "selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_zero_denominator_exclusion_count"
        ),
        (pl.col("_opportunity").cast(pl.Float64) / hindsight_fee.cast(pl.Float64))
        .sum()
        .alias("immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_sum"),
        pl.len()
        .cast(pl.Int64)
        .alias(
            "immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_defined_origin_count"
        ),
        pl.lit(0, dtype=pl.Int64).alias(
            "immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_zero_denominator_exclusion_count"
        ),
        pl.col("_harmful").sum().cast(pl.Int64).alias("harmful_action_count"),
        pl.concat_list(selected_action_count_by_k).alias("selected_action_count_by_k"),
        pl.col("selected_action_k")
        .cast(pl.Float64)
        .sum()
        .alias("extra_wait_block_opportunities_vs_immediate_k0_sum"),
        pl.col("selected_action_wait_seconds")
        .cast(pl.Float64)
        .sum()
        .alias("selected_action_wait_seconds_sum"),
        pl.col("full_horizon_elapsed_seconds")
        .cast(pl.Float64)
        .sum()
        .alias("full_horizon_elapsed_seconds_sum"),
        (pl.sum_horizontal(f1_by_k) / pl.sum_horizontal(active_by_k)).alias(
            "earliest_hindsight_label_macro_f1"
        ),
        valid_inputs.alias("_valid_inputs"),
    )

    origin_count = pl.col("eligible_origin_count").cast(pl.Float64)
    savings_sum = pl.col("finite_target_base_fee_per_gas_savings_sum")
    opportunity_sum = pl.col("finite_target_base_fee_per_gas_hindsight_opportunity_sum")
    regret_sum = pl.col("finite_target_base_fee_per_gas_hindsight_regret_sum")
    immediate_sum = pl.col("immediate_k0_base_fee_per_gas_sum")
    result_plan = totals.with_columns(
        (pl.col("earliest_hindsight_label_cross_entropy_loss_sum") / origin_count).alias(
            "earliest_hindsight_label_cross_entropy_loss"
        ),
        (
            pl.col("hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss_sum") / origin_count
        ).alias("hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss"),
        (
            pl.col("hindsight_minimum_base_fee_per_gas_within_k_natural_log_absolute_error_sum")
            / origin_count
        ).alias("hindsight_minimum_base_fee_per_gas_within_k_natural_log_mae"),
        (
            pl.col("hindsight_minimum_base_fee_per_gas_within_k_natural_log_squared_error_sum")
            / origin_count
        ).alias("hindsight_minimum_base_fee_per_gas_within_k_natural_log_mse"),
        (
            (
                pl.col("earliest_hindsight_label_cross_entropy_loss_sum")
                + pl.col("hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss_sum")
            )
            / origin_count
        ).alias("multitask_total_loss"),
        (pl.col("earliest_hindsight_label_correct_count").cast(pl.Float64) / origin_count).alias(
            "earliest_hindsight_label_accuracy"
        ),
        (savings_sum / immediate_sum).alias(
            "finite_target_base_fee_per_gas_savings_ratio_vs_immediate_k0"
        ),
        (opportunity_sum / immediate_sum).alias(
            "finite_target_base_fee_per_gas_hindsight_opportunity_ratio_vs_immediate_k0"
        ),
        (regret_sum / immediate_sum).alias(
            "finite_target_base_fee_per_gas_hindsight_regret_ratio_vs_immediate_k0"
        ),
        pl.when(pl.col("_exact_opportunity_sum") == 0)
        .then(pl.lit(None, dtype=pl.Float64))
        .otherwise(savings_sum / opportunity_sum)
        .alias("signed_captured_hindsight_opportunity_ratio"),
        (
            pl.col("target_base_fee_per_gas_savings_fraction_vs_immediate_k0_sum") / origin_count
        ).alias("mean_origin_target_base_fee_per_gas_savings_fraction_vs_immediate_k0"),
        (
            pl.col(
                "selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_sum"
            )
            / origin_count
        ).alias(
            "mean_origin_selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k"
        ),
        (
            pl.col("immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_sum")
            / origin_count
        ).alias(
            "mean_origin_immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k"
        ),
        (pl.col("harmful_action_count").cast(pl.Float64) / origin_count).alias(
            "harmful_action_rate"
        ),
        (pl.col("extra_wait_block_opportunities_vs_immediate_k0_sum") / origin_count).alias(
            "mean_extra_wait_block_opportunities_vs_immediate_k0"
        ),
        (pl.col("selected_action_wait_seconds_sum") / origin_count).alias(
            "mean_selected_action_wait_seconds"
        ),
        (pl.col("full_horizon_elapsed_seconds_sum") / origin_count).alias(
            "mean_full_horizon_elapsed_seconds"
        ),
    ).with_columns(
        pl.all_horizontal(
            [pl.col(name).is_finite().fill_null(True) for name in _FLOAT_RESULT_COLUMNS]
        ).alias("_finite_results"),
        pl.all_horizontal(
            [
                pl.col(name).is_not_null()
                for name in _RESULT_COLUMNS
                if name != "signed_captured_hindsight_opportunity_ratio"
            ]
        ).alias("_nonnull_results"),
    )

    result = result_plan.select(
        *_RESULT_COLUMNS,
        "_valid_inputs",
        "_finite_results",
        "_nonnull_results",
    ).collect()
    if not all(
        result[name].item() is True
        for name in ("_valid_inputs", "_finite_results", "_nonnull_results")
    ):
        raise ValueError("evaluation observations contain invalid scientific facts")
    result.drop_in_place("_valid_inputs")
    result.drop_in_place("_finite_results")
    result.drop_in_place("_nonnull_results")
    return result


__all__ = ["ResolvedEvaluation", "reduce_evaluation", "resolve_evaluations"]
