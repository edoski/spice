"""Execution-owned workflow submit/follow lifecycle."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from ..config.resolved_workflows import ResolvedWorkflowConfig
from ..core.errors import SpiceOperatorError
from .provenance import ExecutionJobProvenance
from .session import ExecutionSession, open_execution_session

WorkflowSubmissionEventKind = Literal["submitted", "detached", "finished"]
WorkflowSubmissionEventFn = Callable[["WorkflowSubmissionEvent"], None]


@dataclass(frozen=True, slots=True)
class WorkflowSubmissionEvent:
    kind: WorkflowSubmissionEventKind
    provenance: ExecutionJobProvenance
    state: str | None = None


@dataclass(frozen=True, slots=True)
class WorkflowSubmissionResult:
    provenance: ExecutionJobProvenance
    state: str | None
    detached: bool


def submit_resolved_workflow(
    config: ResolvedWorkflowConfig,
    *,
    target: str,
    dependency: str | None = None,
    detach: bool = False,
    on_event: WorkflowSubmissionEventFn | None = None,
    session_factory: Callable[[str], ExecutionSession] | None = None,
) -> WorkflowSubmissionResult:
    if session_factory is None:
        session_factory = open_execution_session
    session = session_factory(target)
    provenance = session.submit_workflow(
        config.workflow,
        config=config,
        dependency=dependency,
    )
    _emit(on_event, WorkflowSubmissionEvent("submitted", provenance))
    if detach or not session.follow_by_default:
        return WorkflowSubmissionResult(provenance=provenance, state=None, detached=True)
    try:
        state = session.follow_job(provenance)
    except KeyboardInterrupt:
        _emit(on_event, WorkflowSubmissionEvent("detached", provenance, state="running"))
        return WorkflowSubmissionResult(provenance=provenance, state="running", detached=True)
    if state is None:
        return WorkflowSubmissionResult(provenance=provenance, state=None, detached=False)
    _emit(on_event, WorkflowSubmissionEvent("finished", provenance, state=state))
    if state != "COMPLETED":
        raise SpiceOperatorError(f"Job {provenance.job_id} ended with state {state}")
    return WorkflowSubmissionResult(provenance=provenance, state=state, detached=False)


def _emit(
    on_event: WorkflowSubmissionEventFn | None,
    event: WorkflowSubmissionEvent,
) -> None:
    if on_event is not None:
        on_event(event)
