# pyright: strict

"""Workflow command routing."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ...config import (
    AcquireConfig,
    EvaluateConfig,
    TrainConfig,
    TuneConfig,
    WorkflowSelections,
    WorkflowTask,
    resolve_workflow_config,
)
from ...config.registry import load_named_group
from ...core.errors import ConfigResolutionError, SpiceOperatorError
from ...remote import DEFAULT_REMOTE_EXECUTION_NAME, follow_remote_job, submit_remote_workflow


def _selection_option(*param_decls: str, metavar: str, help: str) -> object:
    return typer.Option(*param_decls, metavar=metavar, help=help, rich_help_panel="Selection")


def _execution_option(*param_decls: str, metavar: str, help: str) -> object:
    return typer.Option(*param_decls, metavar=metavar, help=help, rich_help_panel="Execution")


def _output_option(*param_decls: str, metavar: str, help: str) -> object:
    return typer.Option(*param_decls, metavar=metavar, help=help, rich_help_panel="Outputs")


def _append_option(args: list[str], flag: str, value: str | int | Path | None) -> None:
    if value is None:
        return
    args.extend([flag, str(value)])


def _resolve_remote_execution_name(*, preset: str | None, execution: str | None) -> str:
    if execution is not None:
        return execution
    if preset is not None:
        execution_value = load_named_group(preset, "preset").get("execution")
        if execution_value is None:
            return DEFAULT_REMOTE_EXECUTION_NAME
        if isinstance(execution_value, str):
            return execution_value
        raise ConfigResolutionError("preset.execution must be a string")
    return DEFAULT_REMOTE_EXECUTION_NAME


def _submit_remote_workflow(
    *,
    task: WorkflowTask,
    execution_name: str,
    cli_args: list[str],
    detach: bool,
    storage_root: Path | None,
) -> None:
    if storage_root is not None:
        raise SpiceOperatorError("--storage-root is not supported with --remote")
    submission = submit_remote_workflow(
        task,
        cli_args=cli_args,
        execution_name=execution_name,
    )
    typer.echo(
        " ".join(
            [
                f"submitted remote {task.value}",
                f"job_id={submission.job_id}",
                f"execution={submission.execution_name}",
                f"log={submission.log_path}",
            ]
        )
    )
    if detach or not submission.target.spec.follow_by_default:
        return
    try:
        state = follow_remote_job(submission)
    except KeyboardInterrupt:
        typer.echo(f"detached from remote job {submission.job_id}; job continues on cluster")
        return
    if state is not None:
        typer.echo(f"remote job {submission.job_id} finished: {state}")
        if state != "COMPLETED":
            raise SpiceOperatorError(f"Remote job {submission.job_id} ended with state {state}")


def _resolve_acquire_config(
    *,
    preset: str | None,
    dataset: str | None,
    problem: str | None,
    chain: str | None,
    provider: str | None,
    feature_set: str | None,
    storage_root: Path | None,
    dry_run: bool | None,
) -> AcquireConfig:
    return resolve_workflow_config(
        WorkflowTask.ACQUIRE,
        WorkflowSelections(
            preset=preset,
            dataset=dataset,
            problem=problem,
            chain=chain,
            provider=provider,
            feature_set=feature_set,
            storage_root=storage_root,
            dry_run=dry_run,
        ),
    )


def _resolve_train_config(
    *,
    preset: str | None,
    dataset: str | None,
    problem: str | None,
    chain: str | None,
    model: str | None,
    feature_set: str | None,
    prediction: str | None,
    study: str | None,
    variant: str | None,
    storage_root: Path | None,
) -> TrainConfig:
    return resolve_workflow_config(
        WorkflowTask.TRAIN,
        WorkflowSelections(
            preset=preset,
            dataset=dataset,
            problem=problem,
            chain=chain,
            model=model,
            feature_set=feature_set,
            prediction=prediction,
            study=study,
            variant=variant,
            storage_root=storage_root,
        ),
    )


def _resolve_tune_config(
    *,
    preset: str | None,
    dataset: str | None,
    problem: str | None,
    chain: str | None,
    model: str | None,
    feature_set: str | None,
    prediction: str | None,
    study: str | None,
    trial_count: int | None,
    storage_root: Path | None,
) -> TuneConfig:
    return resolve_workflow_config(
        WorkflowTask.TUNE,
        WorkflowSelections(
            preset=preset,
            dataset=dataset,
            problem=problem,
            chain=chain,
            model=model,
            feature_set=feature_set,
            prediction=prediction,
            study=study,
            trial_count=trial_count,
            storage_root=storage_root,
        ),
    )


def _resolve_evaluate_config(
    *,
    preset: str | None,
    dataset: str | None,
    problem: str | None,
    chain: str | None,
    model: str | None,
    feature_set: str | None,
    prediction: str | None,
    study: str | None,
    variant: str | None,
    delay_seconds: int | None,
    storage_root: Path | None,
) -> EvaluateConfig:
    return resolve_workflow_config(
        WorkflowTask.EVALUATE,
        WorkflowSelections(
            preset=preset,
            dataset=dataset,
            problem=problem,
            chain=chain,
            model=model,
            feature_set=feature_set,
            prediction=prediction,
            study=study,
            variant=variant,
            delay_seconds=delay_seconds,
            storage_root=storage_root,
        ),
    )


def acquire_command(
    preset: Annotated[
        str | None,
        _selection_option(
            "--preset",
            metavar="PRESET",
            help="Apply a named preset before selector overrides.",
        ),
    ] = None,
    dataset: Annotated[
        str | None,
        _selection_option("--dataset", metavar="DATASET", help="Use a named dataset spec."),
    ] = None,
    problem: Annotated[
        str | None,
        _selection_option("--problem", metavar="PROBLEM", help="Use a named problem spec."),
    ] = None,
    chain: Annotated[
        str | None,
        _selection_option("--chain", metavar="CHAIN", help="Override the target chain."),
    ] = None,
    provider: Annotated[
        str | None,
        _selection_option("--provider", metavar="PROVIDER", help="Override the RPC provider."),
    ] = None,
    feature_set: Annotated[
        str | None,
        _selection_option(
            "--feature-set",
            metavar="FEATURE_SET",
            help="Use a named feature selection.",
        ),
    ] = None,
    storage_root: Annotated[
        Path | None,
        _output_option(
            "--storage-root",
            metavar="PATH",
            help="Store outputs under a non-default root.",
        ),
    ] = None,
    dry_run: Annotated[
        bool | None,
        typer.Option(
            "--dry-run/--no-dry-run",
            help="Skip persistence and RPC side effects.",
            rich_help_panel="Execution",
        ),
    ] = None,
) -> None:
    from ...workflows import acquire

    acquire.run(
        _resolve_acquire_config(
            preset=preset,
            dataset=dataset,
            problem=problem,
            chain=chain,
            provider=provider,
            feature_set=feature_set,
            storage_root=storage_root,
            dry_run=dry_run,
        )
    )


def train_command(
    preset: Annotated[
        str | None,
        _selection_option(
            "--preset",
            metavar="PRESET",
            help="Apply a named preset before selector overrides.",
        ),
    ] = None,
    dataset: Annotated[
        str | None,
        _selection_option("--dataset", metavar="DATASET", help="Use a named dataset spec."),
    ] = None,
    problem: Annotated[
        str | None,
        _selection_option("--problem", metavar="PROBLEM", help="Use a named problem spec."),
    ] = None,
    chain: Annotated[
        str | None,
        _selection_option("--chain", metavar="CHAIN", help="Override the target chain."),
    ] = None,
    model: Annotated[
        str | None,
        _selection_option("--model", metavar="MODEL", help="Use a named model config."),
    ] = None,
    feature_set: Annotated[
        str | None,
        _selection_option(
            "--feature-set",
            metavar="FEATURE_SET",
            help="Use a named feature selection.",
        ),
    ] = None,
    prediction: Annotated[
        str | None,
        _selection_option(
            "--prediction",
            metavar="PREDICTION",
            help="Use a named prediction config.",
        ),
    ] = None,
    study: Annotated[
        str | None,
        _selection_option("--study", metavar="STUDY", help="Override the study name."),
    ] = None,
    variant: Annotated[
        str | None,
        _selection_option("--variant", metavar="VARIANT", help="Override the artifact variant."),
    ] = None,
    storage_root: Annotated[
        Path | None,
        _output_option(
            "--storage-root",
            metavar="PATH",
            help="Store outputs under a non-default root.",
        ),
    ] = None,
    remote: Annotated[
        bool,
        typer.Option("--remote", help="Submit to the remote university cluster."),
    ] = False,
    execution: Annotated[
        str | None,
        _execution_option(
            "--execution",
            metavar="EXECUTION",
            help="Use a named remote execution spec.",
        ),
    ] = None,
    detach: Annotated[
        bool,
        typer.Option("--detach", help="Submit remote job and exit without following."),
    ] = False,
) -> None:
    if remote:
        args: list[str] = []
        _append_option(args, "--preset", preset)
        _append_option(args, "--dataset", dataset)
        _append_option(args, "--problem", problem)
        _append_option(args, "--chain", chain)
        _append_option(args, "--model", model)
        _append_option(args, "--feature-set", feature_set)
        _append_option(args, "--prediction", prediction)
        _append_option(args, "--study", study)
        _append_option(args, "--variant", variant)
        _submit_remote_workflow(
            task=WorkflowTask.TRAIN,
            execution_name=_resolve_remote_execution_name(preset=preset, execution=execution),
            cli_args=args,
            detach=detach,
            storage_root=storage_root,
        )
        return
    from ...workflows import train

    train.run(
        _resolve_train_config(
            preset=preset,
            dataset=dataset,
            problem=problem,
            chain=chain,
            model=model,
            feature_set=feature_set,
            prediction=prediction,
            storage_root=storage_root,
            variant=variant,
            study=study,
        )
    )


def tune_command(
    preset: Annotated[
        str | None,
        _selection_option(
            "--preset",
            metavar="PRESET",
            help="Apply a named preset before selector overrides.",
        ),
    ] = None,
    dataset: Annotated[
        str | None,
        _selection_option("--dataset", metavar="DATASET", help="Use a named dataset spec."),
    ] = None,
    problem: Annotated[
        str | None,
        _selection_option("--problem", metavar="PROBLEM", help="Use a named problem spec."),
    ] = None,
    chain: Annotated[
        str | None,
        _selection_option("--chain", metavar="CHAIN", help="Override the target chain."),
    ] = None,
    model: Annotated[
        str | None,
        _selection_option("--model", metavar="MODEL", help="Use a named model config."),
    ] = None,
    feature_set: Annotated[
        str | None,
        _selection_option(
            "--feature-set",
            metavar="FEATURE_SET",
            help="Use a named feature selection.",
        ),
    ] = None,
    prediction: Annotated[
        str | None,
        _selection_option(
            "--prediction",
            metavar="PREDICTION",
            help="Use a named prediction config.",
        ),
    ] = None,
    study: Annotated[
        str | None,
        _selection_option("--study", metavar="STUDY", help="Override the study name."),
    ] = None,
    trial_count: Annotated[
        int | None,
        _execution_option(
            "--trial-count",
            metavar="COUNT",
            help="Override the requested trial count.",
        ),
    ] = None,
    storage_root: Annotated[
        Path | None,
        _output_option(
            "--storage-root",
            metavar="PATH",
            help="Store outputs under a non-default root.",
        ),
    ] = None,
    remote: Annotated[
        bool,
        typer.Option("--remote", help="Submit to the remote university cluster."),
    ] = False,
    execution: Annotated[
        str | None,
        _execution_option(
            "--execution",
            metavar="EXECUTION",
            help="Use a named remote execution spec.",
        ),
    ] = None,
    detach: Annotated[
        bool,
        typer.Option("--detach", help="Submit remote job and exit without following."),
    ] = False,
) -> None:
    if remote:
        args: list[str] = []
        _append_option(args, "--preset", preset)
        _append_option(args, "--dataset", dataset)
        _append_option(args, "--problem", problem)
        _append_option(args, "--chain", chain)
        _append_option(args, "--model", model)
        _append_option(args, "--feature-set", feature_set)
        _append_option(args, "--prediction", prediction)
        _append_option(args, "--study", study)
        _append_option(args, "--trial-count", trial_count)
        _submit_remote_workflow(
            task=WorkflowTask.TUNE,
            execution_name=_resolve_remote_execution_name(preset=preset, execution=execution),
            cli_args=args,
            detach=detach,
            storage_root=storage_root,
        )
        return
    from ...workflows import tune

    tune.run(
        _resolve_tune_config(
            preset=preset,
            dataset=dataset,
            problem=problem,
            chain=chain,
            model=model,
            feature_set=feature_set,
            prediction=prediction,
            storage_root=storage_root,
            study=study,
            trial_count=trial_count,
        )
    )


def evaluate_command(
    preset: Annotated[
        str | None,
        _selection_option(
            "--preset",
            metavar="PRESET",
            help="Apply a named preset before selector overrides.",
        ),
    ] = None,
    dataset: Annotated[
        str | None,
        _selection_option("--dataset", metavar="DATASET", help="Use a named dataset spec."),
    ] = None,
    problem: Annotated[
        str | None,
        _selection_option("--problem", metavar="PROBLEM", help="Use a named problem spec."),
    ] = None,
    chain: Annotated[
        str | None,
        _selection_option("--chain", metavar="CHAIN", help="Override the target chain."),
    ] = None,
    model: Annotated[
        str | None,
        _selection_option("--model", metavar="MODEL", help="Use a named model config."),
    ] = None,
    feature_set: Annotated[
        str | None,
        _selection_option(
            "--feature-set",
            metavar="FEATURE_SET",
            help="Use a named feature selection.",
        ),
    ] = None,
    prediction: Annotated[
        str | None,
        _selection_option(
            "--prediction",
            metavar="PREDICTION",
            help="Use a named prediction config.",
        ),
    ] = None,
    study: Annotated[
        str | None,
        _selection_option("--study", metavar="STUDY", help="Override the study name."),
    ] = None,
    variant: Annotated[
        str | None,
        _selection_option("--variant", metavar="VARIANT", help="Override the artifact variant."),
    ] = None,
    delay_seconds: Annotated[
        int | None,
        _execution_option(
            "--delay-seconds",
            metavar="SECONDS",
            help="Override the evaluation delay in seconds.",
        ),
    ] = None,
    storage_root: Annotated[
        Path | None,
        _output_option(
            "--storage-root",
            metavar="PATH",
            help="Store outputs under a non-default root.",
        ),
    ] = None,
    remote: Annotated[
        bool,
        typer.Option("--remote", help="Submit to the remote university cluster."),
    ] = False,
    execution: Annotated[
        str | None,
        _execution_option(
            "--execution",
            metavar="EXECUTION",
            help="Use a named remote execution spec.",
        ),
    ] = None,
    detach: Annotated[
        bool,
        typer.Option("--detach", help="Submit remote job and exit without following."),
    ] = False,
) -> None:
    if remote:
        args: list[str] = []
        _append_option(args, "--preset", preset)
        _append_option(args, "--dataset", dataset)
        _append_option(args, "--problem", problem)
        _append_option(args, "--chain", chain)
        _append_option(args, "--model", model)
        _append_option(args, "--feature-set", feature_set)
        _append_option(args, "--prediction", prediction)
        _append_option(args, "--study", study)
        _append_option(args, "--variant", variant)
        _append_option(args, "--delay-seconds", delay_seconds)
        _submit_remote_workflow(
            task=WorkflowTask.EVALUATE,
            execution_name=_resolve_remote_execution_name(preset=preset, execution=execution),
            cli_args=args,
            detach=detach,
            storage_root=storage_root,
        )
        return
    from ...workflows import evaluate

    evaluate.run(
        _resolve_evaluate_config(
            preset=preset,
            dataset=dataset,
            problem=problem,
            chain=chain,
            model=model,
            feature_set=feature_set,
            prediction=prediction,
            storage_root=storage_root,
            variant=variant,
            study=study,
            delay_seconds=delay_seconds,
        )
    )
