"""Inference helpers for trained temporal models."""

from __future__ import annotations

from typing import cast

import numpy as np
import torch
from numpy.typing import NDArray

from ..core.reporting import NullReporter, Reporter
from ..temporal.problem_store import CompiledProblemStore
from ._runtime import (
    build_model_loader,
    build_representation_runtime_context,
    resolve_device,
)
from .models import TemporalModel
from .problem_batches import TemporalProblemBatch

IntVector = NDArray[np.int64]


def predict_candidate_offsets(
    model: TemporalModel,
    *,
    model_id: str,
    store: CompiledProblemStore,
    sample_indices: IntVector,
    batch_size: int,
    device: str,
    reporter: Reporter | None = None,
) -> list[int]:
    reporter = reporter or NullReporter()
    if sample_indices.size == 0:
        raise ValueError("sample_indices must be non-empty")

    resolved_device = resolve_device(device)
    model.to(resolved_device)
    model.eval()
    runtime_context = build_representation_runtime_context(
        device=resolved_device,
        batch_size=batch_size,
    )
    loader = build_model_loader(
        store,
        sample_indices,
        model_id=model_id,
        runtime_context=runtime_context,
        seed=0,
    )
    task_id = reporter.start_task("predict candidates", total=len(loader), unit="batches")
    predictions = [0] * int(sample_indices.shape[0])
    with torch.no_grad():
        for batch in loader:
            batch = cast(TemporalProblemBatch, batch)
            sample_positions = batch.sample_positions.tolist()
            device_batch = batch.to_device(resolved_device)
            logits = model(**device_batch.model_kwargs()).logits
            targets = device_batch.objective_targets()
            logits = logits.masked_fill(
                ~targets.candidate_mask,
                torch.finfo(logits.dtype).min,
            )
            batch_predictions = logits.argmax(dim=-1).cpu().tolist()
            for sample_position, prediction in zip(
                sample_positions,
                batch_predictions,
                strict=True,
            ):
                predictions[int(sample_position)] = int(prediction)
            reporter.update_task(task_id, advance=1)
    reporter.finish_task(task_id)
    return predictions
