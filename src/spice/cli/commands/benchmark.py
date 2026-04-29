"""Benchmark command routing."""

from __future__ import annotations

import json
from pathlib import Path
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
    help="Expand one benchmark spec into validated resolved workflow config JSONL.",
)
def benchmark_plan_command(
    name: Annotated[
        str,
        typer.Argument(metavar="NAME", help="Benchmark spec name."),
    ],
) -> None:
    from ...benchmarks import plan_benchmark

    for entry in plan_benchmark(name):
        typer.echo(json.dumps(entry.to_json_dict(), sort_keys=True))


@app.command(
    "submit",
    short_help="Submit a benchmark plan remotely.",
    help="Submit one benchmark spec through the configured remote execution target.",
)
def benchmark_submit_command(
    name: Annotated[
        str,
        typer.Argument(metavar="NAME", help="Benchmark spec name."),
    ],
    target: RemoteTargetOption = DEFAULT_REMOTE_TARGET,
) -> None:
    from ...benchmarks.submission import submit_benchmark_run

    for submitted in submit_benchmark_run(name, target=target):
        typer.echo(
            json.dumps(
                {
                    **submitted.record.model_dump(mode="json"),
                    "run_dir": str(submitted.run_dir),
                },
                sort_keys=True,
            )
        )


@app.command(
    "collect",
    short_help="Collect completed benchmark evaluations into the ledger.",
    help="Pull remote benchmark artifacts for a submitted run and optionally append ledger rows.",
)
def benchmark_collect_command(
    name: Annotated[
        str,
        typer.Argument(metavar="NAME", help="Benchmark spec name."),
    ],
    target: RemoteTargetOption = DEFAULT_REMOTE_TARGET,
    run_dir: Annotated[
        Path | None,
        typer.Option(
            "--run-dir",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Specific benchmark run directory. Defaults to latest run for NAME.",
        ),
    ] = None,
    ledger: Annotated[
        Path,
        typer.Option(
            "--ledger",
            help="Benchmark result ledger path.",
        ),
    ] = Path("benchmarks") / "results.csv",
    write: Annotated[
        bool,
        typer.Option(
            "--write",
            help="Append complete, non-duplicate evaluation rows to the ledger.",
        ),
    ] = False,
) -> None:
    from ...benchmarks.collection import collect_benchmark_run
    from ...benchmarks.runs import latest_benchmark_run_dir

    resolved_run_dir = run_dir or latest_benchmark_run_dir(name)
    records = collect_benchmark_run(
        run_dir=resolved_run_dir,
        target_name=target,
        ledger_path=ledger,
        write=write,
    )
    for record in records:
        typer.echo(json.dumps(record.model_dump(mode="json"), sort_keys=True))
