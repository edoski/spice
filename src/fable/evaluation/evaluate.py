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
from ..min_block_fee import decode_action
from ..modeling import load_artifact
from ..temporal.history import HistoricalDataset, prepare_historical_window
from .contract import OBSERVATION_SCHEMA, validate_request_artifact

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
    validate_request_artifact(request, association)
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
    )
    (scratch / "evaluation.json").write_text(
        request.model_dump_json(),
        encoding="utf-8",
    )
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
) -> pl.DataFrame:
    count = len(dataset)
    origin_blocks = np.empty(count, dtype=np.int64)
    predicted_actions = np.empty(count, dtype=np.int64)
    predicted_z = np.empty(count, dtype=np.float32)

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
            inputs = batch["inputs"].to(_DEVICE)
            output = model(inputs)
            actions = decode_action(output).to(device="cpu", dtype=torch.int64)
            minimum_fee_z = output.minimum_fee_z
            if (
                minimum_fee_z.ndim != 1
                or minimum_fee_z.shape[0] != actions.shape[0]
                or not minimum_fee_z.is_floating_point()
                or not torch.isfinite(minimum_fee_z).all()
            ):
                raise ValueError("minimum_fee_z must be a finite floating vector matching actions")
            minimum_fee_z = minimum_fee_z.to(device="cpu", dtype=torch.float32)

            size = actions.shape[0]
            destination = slice(cursor, cursor + size)
            origin_blocks[destination] = batch["origin_block"].numpy()
            predicted_actions[destination] = actions.numpy()
            predicted_z[destination] = minimum_fee_z.numpy()
            cursor += size

    return pl.DataFrame(
        {
            "origin_block": origin_blocks,
            "predicted_action_k": predicted_actions,
            "predicted_minimum_log_base_fee_z": predicted_z,
        },
        schema=OBSERVATION_SCHEMA,
    )


__all__ = ["EvaluationDeployment", "evaluate"]
