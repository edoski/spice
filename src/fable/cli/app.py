"""FABLE command-line application."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer

from ..config import WORKFLOW_REQUEST_ADAPTER, WorkflowRequest
from ..environment import resolve_storage_root
from ..evaluation import compare_rolling
from ..execution import submit as submit_workflow
from .commands.remote import app as remote_app
from .commands.study import app as study_app

app = typer.Typer(add_completion=False)
app.add_typer(remote_app, name="remote", hidden=True)
app.add_typer(study_app, name="study")


@app.command("submit")
def submit_command(
    request_paths: Annotated[
        list[Path],
        typer.Argument(metavar="REQUEST.json"),
    ],
) -> None:
    requests: list[WorkflowRequest] = [
        WORKFLOW_REQUEST_ADAPTER.validate_json(path.read_bytes()) for path in request_paths
    ]
    for request in requests:
        typer.echo(submit_workflow(request))


@app.command("rolling")
def rolling_command(
    roster_path: Annotated[Path, typer.Argument(metavar="ROLLING.json")],
) -> None:
    payload = json.loads(roster_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("ROLLING.json must contain one object of named cells")
    try:
        roster = {
            cell: {int(horizon): UUID(evaluation_id) for horizon, evaluation_id in ids.items()}
            for cell, ids in payload.items()
        }
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError("ROLLING.json must map cells and horizons to Evaluation UUIDs") from error

    typer.echo(compare_rolling(resolve_storage_root(), roster).write_csv(), nl=False)


def main() -> None:
    app()
