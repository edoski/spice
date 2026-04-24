from __future__ import annotations

import numpy as np
import pytest
import torch

from spice.modeling.batch_sources import (
    _build_batch_source,
    _resolve_host_loader_worker_settings,
)
from spice.modeling.representations import RepresentationRuntimeContext


def test_host_loader_worker_override_rejects_invalid_values(monkeypatch) -> None:
    monkeypatch.setenv("SPICE_DATALOADER_WORKERS", "-1")

    with pytest.raises(ValueError, match="must be non-negative"):
        _resolve_host_loader_worker_settings()


def test_device_resident_oom_falls_back_to_host_loader(monkeypatch) -> None:
    class _Prepared:
        sample_count = 4
        batch_signatures = np.array([1, 1, 1, 1], dtype=np.int64)
        estimated_storage_bytes = 1024

        def build_batch(self, sample_positions: torch.Tensor) -> torch.Tensor:
            return sample_positions

        def to_device_storage(self, device: torch.device):
            raise torch.cuda.OutOfMemoryError("oom")

    empty_cache_calls: list[bool] = []
    monkeypatch.setattr(torch.cuda, "empty_cache", lambda: empty_cache_calls.append(True))

    source = _build_batch_source(
        _Prepared(),
        required_bytes=1024,
        runtime_context=RepresentationRuntimeContext(
            batch_size=2,
            available_host_memory_bytes=1024,
            available_device_memory_bytes=2048,
        ),
        resolved_device=torch.device("cuda"),
        seed=2026,
        shuffle=False,
    )

    assert torch.equal(next(iter(source)), torch.tensor([0, 1], dtype=torch.int64))
    assert empty_cache_calls == [True]
