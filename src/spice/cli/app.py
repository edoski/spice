"""Top-level SPICE CLI application."""

from __future__ import annotations

import typer

from .commands.config import app as config_app
from .commands.storage import delete_app, show_app
from .commands.workflows import (
    acquire_command,
    simulate_command,
    train_command,
    tune_command,
)

app = typer.Typer(
    name="spice",
    help="SPICE workflow CLI.",
    epilog="Example:\n  spice acquire --preset icdcs_2026",
    no_args_is_help=True,
    add_completion=True,
)
app.add_typer(config_app, name="config")
app.add_typer(show_app, name="show")
app.add_typer(delete_app, name="delete")

app.command(
    "acquire",
    short_help="Acquire canonical datasets.",
    help="Acquire canonical history and evaluation block datasets.",
    epilog=(
        "Example:\n"
        "  spice acquire --preset icdcs_2026 --chain avalanche --provider publicnode"
    ),
)(acquire_command)
app.command(
    "train",
    short_help="Train a model artifact.",
    help="Train one artifact from a materialized history corpus.",
)(train_command)
app.command(
    "tune",
    short_help="Tune a model artifact.",
    help="Tune one artifact with Optuna.",
)(tune_command)
app.command(
    "simulate",
    short_help="Simulate a model artifact.",
    help="Simulate one trained artifact on evaluation data.",
)(simulate_command)


def main(argv: list[str] | None = None) -> None:
    del argv
    app()
