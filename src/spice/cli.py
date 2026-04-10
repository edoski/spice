"""Command-line interface for SPICE."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from .acquisition.provenance import source_manifest_path_for
from .acquisition.raw_validation import RawPullValidationReport, format_raw_pull_validation_report
from .acquisition.rpc_providers import RpcProviderName
from .api import (
    DatasetSnapshotInfo,
    EnrichedDatasetValidation,
    SnapshotAcquireResult,
    _read_snapshot_details,
    _validate_snapshot,
    acquire_snapshot,
    activate_snapshot,
    list_snapshots,
    load_config,
    simulate_model,
    train_model,
)
from .core.config import ChainName, ModelFamily
from .core.console import RichReporter
from .core.constants import SIMULATION_REPORT_FILENAME, TRAIN_REPORT_FILENAME

app = typer.Typer(no_args_is_help=True, add_completion=False)
datasets_app = typer.Typer(no_args_is_help=True)
app.add_typer(datasets_app, name="datasets")


def _echo_validation_report(report: RawPullValidationReport, *, prefix: str) -> None:
    for line in format_raw_pull_validation_report(report):
        typer.echo(f"{prefix}_{line}")


def _echo_enriched_validation(validation: EnrichedDatasetValidation, *, prefix: str) -> None:
    typer.echo(f"{prefix}_status={validation.status}")
    typer.echo(f"{prefix}_path={validation.path}")
    if validation.error is not None:
        typer.echo(f"{prefix}_error={validation.error}")


def _echo_snapshot_summary(summary: DatasetSnapshotInfo) -> None:
    typer.echo(f"chain={summary.chain}")
    typer.echo(f"snapshot={summary.name}")
    typer.echo(f"active={str(summary.active).lower()}")
    typer.echo(f"created_at_utc={summary.created_at_utc}")
    typer.echo(f"updated_at_utc={summary.updated_at_utc}")
    typer.echo(f"pull_provider={summary.pull_provider}")
    typer.echo(f"enrich_provider={summary.enrich_provider}")
    typer.echo(f"history={summary.history_start_timestamp}:{summary.history_end_timestamp}")
    typer.echo(f"evaluation={summary.evaluation_start_timestamp}:{summary.evaluation_end_timestamp}")


def _echo_snapshot_acquire_result(result: SnapshotAcquireResult) -> None:
    typer.echo(f"snapshot={result.snapshot_name}")
    typer.echo(f"snapshot_root={result.snapshot_root}")
    typer.echo(f"activated={str(result.activated).lower()}")
    typer.echo(f"pull_provider={result.pull_provider}")
    typer.echo(f"enrich_provider={result.enrich_provider}")
    for segment_result in (result.history, result.evaluation):
        prefix = segment_result.segment.value
        typer.echo(f"{prefix}_raw_output_dir={segment_result.raw.output_dir}")
        typer.echo(f"{prefix}_command={segment_result.raw.command}")
        typer.echo(f"{prefix}_completed_chunks={segment_result.raw.completed_chunks}")
        typer.echo(f"{prefix}_expected_chunks={segment_result.raw.expected_chunks}")
        if segment_result.raw.source_manifest_path is not None:
            typer.echo(f"{prefix}_source_manifest_path={segment_result.raw.source_manifest_path}")
        if segment_result.raw.validation is not None:
            _echo_validation_report(segment_result.raw.validation, prefix=f"{prefix}_raw")
        typer.echo(f"{prefix}_enriched_output_dir={segment_result.enriched_output_dir}")
        typer.echo(f"{prefix}_enriched_files={segment_result.enriched_file_count}")
        typer.echo(
            f"{prefix}_enriched_source_manifest_path={segment_result.enriched_source_manifest_path}"
        )


def _parse_chain_snapshot_args(
    config_path: Path,
    chain_or_snapshot: str | None,
    snapshot_name: str | None,
) -> tuple[ChainName | None, str | None]:
    config = load_config(config_path)
    if chain_or_snapshot is None:
        return None, snapshot_name
    if snapshot_name is None:
        try:
            return ChainName(chain_or_snapshot), None
        except ValueError:
            if len(config.chains) != 1:
                raise typer.BadParameter(
                    "chain is required when config contains multiple chains"
                ) from None
            return None, chain_or_snapshot
    try:
        return ChainName(chain_or_snapshot), snapshot_name
    except ValueError as exc:
        raise typer.BadParameter(f"Unknown chain: {chain_or_snapshot}") from exc


def _resolve_cli_chain(config_path: Path, chain_name: ChainName | None) -> ChainName:
    config = load_config(config_path)
    if chain_name is not None:
        return chain_name
    if len(config.chains) != 1:
        raise typer.BadParameter("chain is required when config contains multiple chains")
    return config.chains[0].name


def _parse_activate_args(
    config_path: Path,
    chain_or_snapshot: str,
    snapshot_name: str | None,
) -> tuple[ChainName | None, str]:
    config = load_config(config_path)
    if snapshot_name is None:
        if len(config.chains) != 1:
            raise typer.BadParameter("chain is required when config contains multiple chains")
        return None, chain_or_snapshot
    try:
        return ChainName(chain_or_snapshot), snapshot_name
    except ValueError as exc:
        raise typer.BadParameter(f"Unknown chain: {chain_or_snapshot}") from exc


def _parse_chain_delay_args(
    chain_or_delay: str | None,
    max_delay_seconds: int | None,
) -> tuple[ChainName | None, int | None]:
    if chain_or_delay is None:
        return None, max_delay_seconds
    if max_delay_seconds is not None:
        try:
            return ChainName(chain_or_delay), max_delay_seconds
        except ValueError as exc:
            raise typer.BadParameter(f"Unknown chain: {chain_or_delay}") from exc
    try:
        return ChainName(chain_or_delay), None
    except ValueError:
        try:
            return None, int(chain_or_delay)
        except ValueError as exc:
            raise typer.BadParameter(
                "Expected CHAIN_NAME or MAX_DELAY_SECONDS"
            ) from exc


@app.command("acquire")
def acquire(
    config_path: Path,
    chain_name: Annotated[ChainName | None, typer.Argument()] = None,
    snapshot: Annotated[str, typer.Option()] = "working",
    provider: Annotated[RpcProviderName | None, typer.Option()] = None,
    pull_provider: Annotated[RpcProviderName | None, typer.Option()] = None,
    enrich_provider: Annotated[RpcProviderName | None, typer.Option()] = None,
    dry_run: Annotated[bool, typer.Option()] = True,
    overwrite: Annotated[bool, typer.Option()] = False,
    activate: Annotated[bool, typer.Option()] = True,
    batch_size: Annotated[int, typer.Option()] = 100,
    max_methods_per_second: Annotated[float, typer.Option()] = 20.0,
) -> None:
    config = load_config(config_path)
    with RichReporter() as reporter:
        result = acquire_snapshot(
            config,
            chain_name,
            snapshot_name=snapshot,
            rpc_provider=provider,
            pull_provider=pull_provider,
            enrich_provider=enrich_provider,
            dry_run=dry_run,
            overwrite=overwrite,
            activate=activate,
            batch_size=batch_size,
            max_methods_per_second=max_methods_per_second,
            reporter=reporter,
            config_path=config_path,
        )
    _echo_snapshot_acquire_result(result)


@app.command("train")
def train(
    config_path: Path,
    family: ModelFamily,
    chain_or_delay: Annotated[str | None, typer.Argument()] = None,
    max_delay_seconds: Annotated[int | None, typer.Argument()] = None,
    snapshot: Annotated[str | None, typer.Option()] = None,
    run_name: Annotated[str | None, typer.Option()] = None,
    device: Annotated[str, typer.Option()] = "auto",
    evaluate: Annotated[bool, typer.Option()] = False,
) -> None:
    chain_name, resolved_delay = _parse_chain_delay_args(chain_or_delay, max_delay_seconds)
    config = load_config(config_path)
    with RichReporter() as reporter:
        result = train_model(
            config,
            family,
            chain_name,
            resolved_delay,
            snapshot_name=snapshot,
            run_name=run_name,
            device=device,
            evaluate=evaluate,
            reporter=reporter,
        )
    report = result.training_report
    typer.echo(f"snapshot={result.snapshot_name}")
    typer.echo(f"artifact_dir={result.artifact_dir}")
    typer.echo(f"n_blocks_available={report.n_blocks_available}")
    typer.echo(f"n_blocks_used={report.n_blocks_used}")
    typer.echo(f"n_examples_total={report.n_examples_total}")
    typer.echo(f"lookback_steps={report.lookback_steps}")
    typer.echo(f"max_extra_wait_steps={report.max_extra_wait_steps}")
    typer.echo(f"action_count={report.action_count}")
    typer.echo(f"n_features={report.n_features}")
    typer.echo(f"train_examples={report.split_sizes.train_examples}")
    typer.echo(f"validation_examples={report.split_sizes.validation_examples}")
    typer.echo(f"test_examples={report.split_sizes.test_examples}")
    typer.echo(f"best_epoch={report.best_epoch}")
    typer.echo(f"test_loss={report.test_metrics.total_loss:.6f}")
    typer.echo(f"test_accuracy={report.test_metrics.accuracy:.4f}")
    typer.echo(
        f"test_profit_over_baseline={report.test_metrics.mean_profit_over_baseline:.6f}"
    )
    typer.echo(f"train_report_path={result.artifact_dir / TRAIN_REPORT_FILENAME}")
    if result.simulation_report is not None:
        typer.echo(
            f"simulation_profit_over_baseline={result.simulation_report.profit_over_baseline.mean:.6f}"
        )
        typer.echo(
            f"simulation_cost_over_optimum={result.simulation_report.cost_over_optimum.mean:.6f}"
        )
        typer.echo(
            "simulation_baseline_cost_over_optimum="
            f"{result.simulation_report.baseline_cost_over_optimum.mean:.6f}"
        )
        typer.echo(f"simulation_report_path={result.artifact_dir / SIMULATION_REPORT_FILENAME}")


@app.command("simulate")
def simulate(
    config_path: Path,
    family: ModelFamily,
    chain_or_delay: Annotated[str | None, typer.Argument()] = None,
    max_delay_seconds: Annotated[int | None, typer.Argument()] = None,
    snapshot: Annotated[str | None, typer.Option()] = None,
    run_name: Annotated[str | None, typer.Option()] = None,
    device: Annotated[str, typer.Option()] = "auto",
) -> None:
    chain_name, resolved_delay = _parse_chain_delay_args(chain_or_delay, max_delay_seconds)
    result = simulate_model(
        load_config(config_path),
        family,
        chain_name,
        resolved_delay,
        snapshot_name=snapshot,
        run_name=run_name,
        device=device,
    )
    report = result.report
    typer.echo(f"snapshot={result.snapshot_name}")
    typer.echo(f"artifact_dir={result.artifact_dir}")
    typer.echo(f"n_history_context_blocks={report.n_history_context_blocks}")
    typer.echo(f"n_evaluation_blocks={report.n_evaluation_blocks}")
    typer.echo(f"n_examples_total={report.n_examples_total}")
    typer.echo(f"simulation_profit_over_baseline={report.profit_over_baseline.mean:.6f}")
    typer.echo(f"simulation_cost_over_optimum={report.cost_over_optimum.mean:.6f}")
    typer.echo(
        "simulation_baseline_cost_over_optimum="
        f"{report.baseline_cost_over_optimum.mean:.6f}"
    )
    typer.echo(f"simulation_report_path={result.artifact_dir / SIMULATION_REPORT_FILENAME}")


@datasets_app.command("list")
def list_datasets(
    config_path: Path,
    chain_name: Annotated[ChainName | None, typer.Argument()] = None,
) -> None:
    items = list_snapshots(load_config(config_path), chain_name)
    if not items:
        typer.echo("snapshots=0")
        return
    for index, item in enumerate(items):
        if index:
            typer.echo("")
        _echo_snapshot_summary(item)


@datasets_app.command("show")
def show_dataset(
    config_path: Path,
    chain_or_snapshot: Annotated[str | None, typer.Argument()] = None,
    snapshot_name: Annotated[str | None, typer.Argument()] = None,
) -> None:
    chain_name, resolved_snapshot = _parse_chain_snapshot_args(
        config_path,
        chain_or_snapshot,
        snapshot_name,
    )
    config = load_config(config_path)
    details = _read_snapshot_details(
        config,
        config.resolve_chain(_resolve_cli_chain(config_path, chain_name)),
        resolved_snapshot,
    )
    _echo_snapshot_summary(details.summary)
    typer.echo(f"snapshot_root={details.paths.snapshot_root}")
    typer.echo(f"raw_history_dir={details.paths.raw_history_dir}")
    typer.echo(f"raw_evaluation_dir={details.paths.raw_evaluation_dir}")
    typer.echo(f"enriched_history_dir={details.paths.enriched_history_dir}")
    typer.echo(f"enriched_evaluation_dir={details.paths.enriched_evaluation_dir}")
    typer.echo(f"raw_history_manifest={source_manifest_path_for(details.paths.raw_history_dir)}")
    typer.echo(
        f"raw_evaluation_manifest={source_manifest_path_for(details.paths.raw_evaluation_dir)}"
    )
    typer.echo(
        f"enriched_history_manifest={source_manifest_path_for(details.paths.enriched_history_dir)}"
    )
    typer.echo(
        "enriched_evaluation_manifest="
        f"{source_manifest_path_for(details.paths.enriched_evaluation_dir)}"
    )


@datasets_app.command("validate")
def validate_dataset(
    config_path: Path,
    chain_or_snapshot: Annotated[str | None, typer.Argument()] = None,
    snapshot_name: Annotated[str | None, typer.Argument()] = None,
) -> None:
    chain_name, resolved_snapshot = _parse_chain_snapshot_args(
        config_path,
        chain_or_snapshot,
        snapshot_name,
    )
    config = load_config(config_path)
    chain = config.resolve_chain(_resolve_cli_chain(config_path, chain_name))
    report = _validate_snapshot(config, chain, resolved_snapshot)
    typer.echo(f"snapshot={report.snapshot_name}")
    typer.echo(f"status={report.status}")
    _echo_validation_report(report.history_raw, prefix="history_raw")
    _echo_validation_report(report.evaluation_raw, prefix="evaluation_raw")
    _echo_enriched_validation(report.history_enriched, prefix="history_enriched")
    _echo_enriched_validation(report.evaluation_enriched, prefix="evaluation_enriched")
    if report.status == "error":
        raise typer.Exit(code=1)


@datasets_app.command("activate")
def activate_dataset(
    config_path: Path,
    chain_or_snapshot: Annotated[str, typer.Argument()],
    snapshot_name: Annotated[str | None, typer.Argument()] = None,
) -> None:
    chain_name, resolved_snapshot = _parse_activate_args(
        config_path,
        chain_or_snapshot,
        snapshot_name,
    )
    result = activate_snapshot(load_config(config_path), resolved_snapshot, chain_name)
    _echo_snapshot_summary(result)


if __name__ == "__main__":
    app()
