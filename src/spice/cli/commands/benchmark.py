"""Benchmark command routing."""

from __future__ import annotations

import json
from typing import Annotated

import typer

from ..options import DEFAULT_REMOTE_TARGET, RemoteTargetOption

app = typer.Typer(
    help="Plan and submit benchmark matrices.",
    no_args_is_help=True,
)


@app.command(
    "plan",
    short_help="Print resolved benchmark plan JSONL.",
    help="Expand one benchmark YAML into validated resolved workflow config JSONL.",
)
def benchmark_plan_command(
    name: Annotated[
        str,
        typer.Argument(metavar="NAME", help="Benchmark spec name."),
    ],
) -> None:
    from ...config.benchmarks import plan_benchmark

    for entry in plan_benchmark(name):
        typer.echo(json.dumps(entry.to_json_dict(), sort_keys=True))


@app.command(
    "submit",
    short_help="Submit a benchmark plan remotely.",
    help="Submit one benchmark YAML through the configured remote execution target.",
)
def benchmark_submit_command(
    name: Annotated[
        str,
        typer.Argument(metavar="NAME", help="Benchmark spec name."),
    ],
    target: RemoteTargetOption = DEFAULT_REMOTE_TARGET,
) -> None:
    from ...config.benchmarks import plan_benchmark
    from ...execution.slurm_ssh import submit_execution_workflow

    submitted: dict[str, str] = {}
    for entry in plan_benchmark(name):
        dependency = _compose_dependency(
            local_job_ids=[submitted[run_id] for run_id in entry.depends_on],
            external_dependencies=entry.external_dependencies,
        )
        submission = submit_execution_workflow(
            entry.workflow,
            config=entry.config,
            target_name=target,
            dependency=dependency,
        )
        submitted[entry.run_id] = submission.job_id
        typer.echo(
            json.dumps(
                {
                    "run_id": entry.run_id,
                    "workflow": entry.workflow.value,
                    "job_id": submission.job_id,
                    "dependency": dependency,
                    "log_path": str(submission.log_path),
                },
                sort_keys=True,
            )
        )


def _compose_dependency(
    *,
    local_job_ids: list[str],
    external_dependencies: tuple[str, ...],
) -> str | None:
    parts = list(external_dependencies)
    if local_job_ids:
        parts.append("afterok:" + ":".join(local_job_ids))
    if not parts:
        return None
    return ",".join(parts)
