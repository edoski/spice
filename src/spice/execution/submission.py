"""Submit one typed workflow through SSH and Slurm."""

from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path
from typing import Annotated

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from ..config import WORKFLOW_REQUEST_ADAPTER, WorkflowRequest

_NonEmptyString = Annotated[str, Field(strict=True, min_length=1)]
_PositiveInt = Annotated[int, Field(strict=True, gt=0)]
_JOB_ID_PATTERN = re.compile(r"([0-9]+)(?:;[^;\r\n]+)?\n?")


class _Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")


class _Resources(_Record):
    partition: _NonEmptyString
    cpus_per_task: _PositiveInt
    memory_gb: _PositiveInt
    time_limit: _NonEmptyString


class _Remote(_Record):
    ssh: _NonEmptyString
    executable: _NonEmptyString
    storage_root: _NonEmptyString
    log_root: _NonEmptyString
    train: _Resources
    tune: _Resources
    evaluate: _Resources

    @field_validator("executable", "storage_root", "log_root")
    @classmethod
    def validate_absolute_path(cls, value: str, info: ValidationInfo) -> str:
        if not Path(value).is_absolute():
            raise ValueError(f"{info.field_name} must be an absolute path")
        return value


def submit(request: WorkflowRequest) -> int:
    """Submit one Train or Evaluate request and return its positive Slurm ID."""

    request_json = WORKFLOW_REQUEST_ADAPTER.dump_json(request).decode()
    remote = _Remote.model_validate(yaml.safe_load(Path("REMOTE.yaml").read_bytes()))
    resources = remote.train if request.workflow == "train" else remote.evaluate
    script = _render_script(remote, resources, request_json)
    result = subprocess.run(
        [
            "ssh",
            "-T",
            "-o",
            "BatchMode=yes",
            remote.ssh,
            "sbatch",
            "--parsable",
        ],
        input=script,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    )
    return _parse_job_id(result.stdout)


def _render_script(remote: _Remote, resources: _Resources, request_json: str) -> str:
    return "\n".join(
        (
            "#!/bin/bash",
            f"#SBATCH --partition={resources.partition}",
            "#SBATCH --nodes=1",
            "#SBATCH --ntasks=1",
            "#SBATCH --gres=gpu:1",
            f"#SBATCH --cpus-per-task={resources.cpus_per_task}",
            f"#SBATCH --mem={resources.memory_gb}G",
            f"#SBATCH --time={resources.time_limit}",
            f"#SBATCH --output={remote.log_root}/%j.out",
            f"export STORAGE_ROOT={shlex.quote(remote.storage_root)}",
            f"exec {shlex.quote(remote.executable)} remote workflow <<'SPICE_REQUEST'",
            request_json,
            "SPICE_REQUEST",
            "",
        )
    )


def _parse_job_id(output: str) -> int:
    match = _JOB_ID_PATTERN.fullmatch(output)
    if match is None or (job_id := int(match.group(1))) <= 0:
        raise ValueError(f"invalid sbatch --parsable output: {output!r}")
    return job_id
