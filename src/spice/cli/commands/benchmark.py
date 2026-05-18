"""Benchmark command routing."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer

from ..errors import OperatorTyper
from ..options import (
    DEFAULT_BENCHMARK_INDEX_PATH,
    DEFAULT_BENCHMARK_RUNS_ROOT,
    DEFAULT_REMOTE_TARGET,
    RemoteTargetOption,
)
from ..output import echo_json

app = OperatorTyper(help="Plan, submit, collect, and export benchmark runs.", no_args_is_help=True)
index_app = OperatorTyper(
    help="Maintain and inspect the benchmark result index.",
    no_args_is_help=True,
)
app.add_typer(index_app, name="index")

@app.command("plan", short_help="Create a durable benchmark run plan.")
def benchmark_plan_command(
    name: Annotated[str, typer.Argument(metavar="NAME", help="Benchmark spec name.")],
    target: RemoteTargetOption = DEFAULT_REMOTE_TARGET,
    runs_root: Annotated[
        Path,
        typer.Option("--runs-root", help="Benchmark run root directory."),
    ] = DEFAULT_BENCHMARK_RUNS_ROOT,
) -> None:
    from ...benchmarks.submission import materialize_benchmark_plan_run

    planned = materialize_benchmark_plan_run(name, target=target, runs_root=runs_root)
    echo_json({"run_dir": str(planned.run_dir), "entries": planned.entry_count})


@app.command("submit", short_help="Submit an existing benchmark run plan remotely.")
def benchmark_submit_command(
    run_dir: Annotated[
        Path,
        typer.Argument(exists=True, file_okay=False, dir_okay=True, readable=True),
    ],
) -> None:
    from ...benchmarks.submission import submit_benchmark_run

    for submitted in submit_benchmark_run(run_dir):
        echo_json({"run_dir": str(submitted.run_dir), **submitted.record.model_dump(mode="json")})


@app.command("collect", short_help="Collect a completed benchmark run.")
def benchmark_collect_command(
    run_dir: Annotated[
        Path,
        typer.Argument(exists=True, file_okay=False, dir_okay=True, readable=True),
    ],
) -> None:
    from ...benchmarks.collection import collect_benchmark_run

    snapshot = collect_benchmark_run(run_dir)
    echo_json(
        {
            "run_dir": str(run_dir),
            "records": len(snapshot.records),
            "collection": "complete",
        }
    )


@app.command("show", short_help="Show benchmark run state.")
def benchmark_show_command(
    run_dir: Annotated[
        Path,
        typer.Argument(exists=True, file_okay=False, dir_okay=True, readable=True),
    ],
) -> None:
    from ...benchmarks.runs import load_benchmark_run

    run = load_benchmark_run(run_dir)
    evaluate_count = sum(1 for entry in run.plan if entry.workflow.value == "evaluate")
    echo_json(
        {
            "run_dir": str(run.run_dir),
            "benchmark": run.metadata.benchmark,
            "target": run.metadata.target,
            "entries": len(run.plan),
            "evaluate_entries": evaluate_count,
            "submissions": len(run.submissions),
            "collection": run.has_collection,
        }
    )


@index_app.command("rebuild", short_help="Rebuild results.sqlite from benchmark run dirs.")
def benchmark_index_rebuild_command(
    runs_root: Annotated[
        Path,
        typer.Option("--runs-root", help="Benchmark run root directory."),
    ] = DEFAULT_BENCHMARK_RUNS_ROOT,
    index_path: Annotated[
        Path,
        typer.Option("--index", help="Benchmark result index path."),
    ] = DEFAULT_BENCHMARK_INDEX_PATH,
) -> None:
    from ...benchmarks.result_index import rebuild_benchmark_result_index

    echo_json(rebuild_benchmark_result_index(runs_root=runs_root, index_path=index_path))


@index_app.command("show", short_help="Show benchmark result index counts.")
def benchmark_index_show_command(
    index_path: Annotated[
        Path,
        typer.Option("--index", help="Benchmark result index path."),
    ] = DEFAULT_BENCHMARK_INDEX_PATH,
) -> None:
    from ...benchmarks.result_index import benchmark_result_index_counts

    echo_json(benchmark_result_index_counts(index_path=index_path))


@index_app.command("list", short_help="List indexed benchmark results.")
def benchmark_index_list_command(
    benchmark: Annotated[str | None, typer.Option("--benchmark")] = None,
    chain: Annotated[str | None, typer.Option("--chain")] = None,
    model: Annotated[str | None, typer.Option("--model")] = None,
    evaluator: Annotated[str | None, typer.Option("--evaluator")] = None,
    limit: Annotated[int | None, typer.Option("--limit")] = None,
    index_path: Annotated[
        Path,
        typer.Option("--index", help="Benchmark result index path."),
    ] = DEFAULT_BENCHMARK_INDEX_PATH,
) -> None:
    from ...benchmarks.result_index import list_benchmark_results

    for row in list_benchmark_results(
        index_path=index_path,
        benchmark=benchmark,
        chain=chain,
        model=model,
        evaluator=evaluator,
        limit=limit,
    ):
        echo_json(asdict(row))


@index_app.command("export", short_help="Export indexed benchmark results to CSV.")
def benchmark_index_export_command(
    output: Annotated[
        Path,
        typer.Option("--output", help="Named CSV output path."),
    ],
    benchmark: Annotated[str | None, typer.Option("--benchmark")] = None,
    chain: Annotated[str | None, typer.Option("--chain")] = None,
    model: Annotated[str | None, typer.Option("--model")] = None,
    evaluator: Annotated[str | None, typer.Option("--evaluator")] = None,
    index_path: Annotated[
        Path,
        typer.Option("--index", help="Benchmark result index path."),
    ] = DEFAULT_BENCHMARK_INDEX_PATH,
) -> None:
    from ...benchmarks.result_index import export_benchmark_results_csv

    rows = export_benchmark_results_csv(
        output_path=output,
        index_path=index_path,
        benchmark=benchmark,
        chain=chain,
        model=model,
        evaluator=evaluator,
    )
    echo_json({"output": str(output), "rows": len(rows)})
