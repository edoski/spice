"""Disposable exact-evaluation collection and consumer prototype for Issue 35."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from uuid import UUID

import polars as pl
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

OBSERVATION_SCHEMA = pl.Schema(
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

SEALED_COLUMNS = (
    "selected_action_k",
    "earliest_hindsight_action_k",
    "classification_loss_contribution",
    "predicted_hindsight_minimum_base_fee_z",
    "immediate_k0_base_fee_per_gas",
    "selected_target_base_fee_per_gas",
    "hindsight_minimum_base_fee_per_gas",
    "selected_action_wait_seconds",
    "full_horizon_elapsed_seconds",
)


class AuthorityError(ValueError):
    """One exact authority object is missing or malformed."""


class EvaluateRequest(BaseModel):
    """Prototype envelope; the production Window type remains owned by Issue 46."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    workflow: Literal["evaluate"]
    evaluation_id: UUID
    artifact_id: UUID
    corpus_id: UUID
    window: dict[str, object]

    @field_validator("window")
    @classmethod
    def require_nonempty_window(_cls, value: dict[str, object]) -> dict[str, object]:
        if not value:
            raise ValueError("window must not be empty")
        return value


class CheckpointFacts(BaseModel):
    """Synthetic stand-in for facts returned by native Lightning loading."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    artifact_id: UUID
    action_width: int
    target_log_mean: float
    target_log_std: float

    @field_validator("action_width")
    @classmethod
    def require_positive_action_width(_cls, value: int) -> int:
        if isinstance(value, bool) or value <= 0:
            raise ValueError("action_width must be a positive integer")
        return value

    @field_validator("target_log_mean", "target_log_std")
    @classmethod
    def require_finite_target_fact(_cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("target fitted state must be finite")
        return value

    @field_validator("target_log_std")
    @classmethod
    def require_positive_target_std(_cls, value: float) -> float:
        if value <= 0:
            raise ValueError("target_log_std must be positive")
        return value


@dataclass(frozen=True, slots=True)
class EvaluationInput:
    evaluation_dir: Path
    checkpoint_path: Path | None = None


@dataclass(frozen=True, slots=True)
class LoadedInput:
    request: EvaluateRequest
    observations_path: Path
    checkpoint: CheckpointFacts | None


def exact_collection_paths(
    inputs: Sequence[EvaluationInput],
) -> tuple[Path, ...]:
    """Return an ephemeral ordered copy list, never a persisted manifest."""
    loaded = _load_inputs(inputs)
    paths: list[Path] = []
    for item in loaded:
        paths.extend(
            (
                item.observations_path.parent / "evaluation.json",
                item.observations_path,
            )
        )
    seen_artifacts: set[UUID] = set()
    for source, item in zip(inputs, loaded, strict=True):
        if item.request.artifact_id in seen_artifacts:
            continue
        seen_artifacts.add(item.request.artifact_id)
        if source.checkpoint_path is None:
            raise AssertionError("validated checkpoint path cannot be None")
        paths.append(source.checkpoint_path)
    return tuple(paths)


def reduce_evaluations(
    inputs: Sequence[EvaluationInput],
) -> pl.DataFrame:
    """Validate every input first, then run the sole column-pruned reducer."""
    loaded = _load_inputs(inputs)
    return _sealed_rows(loaded)


def _load_inputs(
    inputs: Sequence[EvaluationInput],
) -> tuple[LoadedInput, ...]:
    if not inputs:
        raise AuthorityError("explicit evaluation path list must not be empty")
    loaded: list[LoadedInput] = []
    seen_ids: set[UUID] = set()
    for ordinal, source in enumerate(inputs):
        request_path = source.evaluation_dir / "evaluation.json"
        observations_path = source.evaluation_dir / "observations.parquet"
        request = _load_request(request_path)
        if request.evaluation_id in seen_ids:
            raise AuthorityError(
                f"input[{ordinal}] duplicates evaluation_id {request.evaluation_id}"
            )
        seen_ids.add(request.evaluation_id)
        if source.evaluation_dir.name != str(request.evaluation_id):
            raise AuthorityError(f"{request_path}: evaluation_id does not match directory name")
        _validate_observations(observations_path)
        if source.checkpoint_path is None:
            raise AuthorityError(
                f"{request.evaluation_id}: sealed summary requires its checkpoint path"
            )
        checkpoint = _load_checkpoint(source.checkpoint_path)
        if checkpoint.artifact_id != request.artifact_id:
            raise AuthorityError(
                f"{source.checkpoint_path}: artifact_id does not match evaluation request"
            )
        _validate_action_domain(
            observations_path,
            evaluation_id=request.evaluation_id,
            action_width=checkpoint.action_width,
        )
        loaded.append(
            LoadedInput(
                request=request,
                observations_path=observations_path,
                checkpoint=checkpoint,
            )
        )
    return tuple(loaded)


def _load_request(path: Path) -> EvaluateRequest:
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise AuthorityError(f"{path}: request must be a JSON object")
        return EvaluateRequest.model_validate_json(raw)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise AuthorityError(f"{path}: malformed EvaluateRequest: {exc}") from exc


def _load_checkpoint(path: Path) -> CheckpointFacts:
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise AuthorityError(f"{path}: checkpoint proxy must be a JSON object")
        return CheckpointFacts.model_validate_json(raw)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise AuthorityError(f"{path}: malformed native checkpoint facts: {exc}") from exc


def _validate_observations(path: Path) -> None:
    try:
        actual_schema = pl.read_parquet_schema(path)
    except (OSError, pl.exceptions.PolarsError) as exc:
        raise AuthorityError(f"{path}: unreadable observations parquet: {exc}") from exc
    if actual_schema != OBSERVATION_SCHEMA:
        raise AuthorityError(
            f"{path}: expected exact observations schema {OBSERVATION_SCHEMA}, got {actual_schema}"
        )
    try:
        facts = (
            pl.scan_parquet(path)
            .select(
                pl.len().alias("rows"),
                pl.any_horizontal(pl.all().is_null()).alias("has_null"),
                (~pl.col("classification_loss_contribution").is_finite())
                .any()
                .alias("bad_classification_loss"),
                (~pl.col("predicted_hindsight_minimum_base_fee_z").is_finite())
                .any()
                .alias("bad_prediction"),
                (pl.col("origin_block").diff().drop_nulls() <= 0).any().alias("bad_block_order"),
                (pl.col("origin_timestamp").diff().drop_nulls() <= 0)
                .any()
                .alias("bad_timestamp_order"),
                (pl.col("selected_action_k") < 0).any().alias("negative_selected_action"),
                (pl.col("earliest_hindsight_action_k") < 0)
                .any()
                .alias("negative_hindsight_action"),
                (pl.col("classification_loss_contribution") < 0)
                .any()
                .alias("negative_classification_loss"),
                (pl.col("selected_action_wait_seconds") < 0).any().alias("negative_wait"),
                (pl.col("full_horizon_elapsed_seconds") < 0).any().alias("negative_horizon"),
                (pl.col("immediate_k0_base_fee_per_gas") <= 0)
                .any()
                .alias("nonpositive_immediate_fee"),
                (pl.col("selected_target_base_fee_per_gas") <= 0)
                .any()
                .alias("nonpositive_selected_fee"),
                (pl.col("hindsight_minimum_base_fee_per_gas") <= 0)
                .any()
                .alias("nonpositive_hindsight_fee"),
                (
                    pl.col("hindsight_minimum_base_fee_per_gas")
                    > pl.col("selected_target_base_fee_per_gas")
                )
                .any()
                .alias("hindsight_exceeds_selected"),
                (
                    pl.col("hindsight_minimum_base_fee_per_gas")
                    > pl.col("immediate_k0_base_fee_per_gas")
                )
                .any()
                .alias("hindsight_exceeds_immediate"),
                ((pl.col("selected_action_k") == 0) & (pl.col("selected_action_wait_seconds") != 0))
                .any()
                .alias("k0_wait_nonzero"),
                (pl.col("selected_action_wait_seconds") > pl.col("full_horizon_elapsed_seconds"))
                .any()
                .alias("wait_exceeds_horizon"),
            )
            .collect()
            .row(0, named=True)
        )
    except pl.exceptions.PolarsError as exc:
        raise AuthorityError(f"{path}: failed structural validation: {exc}") from exc
    if facts["rows"] == 0:
        raise AuthorityError(f"{path}: observations must not be empty")
    failures = [name for name, failed in facts.items() if name != "rows" and failed]
    if failures:
        raise AuthorityError(f"{path}: invalid observation facts: {', '.join(failures)}")


def _validate_action_domain(path: Path, *, evaluation_id: UUID, action_width: int) -> None:
    invalid = (
        pl.scan_parquet(path)
        .select(
            (
                (pl.col("selected_action_k") >= action_width)
                | (pl.col("earliest_hindsight_action_k") >= action_width)
            )
            .any()
            .alias("invalid")
        )
        .collect()
        .item()
    )
    if invalid:
        raise AuthorityError(f"{evaluation_id}: action index lies outside checkpoint K")


def _sealed_rows(inputs: Sequence[LoadedInput]) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for evaluation_ordinal, item in enumerate(inputs):
        checkpoint = item.checkpoint
        if checkpoint is None:
            raise AssertionError("sealed reduction input must have checkpoint facts")
        observations = (
            pl.scan_parquet(item.observations_path)
            .select(SEALED_COLUMNS)
            .with_columns(
                pl.col("hindsight_minimum_base_fee_per_gas").log().alias("target_log_fee")
            )
            .with_columns(
                (
                    (pl.col("target_log_fee") - checkpoint.target_log_mean)
                    / checkpoint.target_log_std
                ).alias("target_z"),
                (
                    pl.col("predicted_hindsight_minimum_base_fee_z") * checkpoint.target_log_std
                    + checkpoint.target_log_mean
                ).alias("predicted_log_fee"),
                (
                    pl.col("immediate_k0_base_fee_per_gas")
                    - pl.col("selected_target_base_fee_per_gas")
                ).alias("savings"),
                (
                    pl.col("immediate_k0_base_fee_per_gas")
                    - pl.col("hindsight_minimum_base_fee_per_gas")
                ).alias("opportunity"),
                (
                    pl.col("selected_target_base_fee_per_gas")
                    - pl.col("hindsight_minimum_base_fee_per_gas")
                ).alias("regret"),
            )
            .with_columns(
                (pl.col("predicted_hindsight_minimum_base_fee_z") - pl.col("target_z")).alias(
                    "standardized_error"
                ),
                (pl.col("predicted_log_fee") - pl.col("target_log_fee")).alias("log_error"),
            )
            .collect()
        )
        aggregate = observations.select(
            pl.len().alias("eligible_origins"),
            pl.col("classification_loss_contribution").mean().alias("classification_loss"),
            (pl.col("selected_action_k") == pl.col("earliest_hindsight_action_k"))
            .mean()
            .alias("earliest_hindsight_label_accuracy"),
            pl.when(pl.col("standardized_error").abs() < 1)
            .then(0.5 * pl.col("standardized_error").pow(2))
            .otherwise(pl.col("standardized_error").abs() - 0.5)
            .mean()
            .alias("smooth_l1_loss"),
            pl.col("log_error").abs().mean().alias("natural_log_mae"),
            pl.col("log_error").pow(2).mean().alias("natural_log_mse"),
            (pl.col("savings").sum() / pl.col("immediate_k0_base_fee_per_gas").sum()).alias(
                "savings_ratio_vs_immediate_k0"
            ),
            (pl.col("opportunity").sum() / pl.col("immediate_k0_base_fee_per_gas").sum()).alias(
                "hindsight_opportunity_ratio_vs_immediate_k0"
            ),
            (pl.col("regret").sum() / pl.col("immediate_k0_base_fee_per_gas").sum()).alias(
                "hindsight_regret_ratio_vs_immediate_k0"
            ),
            pl.when(pl.col("opportunity").sum() > 0)
            .then(pl.col("savings").sum() / pl.col("opportunity").sum())
            .otherwise(None)
            .alias("signed_captured_hindsight_opportunity_ratio"),
            pl.col("selected_action_wait_seconds").mean().alias("mean_selected_wait_seconds"),
            pl.col("full_horizon_elapsed_seconds")
            .mean()
            .alias("mean_full_horizon_elapsed_seconds"),
        ).row(0, named=True)
        rows.append(
            {
                "evaluation_ordinal": evaluation_ordinal,
                "evaluation_id": str(item.request.evaluation_id),
                "artifact_id": str(item.request.artifact_id),
                **aggregate,
            }
        )
    return pl.DataFrame(rows)
