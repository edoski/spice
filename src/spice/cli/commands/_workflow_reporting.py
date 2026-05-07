"""Workflow command reporting composition."""

from __future__ import annotations

from ...core.reporting import Reporter
from ...execution.submission import WorkflowSubmissionEvent


def report_workflow_submission_event(
    reporter: Reporter,
    event: WorkflowSubmissionEvent,
) -> None:
    provenance = event.submission.provenance
    if event.kind == "submitted":
        reporter.header(
            "submit",
            [
                ("workflow", provenance.task.value),
                ("job_id", provenance.job_id),
                ("log", provenance.log_path),
            ],
        )
        return
    if event.kind == "detached":
        reporter.header(
            "submit detached",
            [
                ("job_id", provenance.job_id),
                ("state", event.state or "running"),
            ],
        )
        return
    if event.state is None:
        return
    reporter.header(
        "submit finished",
        [
            ("job_id", provenance.job_id),
            ("state", event.state),
        ],
    )
