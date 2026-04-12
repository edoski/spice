"""Thin Typer CLI that forwards Hydra overrides to workflow entrypoints."""

from __future__ import annotations

from collections.abc import Callable

import typer

from .core.config import ExperimentConfig, WorkflowTask, load_hydra_config
from .workflows import acquire, simulate, train, tune

CONTEXT_SETTINGS = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
}

app = typer.Typer(
    name="spice",
    help="SPICE workflow CLI.",
    no_args_is_help=True,
    add_completion=True,
)


def _dispatch(
    task: WorkflowTask,
    run_workflow: Callable[[ExperimentConfig], None],
    args: list[str],
) -> None:
    run_workflow(load_hydra_config(task, overrides=args))


@app.command("acquire", context_settings=CONTEXT_SETTINGS)
def acquire_command(ctx: typer.Context) -> None:
    """Acquire canonical history and evaluation block datasets."""

    _dispatch(WorkflowTask.ACQUIRE, acquire.run, list(ctx.args))


@app.command("train", context_settings=CONTEXT_SETTINGS)
def train_command(ctx: typer.Context) -> None:
    """Train a model artifact."""

    _dispatch(WorkflowTask.TRAIN, train.run, list(ctx.args))


@app.command("tune", context_settings=CONTEXT_SETTINGS)
def tune_command(ctx: typer.Context) -> None:
    """Tune model hyperparameters."""

    _dispatch(WorkflowTask.TUNE, tune.run, list(ctx.args))


@app.command("simulate", context_settings=CONTEXT_SETTINGS)
def simulate_command(ctx: typer.Context) -> None:
    """Run evaluation-day simulation from a trained artifact."""

    _dispatch(WorkflowTask.SIMULATE, simulate.run, list(ctx.args))


def main(argv: list[str] | None = None) -> None:
    app(prog_name="spice", args=argv)
