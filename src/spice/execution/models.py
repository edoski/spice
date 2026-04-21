"""Execution target configuration models."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import Field, field_validator

from ..core.closed_dispatch import validate_path_segment
from ..modeling.families.base import ConfigModel


class ExecutionBackend(StrEnum):
    SLURM_OVER_SSH = "slurm_over_ssh"

class ExecutionSshSpec(ConfigModel):
    host: str
    user: str


class ExecutionPathsSpec(ConfigModel):
    repo_root: Path
    venv_root: Path
    storage_root: Path
    log_root: Path

    @property
    def venv_activate_path(self) -> Path:
        return self.venv_root / "bin" / "activate"

    @property
    def python_path(self) -> Path:
        return self.venv_root / "bin" / "python"

    @property
    def spice_path(self) -> Path:
        return self.venv_root / "bin" / "spice"


class ExecutionWorkflowSpec(ConfigModel):
    partition: str
    gpus: int = Field(gt=0)
    cpus_per_task: int = Field(gt=0)
    memory_gb: int = Field(gt=0)
    time_limit: str

    @field_validator("partition")
    @classmethod
    def validate_partition(cls, value: str) -> str:
        return validate_path_segment(value, label="execution.workflows.partition")


class ExecutionWorkflowSet(ConfigModel):
    train: ExecutionWorkflowSpec
    tune: ExecutionWorkflowSpec
    evaluate: ExecutionWorkflowSpec


class ExecutionSpec(ConfigModel):
    id: str
    backend: ExecutionBackend = ExecutionBackend.SLURM_OVER_SSH
    ssh: ExecutionSshSpec
    paths: ExecutionPathsSpec
    workflows: ExecutionWorkflowSet
    follow_by_default: bool = True

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return validate_path_segment(value, label="execution.id")
