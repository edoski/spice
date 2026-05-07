"""Execution job identity and environment provenance."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ..config.models import WorkflowTask

EXECUTION_TARGET_ENV = "SPICE_EXECUTION_TARGET"
WORKFLOW_TASK_ENV = "SPICE_WORKFLOW_TASK"
EXECUTION_JOB_ID_ENV = "SPICE_EXECUTION_JOB_ID"
EXECUTION_REF_ENV = "SPICE_EXECUTION_REF"
EXECUTION_LOG_PATH_ENV = "SPICE_EXECUTION_LOG_PATH"

_EXECUTION_ENV_KEYS = frozenset(
    {
        EXECUTION_TARGET_ENV,
        WORKFLOW_TASK_ENV,
        EXECUTION_JOB_ID_ENV,
        EXECUTION_REF_ENV,
        EXECUTION_LOG_PATH_ENV,
    }
)


@dataclass(frozen=True, slots=True)
class ExecutionJobProvenance:
    task: WorkflowTask
    target: str
    job_id: str
    execution_ref: str
    log_path: Path

    @classmethod
    def slurm(
        cls,
        *,
        task: WorkflowTask,
        target: str,
        job_id: str,
        log_path: Path,
    ) -> ExecutionJobProvenance:
        return cls(
            task=task,
            target=target,
            job_id=job_id,
            execution_ref=f"slurm:{job_id}",
            log_path=log_path,
        )


def current_execution_job_provenance(
    environ: Mapping[str, str] | None = None,
) -> ExecutionJobProvenance | None:
    env = os.environ if environ is None else environ
    present = {key for key in _EXECUTION_ENV_KEYS if env.get(key)}
    if not present:
        return None
    missing = _EXECUTION_ENV_KEYS - present
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise RuntimeError(f"Incomplete execution provenance environment: {missing_text}")
    return ExecutionJobProvenance(
        task=WorkflowTask(env[WORKFLOW_TASK_ENV]),
        target=env[EXECUTION_TARGET_ENV],
        job_id=env[EXECUTION_JOB_ID_ENV],
        execution_ref=env[EXECUTION_REF_ENV],
        log_path=Path(env[EXECUTION_LOG_PATH_ENV]),
    )
