"""Adaptive RPC scheduling controller."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from ...config.models import AcquisitionConfig
from .types import AcquisitionRuntimeSnapshot

TRANSIENT_FAILURE_WINDOW = 32
TRANSIENT_FAILURE_WINDOW_THRESHOLD = 3
TRANSIENT_FAILURE_STREAK_THRESHOLD = 2
SUCCESS_STREAK_FOR_RECOVERY = 64


@dataclass(slots=True)
class RpcController:
    configured_batch_size: int
    min_batch_size: int
    concurrency_rungs: tuple[int, ...]
    configured_concurrency: int
    current_batch_size: int = field(init=False)
    _configured_concurrency_index: int = field(init=False, repr=False)
    _current_concurrency_index: int = field(init=False, repr=False)
    _success_streak: int = field(default=0, init=False, repr=False)
    _transient_streak: int = field(default=0, init=False, repr=False)
    _recent_transient_attempts: deque[int] = field(init=False, repr=False)
    oversize_error_count: int = 0
    transient_error_count: int = 0
    oversize_backoffs: int = 0
    transient_backoffs: int = 0
    concurrency_recoveries: int = 0

    def __post_init__(self) -> None:
        if self.min_batch_size > self.configured_batch_size:
            raise ValueError("acquisition.rpc.min_batch_size must be <= batch_size")
        if not self.concurrency_rungs:
            raise ValueError("acquisition.rpc.concurrency_rungs must not be empty")
        if tuple(sorted(self.concurrency_rungs)) != self.concurrency_rungs:
            raise ValueError("acquisition.rpc.concurrency_rungs must be sorted ascending")
        if len(set(self.concurrency_rungs)) != len(self.concurrency_rungs):
            raise ValueError("acquisition.rpc.concurrency_rungs must not contain duplicates")
        if self.configured_concurrency not in self.concurrency_rungs:
            raise ValueError("acquisition.rpc.concurrency must be present in concurrency_rungs")

        self.current_batch_size = self.configured_batch_size
        self._configured_concurrency_index = self.concurrency_rungs.index(
            self.configured_concurrency
        )
        self._current_concurrency_index = self._configured_concurrency_index
        self._recent_transient_attempts = deque(maxlen=TRANSIENT_FAILURE_WINDOW)

    @classmethod
    def from_config(cls, config: AcquisitionConfig) -> RpcController:
        return cls(
            configured_batch_size=config.rpc.batch_size,
            min_batch_size=config.rpc.min_batch_size,
            concurrency_rungs=tuple(config.rpc.concurrency_rungs),
            configured_concurrency=config.rpc.concurrency,
        )

    @property
    def current_concurrency(self) -> int:
        return self.concurrency_rungs[self._current_concurrency_index]

    def record_success(self) -> int | None:
        self._success_streak += 1
        self._transient_streak = 0
        self._recent_transient_attempts.append(0)
        if (
            self._success_streak < SUCCESS_STREAK_FOR_RECOVERY
            or self._current_concurrency_index >= self._configured_concurrency_index
        ):
            return None

        self._current_concurrency_index += 1
        self._success_streak = 0
        self._recent_transient_attempts.clear()
        self.concurrency_recoveries += 1
        return self.current_concurrency

    def record_oversize_failure(self) -> int | None:
        self.oversize_error_count += 1
        self._success_streak = 0
        self._transient_streak = 0

        next_batch_size = max(self.min_batch_size, self.current_batch_size // 2)
        if next_batch_size >= self.current_batch_size:
            return None

        self.current_batch_size = next_batch_size
        self.oversize_backoffs += 1
        return self.current_batch_size

    def record_transient_failure(self) -> int | None:
        self.transient_error_count += 1
        self._success_streak = 0
        self._transient_streak += 1
        self._recent_transient_attempts.append(1)
        if self._current_concurrency_index == 0:
            return None

        if (
            self._transient_streak < TRANSIENT_FAILURE_STREAK_THRESHOLD
            and sum(self._recent_transient_attempts) < TRANSIENT_FAILURE_WINDOW_THRESHOLD
        ):
            return None

        self._current_concurrency_index -= 1
        self._transient_streak = 0
        self._recent_transient_attempts.clear()
        self.transient_backoffs += 1
        return self.current_concurrency

    def snapshot(self) -> AcquisitionRuntimeSnapshot:
        return AcquisitionRuntimeSnapshot(
            configured_batch_size=self.configured_batch_size,
            final_batch_size=self.current_batch_size,
            min_batch_size=self.min_batch_size,
            configured_concurrency=self.configured_concurrency,
            final_concurrency=self.current_concurrency,
            concurrency_rungs=self.concurrency_rungs,
            oversize_error_count=self.oversize_error_count,
            transient_error_count=self.transient_error_count,
            oversize_backoffs=self.oversize_backoffs,
            transient_backoffs=self.transient_backoffs,
            concurrency_recoveries=self.concurrency_recoveries,
        )
