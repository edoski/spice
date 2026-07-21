"""Direct evaluation of one native artifact over one historical window."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import numpy as np
import polars as pl
import torch
from pydantic import BaseModel, ConfigDict, Field
from torch import nn
from torch.utils.data import DataLoader

from ..addresses import evaluation_directory
from ..config import EvaluateRequest
from ..corpus import load_corpus
from ..min_block_fee import TargetState, decode_action
from ..modeling import load_artifact
from ..temporal.history import HistoricalDataset, prepare_historical_window
from .contract import OBSERVATION_SCHEMA

_PositiveInt = Annotated[int, Field(strict=True, gt=0)]
_NonNegativeInt = Annotated[int, Field(strict=True, ge=0)]
_DEVICE = torch.device("cuda:0")


class EvaluationDeployment(BaseModel):
    """Non-scientific execution facts for one evaluation invocation."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        revalidate_instances="always",
        strict=True,
    )

    batch_size: _PositiveInt
    num_workers: _NonNegativeInt
    pin_memory: bool
    prefetch_factor: _PositiveInt | None
    persistent_workers: bool
    deterministic: bool | Literal["warn"]
    benchmark: bool
    float32_matmul_precision: Literal["highest", "high"]
    cuda_matmul_allow_tf32: bool
    cudnn_allow_tf32: bool


def evaluate(
    request: EvaluateRequest,
    storage_root: Path,
    deployment: EvaluationDeployment,
) -> None:
    """Publish canonical observations for one exact artifact/window request."""

    scratch = storage_root / "evaluations" / f".{request.evaluation_id}"
    scratch.parent.mkdir(parents=True, exist_ok=True)
    scratch.mkdir()

    corpus = load_corpus(storage_root, request.corpus_id)
    association, model = load_artifact(storage_root, request.artifact_id)
    if association.request.artifact_id != request.artifact_id:
        raise ValueError("artifact request ID must match the evaluation artifact")
    if association.request.source.corpus_id != request.corpus_id:
        raise ValueError("artifact source Corpus must match the evaluation Corpus")
    experiment = association.training_definition.experiment
    testing_window = request.testing_window
    if testing_window.first_parent_block <= corpus.request.definition.first_block:
        raise ValueError("Corpus must include the previous closed parent")
    dataset = prepare_historical_window(
        corpus,
        experiment,
        testing_window,
        feature_state=association.feature_state,
        target_state=association.target_state,
    )

    _configure_execution(deployment)
    observations = _collect_observations(
        dataset,
        model,
        deployment,
        target_state=association.target_state,
    )
    (scratch / "evaluation.json").write_text(request.model_dump_json(), encoding="utf-8")
    observations.write_parquet(scratch / "observations.parquet")

    canonical = evaluation_directory(storage_root, request.evaluation_id)
    if canonical.exists():
        raise FileExistsError(canonical)
    scratch.rename(canonical)


def _configure_execution(deployment: EvaluationDeployment) -> None:
    torch.use_deterministic_algorithms(
        deployment.deterministic is not False,
        warn_only=deployment.deterministic == "warn",
    )
    torch.backends.cudnn.deterministic = deployment.deterministic is not False
    torch.backends.cudnn.benchmark = deployment.benchmark
    torch.set_float32_matmul_precision(deployment.float32_matmul_precision)
    torch.backends.cuda.matmul.allow_tf32 = deployment.cuda_matmul_allow_tf32
    torch.backends.cudnn.allow_tf32 = deployment.cudnn_allow_tf32


def _collect_observations(
    dataset: HistoricalDataset,
    model: nn.Module,
    deployment: EvaluationDeployment,
    *,
    target_state: TargetState,
) -> pl.DataFrame:
    count = len(dataset)
    columns = {
        "origin_block": np.empty(count, dtype=np.int64),
        "predicted_action_k": np.empty(count, dtype=np.int64),
        "predicted_minimum_log_base_fee": np.empty(count, dtype=np.float64),
        "minimum_action_k": np.empty(count, dtype=np.int64),
        "immediate_base_fee_per_gas": np.empty(count, dtype=np.int64),
        "selected_base_fee_per_gas": np.empty(count, dtype=np.int64),
        "minimum_base_fee_per_gas": np.empty(count, dtype=np.int64),
    }

    loader = DataLoader(
        dataset,
        batch_size=deployment.batch_size,
        shuffle=False,
        drop_last=False,
        num_workers=deployment.num_workers,
        pin_memory=deployment.pin_memory,
        prefetch_factor=deployment.prefetch_factor,
        persistent_workers=deployment.persistent_workers,
    )
    model.to(_DEVICE)
    cursor = 0
    with torch.inference_mode():
        for batch in loader:
            output = model(batch["inputs"].to(_DEVICE))
            actions = decode_action(output).to(device="cpu", dtype=torch.int64).numpy()
            minimum_actions_batch = batch["label"].to(dtype=torch.int64).numpy()
            base_fees = batch["base_fees"].to(dtype=torch.int64).numpy()
            minimum_fee_z = output.minimum_fee_z
            if minimum_fee_z.shape != actions.shape or not minimum_fee_z.is_floating_point():
                raise ValueError("evaluation batch outputs must have matching vector rows")
            if (
                np.any(actions < 0)
                or np.any(actions >= base_fees.shape[1])
                or np.any(minimum_actions_batch < 0)
                or np.any(minimum_actions_batch >= base_fees.shape[1])
            ):
                raise ValueError("evaluation actions must be within the batch horizon")

            rows = np.arange(actions.size, dtype=np.int64)
            immediate_batch = base_fees[:, 0]
            selected_batch = base_fees[rows, actions]
            minimum_batch = base_fees[rows, minimum_actions_batch]
            predicted_logs_batch = target_state.mean + target_state.standard_deviation * (
                minimum_fee_z.to(device="cpu", dtype=torch.float32).numpy().astype(np.float64)
            )
            if not np.isfinite(predicted_logs_batch).all():
                raise ValueError("predicted minimum-log fees must be finite")
            if np.any(np.column_stack((immediate_batch, selected_batch, minimum_batch)) <= 0):
                raise ValueError("evaluation fees must be positive")

            size = actions.size
            if cursor + size > count:
                raise ValueError("evaluation batches must exactly cover the testing window")
            destination = slice(cursor, cursor + size)
            columns["origin_block"][destination] = batch["origin_block"].numpy()
            columns["predicted_action_k"][destination] = actions
            columns["predicted_minimum_log_base_fee"][destination] = predicted_logs_batch
            columns["minimum_action_k"][destination] = minimum_actions_batch
            columns["immediate_base_fee_per_gas"][destination] = immediate_batch
            columns["selected_base_fee_per_gas"][destination] = selected_batch
            columns["minimum_base_fee_per_gas"][destination] = minimum_batch
            cursor += size

    if cursor != count:
        raise ValueError("evaluation batches must exactly cover the testing window")

    return pl.DataFrame(columns, schema=OBSERVATION_SCHEMA)


__all__ = ["EvaluationDeployment", "evaluate"]
