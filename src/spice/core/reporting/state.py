"""Reporting state dataclasses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class _TaskBinding:
    stage_key: str
    task_name: str
    done_status: str


@dataclass(slots=True)
class _StageState:
    key: str
    label: str
    status: str = "pending"
    total: int | None = None
    unit: str | None = None
    completed: int = 0
    detail: str | None = None
    started_at: float | None = None
    finished_at: float | None = None
    last_progress_at: float | None = None
    last_progress_completed: int = 0
    smoothed_rate: float | None = None
    last_emitted_status: str | None = None
    last_emitted_detail: str | None = None
    last_emitted_completed: int | None = None
    last_emitted_bucket: int | None = None


@dataclass(frozen=True, slots=True)
class _StageLayout:
    stage_width: int
    status_width: int
    progress_bar_width: int
    show_rate: bool
    show_eta: bool
    show_detail: bool
    metric_columns: tuple[str, ...] = ()

    @property
    def progress_width(self) -> int:
        return self.progress_bar_width + 5
