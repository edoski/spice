# pyright: strict

"""Workflow command routing."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from ...config import WorkflowSelections, WorkflowTask, resolve_workflow_config
from ...core.errors import SpiceOperatorError
from ...execution import follow_execution_job, submit_execution_workflow


def _selection_option(*param_decls: str, metavar: str, help: str) -> object:
    return typer.Option(*param_decls, metavar=metavar, help=help, rich_help_panel="Selection")


def _workflow_option(*param_decls: str, metavar: str, help: str) -> object:
    return typer.Option(*param_decls, metavar=metavar, help=help, rich_help_panel="Execution")


def _output_option(*param_decls: str, metavar: str, help: str) -> object:
    return typer.Option(*param_decls, metavar=metavar, help=help, rich_help_panel="Outputs")


def _submission_option(*param_decls: str, metavar: str, help: str) -> object:
    return typer.Option(*param_decls, metavar=metavar, help=help, rich_help_panel="Execution")


def _append_option(args: list[str], flag: str, value: str | int | Path | None) -> None:
    if value is None:
        return
    args.extend([flag, str(value)])


def _build_cli_args(*options: tuple[str, str | int | Path | None]) -> list[str]:
    args: list[str] = []
    for flag, value in options:
        _append_option(args, flag, value)
    return args


def _submit_selected_workflow(
    *,
    task: WorkflowTask,
    dependency: str | None,
    detach: bool,
    cli_options: list[tuple[str, str | int | Path | None]],
) -> None:
    submission = submit_execution_workflow(
        task,
        cli_args=_build_cli_args(*cli_options),
        dependency=dependency,
    )
    typer.echo(
        " ".join(
            [
                "submit",
                f"workflow={task.value}",
                f"job_id={submission.job_id}",
                f"log={submission.log_path}",
            ]
        )
    )
    if detach or not submission.target.spec.follow_by_default:
        return
    try:
        state = follow_execution_job(submission)
    except KeyboardInterrupt:
        typer.echo(f"submit detached job_id={submission.job_id} state=running")
        return
    if state is None:
        return
    typer.echo(f"submit finished job_id={submission.job_id} state={state}")
    if state != "COMPLETED":
        raise SpiceOperatorError(f"Job {submission.job_id} ended with state {state}")


def _validate_submission_flags(
    *,
    submit: bool,
    dependency: str | None,
    detach: bool,
    storage_root: Path | None,
) -> None:
    if submit:
        if storage_root is not None:
            raise SpiceOperatorError("--storage-root cannot be combined with --submit")
        return
    if dependency is not None or detach:
        raise SpiceOperatorError("--dependency and --detach require --submit")


def _run_resolved_workflow(
    *,
    task: WorkflowTask,
    runner: Callable[..., None],
    selections: WorkflowSelections,
) -> None:
    runner(resolve_workflow_config(task, selections))


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
        resolve_workflow_config(
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
    dataset_builder: Annotated[
        str | None,
        _selection_option(
            "--dataset-builder",
            metavar="DATASET_BUILDER",
            help="Use a named dataset builder config.",
        ),
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
    evaluation: Annotated[
        str | None,
        _selection_option(
            "--evaluation",
            metavar="EVALUATION",
            help="Use a named evaluation config.",
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
    submit: Annotated[
        bool,
        typer.Option(
            "--submit",
            help="Submit the workflow to the checked-in execution target.",
            rich_help_panel="Execution",
        ),
    ] = False,
    dependency: Annotated[
        str | None,
        _submission_option(
            "--dependency",
            metavar="DEPENDENCY",
            help="Pass one Slurm dependency spec such as afterok:12345.",
        ),
    ] = None,
    detach: Annotated[
        bool,
        typer.Option(
            "--detach",
            help="Submit and exit without following the job.",
            rich_help_panel="Execution",
        ),
    ] = False,
) -> None:
    from ...workflows import train

    _validate_submission_flags(
        submit=submit,
        dependency=dependency,
        detach=detach,
        storage_root=storage_root,
    )
    if submit:
        _submit_selected_workflow(
            task=WorkflowTask.TRAIN,
            dependency=dependency,
            detach=detach,
            cli_options=[
                ("--preset", preset),
                ("--dataset", dataset),
                ("--problem", problem),
                ("--chain", chain),
                ("--model", model),
                ("--dataset-builder", dataset_builder),
                ("--feature-set", feature_set),
                ("--prediction", prediction),
                ("--evaluation", evaluation),
                ("--study", study),
                ("--variant", variant),
            ],
        )
        return
    _run_resolved_workflow(
        task=WorkflowTask.TRAIN,
        runner=train.run,
        selections=WorkflowSelections(
            preset=preset,
            dataset=dataset,
            problem=problem,
            chain=chain,
            model=model,
            dataset_builder=dataset_builder,
            feature_set=feature_set,
            prediction=prediction,
            evaluation=evaluation,
            storage_root=storage_root,
            variant=variant,
            study=study,
        ),
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
    dataset_builder: Annotated[
        str | None,
        _selection_option(
            "--dataset-builder",
            metavar="DATASET_BUILDER",
            help="Use a named dataset builder config.",
        ),
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
        _workflow_option(
            "--trial-count",
            metavar="COUNT",
            help="Override the requested trial count.",
        ),
    ] = None,
    evaluation: Annotated[
        str | None,
        _selection_option(
            "--evaluation",
            metavar="EVALUATION",
            help="Use a named evaluation config.",
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
    submit: Annotated[
        bool,
        typer.Option(
            "--submit",
            help="Submit the workflow to the checked-in execution target.",
            rich_help_panel="Execution",
        ),
    ] = False,
    dependency: Annotated[
        str | None,
        _submission_option(
            "--dependency",
            metavar="DEPENDENCY",
            help="Pass one Slurm dependency spec such as afterok:12345.",
        ),
    ] = None,
    detach: Annotated[
        bool,
        typer.Option(
            "--detach",
            help="Submit and exit without following the job.",
            rich_help_panel="Execution",
        ),
    ] = False,
) -> None:
    from ...workflows import tune

    _validate_submission_flags(
        submit=submit,
        dependency=dependency,
        detach=detach,
        storage_root=storage_root,
    )
    if submit:
        _submit_selected_workflow(
            task=WorkflowTask.TUNE,
            dependency=dependency,
            detach=detach,
            cli_options=[
                ("--preset", preset),
                ("--dataset", dataset),
                ("--problem", problem),
                ("--chain", chain),
                ("--model", model),
                ("--dataset-builder", dataset_builder),
                ("--feature-set", feature_set),
                ("--prediction", prediction),
                ("--evaluation", evaluation),
                ("--study", study),
                ("--trial-count", trial_count),
            ],
        )
        return
    _run_resolved_workflow(
        task=WorkflowTask.TUNE,
        runner=tune.run,
        selections=WorkflowSelections(
            preset=preset,
            dataset=dataset,
            problem=problem,
            chain=chain,
            model=model,
            dataset_builder=dataset_builder,
            feature_set=feature_set,
            prediction=prediction,
            evaluation=evaluation,
            storage_root=storage_root,
            study=study,
            trial_count=trial_count,
        ),
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
    dataset_builder: Annotated[
        str | None,
        _selection_option(
            "--dataset-builder",
            metavar="DATASET_BUILDER",
            help="Use a named dataset builder config.",
        ),
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
    evaluation: Annotated[
        str | None,
        _selection_option(
            "--evaluation",
            metavar="EVALUATION",
            help="Use a named evaluation config.",
        ),
    ] = None,
    delay_seconds: Annotated[
        int | None,
        _workflow_option(
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
    submit: Annotated[
        bool,
        typer.Option(
            "--submit",
            help="Submit the workflow to the checked-in execution target.",
            rich_help_panel="Execution",
        ),
    ] = False,
    dependency: Annotated[
        str | None,
        _submission_option(
            "--dependency",
            metavar="DEPENDENCY",
            help="Pass one Slurm dependency spec such as afterok:12345.",
        ),
    ] = None,
    detach: Annotated[
        bool,
        typer.Option(
            "--detach",
            help="Submit and exit without following the job.",
            rich_help_panel="Execution",
        ),
    ] = False,
) -> None:
    from ...workflows import evaluate

    _validate_submission_flags(
        submit=submit,
        dependency=dependency,
        detach=detach,
        storage_root=storage_root,
    )
    if submit:
        _submit_selected_workflow(
            task=WorkflowTask.EVALUATE,
            dependency=dependency,
            detach=detach,
            cli_options=[
                ("--preset", preset),
                ("--dataset", dataset),
                ("--problem", problem),
                ("--chain", chain),
                ("--model", model),
                ("--dataset-builder", dataset_builder),
                ("--feature-set", feature_set),
                ("--prediction", prediction),
                ("--evaluation", evaluation),
                ("--study", study),
                ("--variant", variant),
                ("--delay-seconds", delay_seconds),
            ],
        )
        return
    _run_resolved_workflow(
        task=WorkflowTask.EVALUATE,
        runner=evaluate.run,
        selections=WorkflowSelections(
            preset=preset,
            dataset=dataset,
            problem=problem,
            chain=chain,
            model=model,
            dataset_builder=dataset_builder,
            feature_set=feature_set,
            prediction=prediction,
            evaluation=evaluation,
            storage_root=storage_root,
            variant=variant,
            study=study,
            delay_seconds=delay_seconds,
        ),
    )
