"""DISPOSABLE PROTOTYPE: direct HPO over retained successful runs.

Question: can generic selection accept any nonempty collection of retained successful
runs, with each run carrying its exact candidate and no failure/completeness state?

Synthetic values only. This is not production implementation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Candidate:
    name: str


@dataclass(frozen=True, slots=True)
class SuccessfulRun:
    candidate: Candidate
    total_loss: float
    best_epoch: int
    completed_epochs: int


def retain_success(
    retained: tuple[SuccessfulRun, ...],
    run: SuccessfulRun,
) -> tuple[SuccessfulRun, ...]:
    _validate_retained(retained)
    validate_success(run)
    return (*retained, run)


def validate_success(run: SuccessfulRun) -> None:
    if not run.candidate.name:
        raise ValueError("successful run must carry its exact candidate")
    if not run.total_loss < float("inf") or run.total_loss != run.total_loss:
        raise ValueError("successful run total_loss must be finite")
    if run.best_epoch < 1 or run.best_epoch > 36:
        raise ValueError("best_epoch must be within 1..36")
    if run.completed_epochs < run.best_epoch or run.completed_epochs > 36:
        raise ValueError("completed_epochs must be within best_epoch..36")


def selected_run(retained: tuple[SuccessfulRun, ...]) -> int:
    if not retained:
        raise ValueError("at least one retained successful run is required")
    _validate_retained(retained)
    return min(range(len(retained)), key=lambda index: (retained[index].total_loss, index))


def publish_study(retained: tuple[SuccessfulRun, ...]) -> tuple[SuccessfulRun, ...]:
    selected_run(retained)
    return retained


def _validate_retained(retained: tuple[SuccessfulRun, ...]) -> None:
    for run in retained:
        validate_success(run)
