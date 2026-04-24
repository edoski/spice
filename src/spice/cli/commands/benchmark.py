"""Benchmark command routing."""

from __future__ import annotations

from typing import Annotated

import typer

app = typer.Typer(
    help="Expand benchmark case batches.",
    no_args_is_help=True,
)


@app.command(
    "expand",
    short_help="Print expanded workflow commands.",
    help="Expand one benchmark YAML into validated concrete workflow commands.",
)
def benchmark_expand_command(
    name: Annotated[
        str,
        typer.Argument(metavar="NAME", help="Benchmark spec name."),
    ],
) -> None:
    from ...config.benchmarks import expand_benchmark_commands

    for command in expand_benchmark_commands(name):
        typer.echo(command)
