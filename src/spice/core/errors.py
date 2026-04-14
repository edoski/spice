"""Operator-facing SPICE error types for CLI and automated workflow entrypoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

import click

if TYPE_CHECKING:
    from ..storage.catalog import CatalogArtifactRecord, CatalogStudyRecord

T = TypeVar("T")


class SpiceOperatorError(click.ClickException):
    """Base error for operator-facing failures that should render without a traceback."""


class ConfigResolutionError(SpiceOperatorError):
    """Raised when selectors or config payloads cannot resolve into a runnable request."""


class MissingStateError(SpiceOperatorError):
    """Raised when a requested stored state root or required state row is missing."""


class StateLayoutError(SpiceOperatorError):
    """Raised when an on-disk state database does not match the current schema."""


class StateConflictError(SpiceOperatorError):
    """Raised when an existing state root conflicts with the requested operation."""


class SelectorResolutionError(SpiceOperatorError, Generic[T]):
    """Raised when selector-driven lookup yields zero or multiple matches."""

    def __init__(self, *, kind: str, records: list[T]) -> None:
        self.kind = kind
        self.records = tuple(records)
        message = f"Expected exactly one {kind} match" if records else f"No {kind} matches found"
        super().__init__(message)


class DeleteBlockedError(SpiceOperatorError):
    """Raised when delete would orphan dependent state without explicit cascade."""

    def __init__(
        self,
        *,
        message: str,
        artifact_records: list[CatalogArtifactRecord] | None = None,
        study_records: list[CatalogStudyRecord] | None = None,
    ) -> None:
        self.artifact_records = tuple(artifact_records or ())
        self.study_records = tuple(study_records or ())
        super().__init__(message)
