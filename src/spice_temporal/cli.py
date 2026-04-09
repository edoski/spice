"""Command-line interface for the SPICE temporal baseline project."""

from __future__ import annotations

from pathlib import Path

import typer

from spice_temporal.config import ExperimentConfig
from spice_temporal.cryo import build_pull_plan, rpc_env_is_set

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.command("show-config")
def show_config(config_path: Path) -> None:
    """Print a quick summary of the experiment configuration."""
    config = ExperimentConfig.from_yaml(config_path)
    typer.echo(f"Output root: {config.output_root}")
    typer.echo(f"Windows: {config.window_seconds}")
    typer.echo(f"Lookback: {config.lookback_seconds}s")
    typer.echo("Chains:")
    for chain in config.chains:
        typer.echo(
            f"  - {chain.name}: chain_id={chain.chain_id}, "
            f"nominal_block_time={chain.nominal_block_time_seconds}s, "
            f"rpc_env_var={chain.rpc_env_var}"
        )


@app.command("plan-pull")
def plan_pull(config_path: Path) -> None:
    """Render the cryo commands required for the baseline pull."""
    config = ExperimentConfig.from_yaml(config_path)
    for plan in build_pull_plan(config):
        typer.echo(f"[{plan.chain}]")
        typer.echo(f"history={plan.history_range.start}:{plan.history_range.end}")
        typer.echo(f"evaluation={plan.evaluation_range.start}:{plan.evaluation_range.end}")
        typer.echo(plan.command)
        typer.echo("")


@app.command("verify-env")
def verify_env(config_path: Path) -> None:
    """Check whether the expected RPC environment variables are configured."""
    config = ExperimentConfig.from_yaml(config_path)
    missing: list[str] = []
    for chain in config.chains:
        status = "set" if rpc_env_is_set(chain.rpc_env_var) else "missing"
        typer.echo(f"{chain.name}: {chain.rpc_env_var}={status}")
        if status == "missing":
            missing.append(chain.rpc_env_var)
    if missing:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
