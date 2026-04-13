"""Explicit Typer CLI over the split config system."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from .config.registry import ConfigGroup

app = typer.Typer(
    name="spice",
    help="SPICE workflow CLI.",
    epilog="Example:\n  spice acquire --preset icdcs_2026",
    no_args_is_help=True,
    add_completion=True,
)
config_app = typer.Typer(
    help="Author saved config specs.",
    no_args_is_help=True,
)
show_app = typer.Typer(
    help="Query stored datasets, studies, and artifacts.",
    no_args_is_help=True,
)
delete_app = typer.Typer(
    help="Delete stored datasets, studies, and artifacts.",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")
app.add_typer(show_app, name="show")
app.add_typer(delete_app, name="delete")
_CONFIG_GROUP_HELP = (
    "One of: chain, provider, dataset, task, execution, feature-set, preset."
)


def _run_acquire(
    *,
    preset: str | None,
    config: Path | None,
    dataset: str | None,
    task: str | None,
    chain: str | None,
    provider: str | None,
    feature_set: str | None,
    acquisition_profile: str | None,
    storage_root: Path | None,
    dry_run: bool | None,
) -> None:
    from .config import load_acquire_config
    from .workflows import acquire

    acquire.run(
        load_acquire_config(
            preset=preset,
            config_path=config,
            dataset=dataset,
            task=task,
            chain=chain,
            provider=provider,
            feature_set=feature_set,
            acquisition=acquisition_profile,
            storage_root=storage_root,
            dry_run=dry_run,
        )
    )


def _run_train(
    *,
    preset: str | None,
    config: Path | None,
    dataset: str | None,
    task: str | None,
    chain: str | None,
    model: str | None,
    feature_set: str | None,
    training_profile: str | None,
    split: str | None,
    storage_root: Path | None,
    variant: str | None,
    study: str | None,
) -> None:
    from .config import load_train_config
    from .workflows import train

    train.run(
        load_train_config(
            preset=preset,
            config_path=config,
            dataset=dataset,
            task=task,
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


def _run_tune(
    *,
    preset: str | None,
    config: Path | None,
    dataset: str | None,
    task: str | None,
    chain: str | None,
    model: str | None,
    feature_set: str | None,
    training_profile: str | None,
    split: str | None,
    tuning_profile: str | None,
    tuning_space: str | None,
    storage_root: Path | None,
    study: str | None,
    trial_count: int | None,
) -> None:
    from .config import load_tune_config
    from .workflows import tune

    tune.run(
        load_tune_config(
            preset=preset,
            config_path=config,
            dataset=dataset,
            task=task,
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


def _run_simulate(
    *,
    preset: str | None,
    config: Path | None,
    dataset: str | None,
    task: str | None,
    chain: str | None,
    model: str | None,
    feature_set: str | None,
    training_profile: str | None,
    simulation_profile: str | None,
    execution: str | None,
    storage_root: Path | None,
    variant: str | None,
    study: str | None,
) -> None:
    from .config import load_simulate_config
    from .workflows import simulate

    simulate.run(
        load_simulate_config(
            preset=preset,
            config_path=config,
            dataset=dataset,
            task=task,
            chain=chain,
            model=model,
            feature_set=feature_set,
            training=training_profile,
            simulation=simulation_profile,
            execution=execution,
            storage_root=storage_root,
            variant=variant,
            study=study,
        )
    )


def _storage_root(storage_root: Path | None) -> Path:
    return storage_root or Path("outputs")


def _catalog_db(storage_root: Path | None) -> Path:
    return _storage_root(storage_root) / ".spice" / "catalog.sqlite"


def _print_sections(
    title: str,
    sections: list[tuple[str, list[tuple[str, str]]]],
) -> None:
    from .core.console import create_console_runtime

    runtime = create_console_runtime()
    try:
        with runtime.activate():
            runtime.log_sectioned_summary(title, sections)
    finally:
        runtime.close()


def _show_root_detail(root_path: Path, *, detail: str | None) -> None:
    from .state.show import describe_root, sectioned_summary

    payload = describe_root(root_path, detail=detail)
    title, sections = sectioned_summary(payload)
    _print_sections(title, sections)


def _fail(message: str) -> None:
    typer.echo(message, err=True)
    raise typer.Exit(code=1)


def _dataset_list_sections(records) -> list[tuple[str, list[tuple[str, str]]]]:
    return [
        (
            "datasets",
            [
                (
                    record.dataset_name,
                    (
                        f"chain={record.chain_name} "
                        f"provider={record.provider_name} "
                        f"id={record.dataset_id}"
                    ),
                )
                for record in records
            ],
        )
    ]


def _study_list_sections(records) -> list[tuple[str, list[tuple[str, str]]]]:
    return [
        (
            "studies",
            [
                (
                    record.study_name,
                    (
                        f"chain={record.chain_name} "
                        f"dataset={record.dataset_name} "
                        f"feature_set={record.feature_set_id} "
                        f"model={record.model_id} "
                        f"task={record.task_id} "
                        f"id={record.study_id}"
                    ),
                )
                for record in records
            ],
        )
    ]


def _artifact_list_sections(records) -> list[tuple[str, list[tuple[str, str]]]]:
    return [
        (
            "artifacts",
            [
                (
                    record.artifact_id,
                    (
                        f"chain={record.chain_name} "
                        f"dataset={record.dataset_name} "
                        f"feature_set={record.feature_set_id} "
                        f"model={record.model_id} "
                        f"task={record.task_id} "
                        f"variant={record.variant}"
                        + (
                            ""
                            if record.study_name is None
                            else f" study={record.study_name}"
                        )
                    ),
                )
                for record in records
            ],
        )
    ]


def _show_records(
    *,
    kind: str,
    records,
    has_filters: bool,
    detail: str | None,
    list_sections,
) -> None:
    if not records:
        _fail(f"No {kind} matches found")
    if detail is not None and len(records) != 1:
        _print_sections(f"{kind} matches", list_sections(records))
        _fail(f"--detail requires exactly one {kind} match")
    if detail is not None:
        _show_root_detail(records[0].root_path, detail=detail)
        return
    if not has_filters or len(records) != 1:
        _print_sections(f"{kind} list", list_sections(records))
        return
    _show_root_detail(records[0].root_path, detail=None)


def _resolve_one(
    *,
    kind: str,
    records,
    list_sections,
) -> object:
    if len(records) == 1:
        return records[0]
    if records:
        _print_sections(f"{kind} matches", list_sections(records))
        _fail(f"Expected exactly one {kind} match")
    _fail(f"No {kind} matches found")


def _delete_artifact_record(storage_root: Path, record) -> None:
    from .core.files import prune_empty_directories, remove_path
    from .state.catalog import delete_artifact_record

    remove_path(record.root_path)
    delete_artifact_record(_catalog_db(storage_root), artifact_id=record.artifact_id)
    prune_empty_directories(record.root_path.parent, stop_at=storage_root / "models")


def _delete_study_record(storage_root: Path, record) -> None:
    from .core.files import prune_empty_directories, remove_path
    from .state.catalog import delete_study_record

    remove_path(record.root_path)
    delete_study_record(_catalog_db(storage_root), study_id=record.study_id)
    prune_empty_directories(record.root_path.parent, stop_at=storage_root / "studies")


def _delete_dataset_record(storage_root: Path, record) -> None:
    from .core.files import prune_empty_directories, remove_path
    from .state.catalog import delete_dataset_record

    remove_path(record.root_path)
    delete_dataset_record(_catalog_db(storage_root), dataset_id=record.dataset_id)
    prune_empty_directories(record.root_path.parent, stop_at=storage_root / "datasets")


@show_app.command(
    "dataset",
    short_help="Show datasets.",
    help="List datasets or show one dataset in detail.",
)
def show_dataset_command(
    chain: Annotated[
        str | None,
        typer.Option("--chain", metavar="CHAIN", help="Filter by chain."),
    ] = None,
    dataset: Annotated[
        str | None,
        typer.Option("--dataset", metavar="DATASET", help="Filter by dataset name."),
    ] = None,
    storage_root: Annotated[
        Path | None,
        typer.Option("--storage-root", metavar="PATH", help="Read from a non-default output root."),
    ] = None,
    detail: Annotated[
        str | None,
        typer.Option("--detail", metavar="DETAIL", help="Show one detail table: runs."),
    ] = None,
) -> None:
    from .state.catalog import list_dataset_records

    records = list_dataset_records(
        _catalog_db(storage_root),
        chain_name=chain,
        dataset_name=dataset,
    )
    _show_records(
        kind="dataset",
        records=records,
        has_filters=chain is not None or dataset is not None,
        detail=detail,
        list_sections=_dataset_list_sections,
    )


@show_app.command(
    "study",
    short_help="Show studies.",
    help="List studies or show one study in detail.",
)
def show_study_command(
    chain: Annotated[
        str | None,
        typer.Option("--chain", metavar="CHAIN", help="Filter by chain."),
    ] = None,
    dataset: Annotated[
        str | None,
        typer.Option("--dataset", metavar="DATASET", help="Filter by dataset name."),
    ] = None,
    feature_set: Annotated[
        str | None,
        typer.Option("--feature-set", metavar="FEATURE_SET", help="Filter by feature set."),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", metavar="MODEL", help="Filter by model."),
    ] = None,
    task: Annotated[
        str | None,
        typer.Option("--task", metavar="TASK", help="Filter by task."),
    ] = None,
    study: Annotated[
        str | None,
        typer.Option("--study", metavar="STUDY", help="Filter by study name."),
    ] = None,
    storage_root: Annotated[
        Path | None,
        typer.Option("--storage-root", metavar="PATH", help="Read from a non-default output root."),
    ] = None,
    detail: Annotated[
        str | None,
        typer.Option("--detail", metavar="DETAIL", help="Show one detail table: trials or config."),
    ] = None,
) -> None:
    from .state.catalog import list_study_records

    records = list_study_records(
        _catalog_db(storage_root),
        chain_name=chain,
        dataset_name=dataset,
        feature_set_id=feature_set,
        model_id=model,
        task_id=task,
        study_name=study,
    )
    _show_records(
        kind="study",
        records=records,
        has_filters=any(
            value is not None
            for value in (chain, dataset, feature_set, model, task, study)
        ),
        detail=detail,
        list_sections=_study_list_sections,
    )


@show_app.command(
    "artifact",
    short_help="Show artifacts.",
    help="List artifacts or show one artifact in detail.",
)
def show_artifact_command(
    chain: Annotated[
        str | None,
        typer.Option("--chain", metavar="CHAIN", help="Filter by chain."),
    ] = None,
    dataset: Annotated[
        str | None,
        typer.Option("--dataset", metavar="DATASET", help="Filter by dataset name."),
    ] = None,
    feature_set: Annotated[
        str | None,
        typer.Option("--feature-set", metavar="FEATURE_SET", help="Filter by feature set."),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", metavar="MODEL", help="Filter by model."),
    ] = None,
    task: Annotated[
        str | None,
        typer.Option("--task", metavar="TASK", help="Filter by task."),
    ] = None,
    variant: Annotated[
        str | None,
        typer.Option("--variant", metavar="VARIANT", help="Filter by artifact variant."),
    ] = None,
    study: Annotated[
        str | None,
        typer.Option("--study", metavar="STUDY", help="Filter by study name."),
    ] = None,
    storage_root: Annotated[
        Path | None,
        typer.Option("--storage-root", metavar="PATH", help="Read from a non-default output root."),
    ] = None,
    detail: Annotated[
        str | None,
        typer.Option("--detail", metavar="DETAIL", help="Show one detail table: epochs or runs."),
    ] = None,
) -> None:
    from .state.catalog import list_artifact_records

    records = list_artifact_records(
        _catalog_db(storage_root),
        chain_name=chain,
        dataset_name=dataset,
        feature_set_id=feature_set,
        model_id=model,
        task_id=task,
        variant=variant,
        study_name=study,
    )
    _show_records(
        kind="artifact",
        records=records,
        has_filters=any(
            value is not None
            for value in (chain, dataset, feature_set, model, task, variant, study)
        ),
        detail=detail,
        list_sections=_artifact_list_sections,
    )


@delete_app.command(
    "artifact",
    short_help="Delete one artifact.",
    help="Delete exactly one artifact.",
)
def delete_artifact_command(
    chain: Annotated[
        str | None,
        typer.Option("--chain", metavar="CHAIN", help="Filter by chain."),
    ] = None,
    dataset: Annotated[
        str | None,
        typer.Option("--dataset", metavar="DATASET", help="Filter by dataset name."),
    ] = None,
    feature_set: Annotated[
        str | None,
        typer.Option("--feature-set", metavar="FEATURE_SET", help="Filter by feature set."),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", metavar="MODEL", help="Filter by model."),
    ] = None,
    task: Annotated[
        str | None,
        typer.Option("--task", metavar="TASK", help="Filter by task."),
    ] = None,
    variant: Annotated[
        str | None,
        typer.Option("--variant", metavar="VARIANT", help="Filter by artifact variant."),
    ] = None,
    study: Annotated[
        str | None,
        typer.Option("--study", metavar="STUDY", help="Filter by study name."),
    ] = None,
    storage_root: Annotated[
        Path | None,
        typer.Option(
            "--storage-root",
            metavar="PATH",
            help="Delete from a non-default output root.",
        ),
    ] = None,
) -> None:
    from .state.catalog import list_artifact_records

    root = _storage_root(storage_root)
    record = _resolve_one(
        kind="artifact",
        records=list_artifact_records(
            _catalog_db(root),
            chain_name=chain,
            dataset_name=dataset,
            feature_set_id=feature_set,
            model_id=model,
            task_id=task,
            variant=variant,
            study_name=study,
        ),
        list_sections=_artifact_list_sections,
    )
    _delete_artifact_record(root, record)


@delete_app.command(
    "study",
    short_help="Delete one study.",
    help=(
        "Delete exactly one study. "
        "Use --cascade to also delete dependent tuned artifacts."
    ),
)
def delete_study_command(
    chain: Annotated[
        str | None,
        typer.Option("--chain", metavar="CHAIN", help="Filter by chain."),
    ] = None,
    dataset: Annotated[
        str | None,
        typer.Option("--dataset", metavar="DATASET", help="Filter by dataset name."),
    ] = None,
    feature_set: Annotated[
        str | None,
        typer.Option("--feature-set", metavar="FEATURE_SET", help="Filter by feature set."),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", metavar="MODEL", help="Filter by model."),
    ] = None,
    task: Annotated[
        str | None,
        typer.Option("--task", metavar="TASK", help="Filter by task."),
    ] = None,
    study: Annotated[
        str | None,
        typer.Option("--study", metavar="STUDY", help="Filter by study name."),
    ] = None,
    storage_root: Annotated[
        Path | None,
        typer.Option(
            "--storage-root",
            metavar="PATH",
            help="Delete from a non-default output root.",
        ),
    ] = None,
    cascade: Annotated[
        bool,
        typer.Option("--cascade", help="Also delete dependent tuned artifacts."),
    ] = False,
) -> None:
    from .state.catalog import list_artifacts_for_study, list_study_records

    root = _storage_root(storage_root)
    record = _resolve_one(
        kind="study",
        records=list_study_records(
            _catalog_db(root),
            chain_name=chain,
            dataset_name=dataset,
            feature_set_id=feature_set,
            model_id=model,
            task_id=task,
            study_name=study,
        ),
        list_sections=_study_list_sections,
    )
    dependent_artifacts = list_artifacts_for_study(_catalog_db(root), study_id=record.study_id)
    if dependent_artifacts and not cascade:
        _print_sections("artifact matches", _artifact_list_sections(dependent_artifacts))
        _fail("Study has dependent artifacts. Re-run with --cascade.")
    for artifact_record in dependent_artifacts:
        _delete_artifact_record(root, artifact_record)
    _delete_study_record(root, record)


@delete_app.command(
    "dataset",
    short_help="Delete one dataset.",
    help=(
        "Delete exactly one dataset. "
        "Use --cascade to also delete dependent studies and artifacts."
    ),
)
def delete_dataset_command(
    chain: Annotated[
        str | None,
        typer.Option("--chain", metavar="CHAIN", help="Filter by chain."),
    ] = None,
    dataset: Annotated[
        str | None,
        typer.Option("--dataset", metavar="DATASET", help="Filter by dataset name."),
    ] = None,
    storage_root: Annotated[
        Path | None,
        typer.Option(
            "--storage-root",
            metavar="PATH",
            help="Delete from a non-default output root.",
        ),
    ] = None,
    cascade: Annotated[
        bool,
        typer.Option("--cascade", help="Also delete dependent studies and artifacts."),
    ] = False,
) -> None:
    from .state.catalog import (
        list_artifacts_for_dataset,
        list_dataset_records,
        list_studies_for_dataset,
    )

    root = _storage_root(storage_root)
    record = _resolve_one(
        kind="dataset",
        records=list_dataset_records(
            _catalog_db(root),
            chain_name=chain,
            dataset_name=dataset,
        ),
        list_sections=_dataset_list_sections,
    )
    dependent_artifacts = list_artifacts_for_dataset(
        _catalog_db(root),
        dataset_id=record.dataset_id,
    )
    dependent_studies = list_studies_for_dataset(
        _catalog_db(root),
        dataset_id=record.dataset_id,
    )
    if (dependent_artifacts or dependent_studies) and not cascade:
        if dependent_artifacts:
            _print_sections("artifact matches", _artifact_list_sections(dependent_artifacts))
        if dependent_studies:
            _print_sections("study matches", _study_list_sections(dependent_studies))
        _fail("Dataset has dependent studies or artifacts. Re-run with --cascade.")
    for artifact_record in dependent_artifacts:
        _delete_artifact_record(root, artifact_record)
    for study_record in dependent_studies:
        _delete_study_record(root, study_record)
    _delete_dataset_record(root, record)


def _print_config_names(names: list[str]) -> None:
    for name in names:
        typer.echo(name)


@config_app.command(
    "list",
    short_help="List saved config specs.",
    help="List saved config names for one authorable group.",
)
def config_list_command(
    group: Annotated[
        ConfigGroup,
        typer.Argument(metavar="GROUP", help=_CONFIG_GROUP_HELP),
    ],
) -> None:
    from .config.registry import list_group_names

    _print_config_names(list_group_names(group.value))


@config_app.command(
    "show",
    short_help="Show one saved config spec.",
    help="Print one saved config spec as canonical YAML.",
)
def config_show_command(
    group: Annotated[
        ConfigGroup,
        typer.Argument(metavar="GROUP", help=_CONFIG_GROUP_HELP),
    ],
    name: Annotated[
        str,
        typer.Argument(metavar="NAME", help="Saved spec name."),
    ],
) -> None:
    from .config.registry import show_named_group

    try:
        typer.echo(show_named_group(group.value, name), nl=False)
    except (FileNotFoundError, TypeError, ValueError) as exc:
        _fail(str(exc))


@config_app.command(
    "create",
    short_help="Create one saved config spec.",
    help="Create one saved config spec with repeated --set path=value operations.",
)
def config_create_command(
    group: Annotated[
        ConfigGroup,
        typer.Argument(metavar="GROUP", help=_CONFIG_GROUP_HELP),
    ],
    name: Annotated[
        str,
        typer.Argument(metavar="NAME", help="Saved spec name."),
    ],
    set_values: Annotated[
        list[str] | None,
        typer.Option(
            "--set",
            metavar="PATH=VALUE",
            help="Set one YAML path using dot notation.",
        ),
    ] = None,
) -> None:
    from .config.registry import create_named_group

    try:
        create_named_group(
            group_token=group.value,
            name=name,
            set_values=list(set_values or []),
        )
    except (FileExistsError, FileNotFoundError, TypeError, ValueError) as exc:
        _fail(str(exc))
    typer.echo(f"created {group.value} {name}")


@config_app.command(
    "update",
    short_help="Update one saved config spec.",
    help="Update one saved config spec with repeated --set and --unset operations.",
)
def config_update_command(
    group: Annotated[
        ConfigGroup,
        typer.Argument(metavar="GROUP", help=_CONFIG_GROUP_HELP),
    ],
    name: Annotated[
        str,
        typer.Argument(metavar="NAME", help="Saved spec name."),
    ],
    set_values: Annotated[
        list[str] | None,
        typer.Option(
            "--set",
            metavar="PATH=VALUE",
            help="Set one YAML path using dot notation.",
        ),
    ] = None,
    unset_paths: Annotated[
        list[str] | None,
        typer.Option(
            "--unset",
            metavar="PATH",
            help="Remove one YAML path using dot notation.",
        ),
    ] = None,
) -> None:
    from .config.registry import update_named_group

    try:
        update_named_group(
            group_token=group.value,
            name=name,
            set_values=list(set_values or []),
            unset_paths=list(unset_paths or []),
        )
    except (FileNotFoundError, TypeError, ValueError) as exc:
        _fail(str(exc))
    typer.echo(f"updated {group.value} {name}")


@config_app.command(
    "delete",
    short_help="Delete one saved config spec.",
    help="Delete one saved config spec. Blocks on dependents unless --force is used.",
)
def config_delete_command(
    group: Annotated[
        ConfigGroup,
        typer.Argument(metavar="GROUP", help=_CONFIG_GROUP_HELP),
    ],
    name: Annotated[
        str,
        typer.Argument(metavar="NAME", help="Saved spec name."),
    ],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Delete even if dependent saved specs exist.",
        ),
    ] = False,
) -> None:
    from .config.registry import delete_named_group

    try:
        delete_named_group(group_token=group.value, name=name, force=force)
    except (FileNotFoundError, TypeError, ValueError) as exc:
        _fail(str(exc))
    typer.echo(f"deleted {group.value} {name}")


@app.command(
    "acquire",
    short_help="Acquire canonical datasets.",
    help="Acquire canonical history and evaluation block datasets.",
    epilog=(
        "Example:\n"
        "  spice acquire --preset icdcs_2026 --chain avalanche --provider publicnode"
    ),
)
def acquire_command(
    preset: Annotated[
        str | None,
        typer.Option(
            "--preset",
            metavar="PRESET",
            help="Apply a named preset before config-file and CLI overrides.",
            rich_help_panel="Selection",
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            metavar="PATH",
            help="Overlay a YAML config file on top of the selected preset.",
            rich_help_panel="Overrides",
        ),
    ] = None,
    dataset: Annotated[
        str | None,
        typer.Option(
            "--dataset",
            metavar="DATASET",
            help="Use a named dataset spec.",
            rich_help_panel="Selection",
        ),
    ] = None,
    task: Annotated[
        str | None,
        typer.Option(
            "--task",
            metavar="TASK",
            help="Use a named task profile.",
            rich_help_panel="Selection",
        ),
    ] = None,
    chain: Annotated[
        str | None,
        typer.Option(
            "--chain",
            metavar="CHAIN",
            help="Override the target chain.",
            rich_help_panel="Selection",
        ),
    ] = None,
    provider: Annotated[
        str | None,
        typer.Option(
            "--provider",
            metavar="PROVIDER",
            help="Override the RPC provider.",
            rich_help_panel="Selection",
        ),
    ] = None,
    feature_set: Annotated[
        str | None,
        typer.Option(
            "--feature-set",
            metavar="FEATURE_SET",
            help="Use a named feature set profile for acquisition planning.",
            rich_help_panel="Selection",
        ),
    ] = None,
    acquisition_profile: Annotated[
        str | None,
        typer.Option(
            "--acquisition",
            metavar="PROFILE",
            help="Use a named acquisition profile.",
            rich_help_panel="Profiles",
        ),
    ] = None,
    storage_root: Annotated[
        Path | None,
        typer.Option(
            "--storage-root",
            metavar="PATH",
            help="Write datasets under a non-default output root.",
            rich_help_panel="Outputs",
        ),
    ] = None,
    dry_run: Annotated[
        bool | None,
        typer.Option(
            "--dry-run/--no-dry-run",
            help="Plan the acquisition and print windows without writing outputs.",
            rich_help_panel="Execution",
        ),
    ] = None,
) -> None:
    _run_acquire(
        preset=preset,
        config=config,
        dataset=dataset,
        task=task,
        chain=chain,
        provider=provider,
        feature_set=feature_set,
        acquisition_profile=acquisition_profile,
        storage_root=storage_root,
        dry_run=dry_run,
    )


@app.command(
    "train",
    short_help="Train a model artifact.",
    help="Train a model artifact from a canonical history dataset.",
    epilog="Example:\n  spice train --preset icdcs_2026 --variant tuned",
)
def train_command(
    preset: Annotated[
        str | None,
        typer.Option(
            "--preset",
            metavar="PRESET",
            help="Apply a named preset before config-file and CLI overrides.",
            rich_help_panel="Selection",
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            metavar="PATH",
            help="Overlay a YAML config file on top of the selected preset.",
            rich_help_panel="Overrides",
        ),
    ] = None,
    dataset: Annotated[
        str | None,
        typer.Option(
            "--dataset",
            metavar="DATASET",
            help="Use a named dataset spec.",
            rich_help_panel="Selection",
        ),
    ] = None,
    task: Annotated[
        str | None,
        typer.Option(
            "--task",
            metavar="TASK",
            help="Use a named task profile.",
            rich_help_panel="Selection",
        ),
    ] = None,
    chain: Annotated[
        str | None,
        typer.Option(
            "--chain",
            metavar="CHAIN",
            help="Override the target chain.",
            rich_help_panel="Selection",
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            metavar="MODEL",
            help="Use a named model spec.",
            rich_help_panel="Selection",
        ),
    ] = None,
    feature_set: Annotated[
        str | None,
        typer.Option(
            "--feature-set",
            metavar="FEATURE_SET",
            help="Use a named feature-set spec.",
            rich_help_panel="Selection",
        ),
    ] = None,
    training_profile: Annotated[
        str | None,
        typer.Option(
            "--training",
            metavar="PROFILE",
            help="Use a named training profile.",
            rich_help_panel="Profiles",
        ),
    ] = None,
    split: Annotated[
        str | None,
        typer.Option(
            "--split",
            metavar="SPLIT",
            help="Use a named train/validation/test split profile.",
            rich_help_panel="Profiles",
        ),
    ] = None,
    storage_root: Annotated[
        Path | None,
        typer.Option(
            "--storage-root",
            metavar="PATH",
            help="Write artifacts under a non-default output root.",
            rich_help_panel="Outputs",
        ),
    ] = None,
    variant: Annotated[
        str | None,
        typer.Option(
            "--variant",
            metavar="VARIANT",
            help="Select the artifact variant, such as baseline or tuned.",
            rich_help_panel="Execution",
        ),
    ] = None,
    study: Annotated[
        str | None,
        typer.Option(
            "--study",
            metavar="STUDY",
            help="Override the study name used for tuned artifacts.",
            rich_help_panel="Execution",
        ),
    ] = None,
) -> None:
    _run_train(
        preset=preset,
        config=config,
        dataset=dataset,
        task=task,
        chain=chain,
        model=model,
        feature_set=feature_set,
        training_profile=training_profile,
        split=split,
        storage_root=storage_root,
        variant=variant,
        study=study,
    )


@app.command(
    "tune",
    short_help="Tune model hyperparameters.",
    help="Run Optuna tuning for a model and write study state.",
    epilog="Example:\n  spice tune --preset icdcs_2026 --trial-count 20",
)
def tune_command(
    preset: Annotated[
        str | None,
        typer.Option(
            "--preset",
            metavar="PRESET",
            help="Apply a named preset before config-file and CLI overrides.",
            rich_help_panel="Selection",
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            metavar="PATH",
            help="Overlay a YAML config file on top of the selected preset.",
            rich_help_panel="Overrides",
        ),
    ] = None,
    dataset: Annotated[
        str | None,
        typer.Option(
            "--dataset",
            metavar="DATASET",
            help="Use a named dataset spec.",
            rich_help_panel="Selection",
        ),
    ] = None,
    task: Annotated[
        str | None,
        typer.Option(
            "--task",
            metavar="TASK",
            help="Use a named task profile.",
            rich_help_panel="Selection",
        ),
    ] = None,
    chain: Annotated[
        str | None,
        typer.Option(
            "--chain",
            metavar="CHAIN",
            help="Override the target chain.",
            rich_help_panel="Selection",
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            metavar="MODEL",
            help="Use a named model spec.",
            rich_help_panel="Selection",
        ),
    ] = None,
    feature_set: Annotated[
        str | None,
        typer.Option(
            "--feature-set",
            metavar="FEATURE_SET",
            help="Use a named feature-set spec.",
            rich_help_panel="Selection",
        ),
    ] = None,
    training_profile: Annotated[
        str | None,
        typer.Option(
            "--training",
            metavar="PROFILE",
            help="Use a named training profile.",
            rich_help_panel="Profiles",
        ),
    ] = None,
    split: Annotated[
        str | None,
        typer.Option(
            "--split",
            metavar="SPLIT",
            help="Use a named train/validation/test split profile.",
            rich_help_panel="Profiles",
        ),
    ] = None,
    tuning_profile: Annotated[
        str | None,
        typer.Option(
            "--tuning",
            metavar="PROFILE",
            help="Use a named tuning profile.",
            rich_help_panel="Profiles",
        ),
    ] = None,
    tuning_space: Annotated[
        str | None,
        typer.Option(
            "--tuning-space",
            metavar="SPACE",
            help="Use a named tuning search space.",
            rich_help_panel="Profiles",
        ),
    ] = None,
    storage_root: Annotated[
        Path | None,
        typer.Option(
            "--storage-root",
            metavar="PATH",
            help="Write tuning outputs under a non-default output root.",
            rich_help_panel="Outputs",
        ),
    ] = None,
    study: Annotated[
        str | None,
        typer.Option(
            "--study",
            metavar="STUDY",
            help="Override the study name.",
            rich_help_panel="Execution",
        ),
    ] = None,
    trial_count: Annotated[
        int | None,
        typer.Option(
            "--trial-count",
            metavar="COUNT",
            min=1,
            help="Override the number of Optuna trials.",
            rich_help_panel="Execution",
        ),
    ] = None,
) -> None:
    _run_tune(
        preset=preset,
        config=config,
        dataset=dataset,
        task=task,
        chain=chain,
        model=model,
        feature_set=feature_set,
        training_profile=training_profile,
        split=split,
        tuning_profile=tuning_profile,
        tuning_space=tuning_space,
        storage_root=storage_root,
        study=study,
        trial_count=trial_count,
    )


@app.command(
    "simulate",
    short_help="Run evaluation-day simulation.",
    help="Run evaluation-day simulation from a trained artifact.",
    epilog="Example:\n  spice simulate --preset icdcs_2026 --variant tuned",
)
def simulate_command(
    preset: Annotated[
        str | None,
        typer.Option(
            "--preset",
            metavar="PRESET",
            help="Apply a named preset before config-file and CLI overrides.",
            rich_help_panel="Selection",
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            metavar="PATH",
            help="Overlay a YAML config file on top of the selected preset.",
            rich_help_panel="Overrides",
        ),
    ] = None,
    dataset: Annotated[
        str | None,
        typer.Option(
            "--dataset",
            metavar="DATASET",
            help="Use a named dataset spec.",
            rich_help_panel="Selection",
        ),
    ] = None,
    task: Annotated[
        str | None,
        typer.Option(
            "--task",
            metavar="TASK",
            help="Use a named task profile.",
            rich_help_panel="Selection",
        ),
    ] = None,
    chain: Annotated[
        str | None,
        typer.Option(
            "--chain",
            metavar="CHAIN",
            help="Override the target chain.",
            rich_help_panel="Selection",
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            metavar="MODEL",
            help="Use a named model spec.",
            rich_help_panel="Selection",
        ),
    ] = None,
    feature_set: Annotated[
        str | None,
        typer.Option(
            "--feature-set",
            metavar="FEATURE_SET",
            help="Use a named feature-set spec.",
            rich_help_panel="Selection",
        ),
    ] = None,
    training_profile: Annotated[
        str | None,
        typer.Option(
            "--training",
            metavar="PROFILE",
            help="Use a named training profile.",
            rich_help_panel="Profiles",
        ),
    ] = None,
    simulation_profile: Annotated[
        str | None,
        typer.Option(
            "--simulation",
            metavar="PROFILE",
            help="Use a named simulation profile.",
            rich_help_panel="Profiles",
        ),
    ] = None,
    execution: Annotated[
        str | None,
        typer.Option(
            "--execution",
            metavar="EXECUTION",
            help="Use a named execution request profile.",
            rich_help_panel="Selection",
        ),
    ] = None,
    storage_root: Annotated[
        Path | None,
        typer.Option(
            "--storage-root",
            metavar="PATH",
            help="Write reports under a non-default output root.",
            rich_help_panel="Outputs",
        ),
    ] = None,
    variant: Annotated[
        str | None,
        typer.Option(
            "--variant",
            metavar="VARIANT",
            help="Select the artifact variant, such as baseline or tuned.",
            rich_help_panel="Execution",
        ),
    ] = None,
    study: Annotated[
        str | None,
        typer.Option(
            "--study",
            metavar="STUDY",
            help="Override the study name used for tuned artifacts.",
            rich_help_panel="Execution",
        ),
    ] = None,
) -> None:
    _run_simulate(
        preset=preset,
        config=config,
        dataset=dataset,
        task=task,
        chain=chain,
        model=model,
        feature_set=feature_set,
        training_profile=training_profile,
        simulation_profile=simulation_profile,
        execution=execution,
        storage_root=storage_root,
        variant=variant,
        study=study,
    )


def main(argv: list[str] | None = None) -> None:
    app(prog_name="spice", args=argv)
