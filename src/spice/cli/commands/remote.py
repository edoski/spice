"""Hidden remote workflow execution."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Annotated, Literal

import typer
from pydantic import BaseModel, ConfigDict, Field

from ...config import BaselineSource, TrainRequest, WorkflowRequest
from ...corpus import load_corpus
from ...evaluation import EvaluationDeployment, evaluate
from ...modeling import FitDeployment, train
from ...temporal.history import prepare_fit_history

_PositiveInt = Annotated[int, Field(strict=True, gt=0)]
_NonNegativeInt = Annotated[int, Field(strict=True, ge=0)]


class _Record(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        revalidate_instances="always",
        strict=True,
    )


class _DeploymentProfile(_Record):
    evaluation_batch_size: _PositiveInt
    num_workers: _NonNegativeInt
    pin_memory: bool
    prefetch_factor: _PositiveInt | None
    persistent_workers: bool
    deterministic: bool | Literal["warn"]
    benchmark: bool
    float32_matmul_precision: Literal["highest", "high"]
    cuda_matmul_allow_tf32: bool
    cudnn_allow_tf32: bool


class _WorkflowEnvelope(_Record):
    request: WorkflowRequest
    deployment: _DeploymentProfile


app = typer.Typer(add_completion=False)


@app.command("workflow")
def workflow_command() -> None:
    envelope = _WorkflowEnvelope.model_validate_json(
        sys.stdin.buffer.read(),
        strict=True,
    )
    storage_root = Path(os.environ["STORAGE_ROOT"])
    request = envelope.request
    profile = envelope.deployment

    if isinstance(request, TrainRequest):
        source = request.source
        experiment = (
            source.training_definition.experiment
            if isinstance(source, BaselineSource)
            else source.experiment
        )
        corpus = load_corpus(storage_root, source.corpus_id)
        prepared = prepare_fit_history(corpus, experiment)
        train(request, prepared, storage_root, _fit_deployment(profile))
    else:
        evaluate(request, storage_root, _evaluation_deployment(profile))


def _fit_deployment(profile: _DeploymentProfile) -> FitDeployment:
    return FitDeployment(
        deterministic=profile.deterministic,
        benchmark=profile.benchmark,
        num_workers=profile.num_workers,
        pin_memory=profile.pin_memory,
        prefetch_factor=profile.prefetch_factor,
        persistent_workers=profile.persistent_workers,
        float32_matmul_precision=profile.float32_matmul_precision,
        cuda_matmul_allow_tf32=profile.cuda_matmul_allow_tf32,
        cudnn_allow_tf32=profile.cudnn_allow_tf32,
    )


def _evaluation_deployment(profile: _DeploymentProfile) -> EvaluationDeployment:
    return EvaluationDeployment(
        batch_size=profile.evaluation_batch_size,
        num_workers=profile.num_workers,
        pin_memory=profile.pin_memory,
        prefetch_factor=profile.prefetch_factor,
        persistent_workers=profile.persistent_workers,
        deterministic=profile.deterministic,
        benchmark=profile.benchmark,
        float32_matmul_precision=profile.float32_matmul_precision,
        cuda_matmul_allow_tf32=profile.cuda_matmul_allow_tf32,
        cudnn_allow_tf32=profile.cudnn_allow_tf32,
    )
