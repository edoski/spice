"""Explicit Typer CLI over the split config system."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from .config import (
    load_acquire_config,
    load_simulate_config,
    load_train_config,
    load_tune_config,
)
from .workflows import acquire, simulate, train, tune

app = typer.Typer(
    name="spice",
    help="SPICE workflow CLI.",
    no_args_is_help=True,
    add_completion=True,
)

@app.command("acquire")
def acquire_command(
    preset: Annotated[str | None, typer.Option("--preset")] = None,
    config: Annotated[Path | None, typer.Option("--config")] = None,
    dataset: Annotated[str | None, typer.Option("--dataset")] = None,
    chain: Annotated[str | None, typer.Option("--chain")] = None,
    provider: Annotated[str | None, typer.Option("--provider")] = None,
    acquisition_profile: Annotated[str | None, typer.Option("--acquisition")] = None,
    storage_root: Annotated[Path | None, typer.Option("--storage-root")] = None,
    dry_run: Annotated[bool | None, typer.Option("--dry-run/--no-dry-run")] = None,
) -> None:
    """Acquire canonical history and evaluation block datasets."""
    acquire.run(
        load_acquire_config(
            preset=preset,
            config_path=config,
            dataset=dataset,
            chain=chain,
            provider=provider,
            acquisition=acquisition_profile,
            storage_root=storage_root,
            dry_run=dry_run,
        )
    )


@app.command("train")
def train_command(
    preset: Annotated[str | None, typer.Option("--preset")] = None,
    config: Annotated[Path | None, typer.Option("--config")] = None,
    dataset: Annotated[str | None, typer.Option("--dataset")] = None,
    chain: Annotated[str | None, typer.Option("--chain")] = None,
    model: Annotated[str | None, typer.Option("--model")] = None,
    feature_set: Annotated[str | None, typer.Option("--feature-set")] = None,
    training_profile: Annotated[str | None, typer.Option("--training")] = None,
    split: Annotated[str | None, typer.Option("--split")] = None,
    storage_root: Annotated[Path | None, typer.Option("--storage-root")] = None,
    variant: Annotated[str | None, typer.Option("--variant")] = None,
    study: Annotated[str | None, typer.Option("--study")] = None,
) -> None:
    """Train a model artifact."""
    train.run(
        load_train_config(
            preset=preset,
            config_path=config,
            dataset=dataset,
            chain=chain,
            model=model,
            feature_set=feature_set,
            training=training_profile,
            split=split,
            storage_root=storage_root,
            variant=variant,
            study=study,
        )
    )


@app.command("tune")
def tune_command(
    preset: Annotated[str | None, typer.Option("--preset")] = None,
    config: Annotated[Path | None, typer.Option("--config")] = None,
    dataset: Annotated[str | None, typer.Option("--dataset")] = None,
    chain: Annotated[str | None, typer.Option("--chain")] = None,
    model: Annotated[str | None, typer.Option("--model")] = None,
    feature_set: Annotated[str | None, typer.Option("--feature-set")] = None,
    training_profile: Annotated[str | None, typer.Option("--training")] = None,
    split: Annotated[str | None, typer.Option("--split")] = None,
    tuning_profile: Annotated[str | None, typer.Option("--tuning")] = None,
    tuning_space: Annotated[str | None, typer.Option("--tuning-space")] = None,
    storage_root: Annotated[Path | None, typer.Option("--storage-root")] = None,
    study: Annotated[str | None, typer.Option("--study")] = None,
    trial_count: Annotated[int | None, typer.Option("--trial-count")] = None,
) -> None:
    """Tune model hyperparameters."""
    tune.run(
        load_tune_config(
            preset=preset,
            config_path=config,
            dataset=dataset,
            chain=chain,
            model=model,
            feature_set=feature_set,
            training=training_profile,
            split=split,
            tuning=tuning_profile,
            tuning_space=tuning_space,
            storage_root=storage_root,
            study=study,
            trial_count=trial_count,
        )
    )


@app.command("simulate")
def simulate_command(
    preset: Annotated[str | None, typer.Option("--preset")] = None,
    config: Annotated[Path | None, typer.Option("--config")] = None,
    dataset: Annotated[str | None, typer.Option("--dataset")] = None,
    chain: Annotated[str | None, typer.Option("--chain")] = None,
    model: Annotated[str | None, typer.Option("--model")] = None,
    feature_set: Annotated[str | None, typer.Option("--feature-set")] = None,
    training_profile: Annotated[str | None, typer.Option("--training")] = None,
    simulation_profile: Annotated[str | None, typer.Option("--simulation")] = None,
    storage_root: Annotated[Path | None, typer.Option("--storage-root")] = None,
    variant: Annotated[str | None, typer.Option("--variant")] = None,
    study: Annotated[str | None, typer.Option("--study")] = None,
) -> None:
    """Run evaluation-day simulation from a trained artifact."""
    simulate.run(
        load_simulate_config(
            preset=preset,
            config_path=config,
            dataset=dataset,
            chain=chain,
            model=model,
            feature_set=feature_set,
            training=training_profile,
            simulation=simulation_profile,
            storage_root=storage_root,
            variant=variant,
            study=study,
        )
    )


def main(argv: list[str] | None = None) -> None:
    app(prog_name="spice", args=argv)
