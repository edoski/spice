# pyright: strict

"""Workflow command routing."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

import typer

from ...config.models import WorkflowTask
from ...config.resolution import WorkflowConfig
from ...config.selections import (
    EvaluateWorkflowSelection,
    TrainWorkflowSelection,
    TuneWorkflowSelection,
)
from ...core.errors import SpiceOperatorError
from ...execution.session import ExecutionSession, open_execution_session
from ..options import DEFAULT_REMOTE_TARGET, RemoteTargetOption
from ..selection import (
    build_acquire_workflow_config,
    build_model_workflow_command_plan,
)


def _selection_option(*param_decls: str, metavar: str, help: str) -> object:
    return typer.Option(*param_decls, metavar=metavar, help=help, rich_help_panel="Selection")


def _execution_option(*param_decls: str, metavar: str, help: str) -> object:
    return typer.Option(*param_decls, metavar=metavar, help=help, rich_help_panel="Execution")


def _output_option(*param_decls: str, metavar: str, help: str) -> object:
    return typer.Option(*param_decls, metavar=metavar, help=help, rich_help_panel="Outputs")


def _submit_selected_workflow(
    *,
    task: WorkflowTask,
    config: WorkflowConfig,
    session: ExecutionSession,
    dependency: str | None,
    detach: bool,
) -> None:
    submission = session.submit_workflow(
        task,
        config=config,
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
        state = session.follow_job(submission)
    except KeyboardInterrupt:
        typer.echo(f"submit detached job_id={submission.job_id} state=running")
        return
    if state is None:
        return
    typer.echo(f"submit finished job_id={submission.job_id} state={state}")
    if state != "COMPLETED":
        raise SpiceOperatorError(f"Job {submission.job_id} ended with state {state}")


def _run_or_submit_model_workflow(
    *,
    task: WorkflowTask,
    selection_type: type[TrainWorkflowSelection]
    | type[TuneWorkflowSelection]
    | type[EvaluateWorkflowSelection],
    runner: Callable[[Any], None],
    submit: bool,
    target: str,
    dependency: str | None,
    detach: bool,
    storage_root: Path | None,
    surface: str | None,
    chain: str | None,
    problem: str | None,
    features: str | None,
    objective: str | None,
    evaluation: str | None,
    model: str | None,
    tuning_space: str | None,
    training: str | None,
    split: str | None,
    tuning: str | None,
    study: str | None,
    variant: str | None = None,
    delay_seconds: int | None = None,
    trial_count: int | None = None,
) -> None:
    plan = build_model_workflow_command_plan(
        task=task,
        selection_type=selection_type,
        submit=submit,
        dependency=dependency,
        detach=detach,
        storage_root=storage_root,
        surface=surface,
        chain=chain,
        problem=problem,
        features=features,
        objective=objective,
        evaluation=evaluation,
        model=model,
        tuning_space=tuning_space,
        training=training,
        split=split,
        tuning=tuning,
        study=study,
        variant=variant,
        delay_seconds=delay_seconds,
        trial_count=trial_count,
    )
    if submit:
        session = open_execution_session(target)
        _submit_selected_workflow(
            task=task,
            config=plan.config,
            session=session,
            dependency=dependency,
            detach=detach,
        )
        return
    runner(plan.config)


def acquire_command(
    surface: Annotated[
        str | None,
        _selection_option(
            "--surface",
            metavar="SURFACE",
            help="Resolve a named workflow surface.",
        ),
    ] = None,
    chain: Annotated[
        str | None,
        _selection_option("--chain", metavar="CHAIN", help="Override the target chain."),
    ] = None,
    problem: Annotated[
        str | None,
        _selection_option("--problem", metavar="PROBLEM", help="Override the problem spec."),
    ] = None,
    features: Annotated[
        str | None,
        _selection_option(
            "--features",
            metavar="FEATURES",
            help="Override the features spec.",
        ),
    ] = None,
    provider: Annotated[
        str | None,
        _selection_option(
            "--provider",
            metavar="PROVIDER",
            help="Override the RPC provider spec.",
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
        build_acquire_workflow_config(
            surface=surface,
            chain=chain,
            problem=problem,
            features=features,
            provider=provider,
            storage_root=storage_root,
            dry_run=dry_run,
        )
    )


def train_command(
    surface: Annotated[
        str | None,
        _selection_option(
            "--surface",
            metavar="SURFACE",
            help="Resolve a named workflow surface.",
        ),
    ] = None,
    chain: Annotated[
        str | None,
        _selection_option("--chain", metavar="CHAIN", help="Override the target chain."),
    ] = None,
    problem: Annotated[
        str | None,
        _selection_option("--problem", metavar="PROBLEM", help="Override the problem spec."),
    ] = None,
    features: Annotated[
        str | None,
        _selection_option(
            "--features",
            metavar="FEATURES",
            help="Override the features spec.",
        ),
    ] = None,
    objective: Annotated[
        str | None,
        _selection_option(
            "--objective",
            metavar="OBJECTIVE",
            help="Override the objective spec.",
        ),
    ] = None,
    evaluation: Annotated[
        str | None,
        _selection_option(
            "--evaluation",
            metavar="EVALUATION",
            help="Override the evaluation spec.",
        ),
    ] = None,
    model: Annotated[
        str | None,
        _selection_option("--model", metavar="MODEL", help="Override the model spec."),
    ] = None,
    tuning_space: Annotated[
        str | None,
        _selection_option(
            "--tuning-space",
            metavar="TUNING_SPACE",
            help="Override the tuning-space spec.",
        ),
    ] = None,
    training: Annotated[
        str | None,
        _selection_option(
            "--training",
            metavar="TRAINING",
            help="Override the training spec.",
        ),
    ] = None,
    split: Annotated[
        str | None,
        _selection_option("--split", metavar="SPLIT", help="Override the split spec."),
    ] = None,
    tuning: Annotated[
        str | None,
        _selection_option("--tuning", metavar="TUNING", help="Override the tuning spec."),
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
        _execution_option(
            "--dependency",
            metavar="DEPENDENCY",
            help="Pass one Slurm dependency spec such as afterok:12345.",
        ),
    ] = None,
    target: RemoteTargetOption = DEFAULT_REMOTE_TARGET,
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

    _run_or_submit_model_workflow(
        task=WorkflowTask.TRAIN,
        selection_type=TrainWorkflowSelection,
        runner=train.run,
        submit=submit,
        target=target,
        dependency=dependency,
        detach=detach,
        storage_root=storage_root,
        surface=surface,
        chain=chain,
        problem=problem,
        features=features,
        objective=objective,
        evaluation=evaluation,
        model=model,
        tuning_space=tuning_space,
        training=training,
        split=split,
        tuning=tuning,
        study=study,
        variant=variant,
    )


def tune_command(
    surface: Annotated[
        str | None,
        _selection_option(
            "--surface",
            metavar="SURFACE",
            help="Resolve a named workflow surface.",
        ),
    ] = None,
    chain: Annotated[
        str | None,
        _selection_option("--chain", metavar="CHAIN", help="Override the target chain."),
    ] = None,
    problem: Annotated[
        str | None,
        _selection_option("--problem", metavar="PROBLEM", help="Override the problem spec."),
    ] = None,
    features: Annotated[
        str | None,
        _selection_option(
            "--features",
            metavar="FEATURES",
            help="Override the features spec.",
        ),
    ] = None,
    objective: Annotated[
        str | None,
        _selection_option(
            "--objective",
            metavar="OBJECTIVE",
            help="Override the objective spec.",
        ),
    ] = None,
    evaluation: Annotated[
        str | None,
        _selection_option(
            "--evaluation",
            metavar="EVALUATION",
            help="Override the evaluation spec.",
        ),
    ] = None,
    model: Annotated[
        str | None,
        _selection_option("--model", metavar="MODEL", help="Override the model spec."),
    ] = None,
    tuning_space: Annotated[
        str | None,
        _selection_option(
            "--tuning-space",
            metavar="TUNING_SPACE",
            help="Override the tuning-space spec.",
        ),
    ] = None,
    training: Annotated[
        str | None,
        _selection_option(
            "--training",
            metavar="TRAINING",
            help="Override the training spec.",
        ),
    ] = None,
    split: Annotated[
        str | None,
        _selection_option("--split", metavar="SPLIT", help="Override the split spec."),
    ] = None,
    tuning: Annotated[
        str | None,
        _selection_option("--tuning", metavar="TUNING", help="Override the tuning spec."),
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
        _execution_option(
            "--dependency",
            metavar="DEPENDENCY",
            help="Pass one Slurm dependency spec such as afterok:12345.",
        ),
    ] = None,
    target: RemoteTargetOption = DEFAULT_REMOTE_TARGET,
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

    _run_or_submit_model_workflow(
        task=WorkflowTask.TUNE,
        selection_type=TuneWorkflowSelection,
        runner=tune.run,
        submit=submit,
        target=target,
        dependency=dependency,
        detach=detach,
        storage_root=storage_root,
        surface=surface,
        chain=chain,
        problem=problem,
        features=features,
        objective=objective,
        evaluation=evaluation,
        model=model,
        tuning_space=tuning_space,
        training=training,
        split=split,
        tuning=tuning,
        study=study,
        trial_count=trial_count,
    )


def evaluate_command(
    surface: Annotated[
        str | None,
        _selection_option(
            "--surface",
            metavar="SURFACE",
            help="Resolve a named workflow surface.",
        ),
    ] = None,
    chain: Annotated[
        str | None,
        _selection_option("--chain", metavar="CHAIN", help="Override the target chain."),
    ] = None,
    problem: Annotated[
        str | None,
        _selection_option("--problem", metavar="PROBLEM", help="Override the problem spec."),
    ] = None,
    features: Annotated[
        str | None,
        _selection_option(
            "--features",
            metavar="FEATURES",
            help="Override the features spec.",
        ),
    ] = None,
    objective: Annotated[
        str | None,
        _selection_option(
            "--objective",
            metavar="OBJECTIVE",
            help="Override the objective spec.",
        ),
    ] = None,
    evaluation: Annotated[
        str | None,
        _selection_option(
            "--evaluation",
            metavar="EVALUATION",
            help="Override the evaluation spec.",
        ),
    ] = None,
    model: Annotated[
        str | None,
        _selection_option("--model", metavar="MODEL", help="Override the model spec."),
    ] = None,
    tuning_space: Annotated[
        str | None,
        _selection_option(
            "--tuning-space",
            metavar="TUNING_SPACE",
            help="Override the tuning-space spec.",
        ),
    ] = None,
    training: Annotated[
        str | None,
        _selection_option(
            "--training",
            metavar="TRAINING",
            help="Override the training spec.",
        ),
    ] = None,
    split: Annotated[
        str | None,
        _selection_option("--split", metavar="SPLIT", help="Override the split spec."),
    ] = None,
    tuning: Annotated[
        str | None,
        _selection_option("--tuning", metavar="TUNING", help="Override the tuning spec."),
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
        _execution_option(
            "--dependency",
            metavar="DEPENDENCY",
            help="Pass one Slurm dependency spec such as afterok:12345.",
        ),
    ] = None,
    target: RemoteTargetOption = DEFAULT_REMOTE_TARGET,
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

    _run_or_submit_model_workflow(
        task=WorkflowTask.EVALUATE,
        selection_type=EvaluateWorkflowSelection,
        runner=evaluate.run,
        submit=submit,
        target=target,
        dependency=dependency,
        detach=detach,
        storage_root=storage_root,
        surface=surface,
        chain=chain,
        problem=problem,
        features=features,
        objective=objective,
        evaluation=evaluation,
        model=model,
        tuning_space=tuning_space,
        training=training,
        split=split,
        tuning=tuning,
        study=study,
        variant=variant,
        delay_seconds=delay_seconds,
    )
