"""Config command routing."""

from __future__ import annotations

from typing import Annotated

import typer

from ...config.registry import ConfigGroup
from ..options import fail

app = typer.Typer(
    help="Author saved config specs.",
    no_args_is_help=True,
)
_CONFIG_GROUP_HELP = (
    "One of: chain, provider, dataset, problem, execution, feature-set, preset."
)


def _print_config_names(names: list[str]) -> None:
    for name in names:
        typer.echo(name)


@app.command(
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
    from ...config.registry import list_group_names

    _print_config_names(list_group_names(group.value))


@app.command(
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
    from ...config.registry import show_named_group

    try:
        typer.echo(show_named_group(group.value, name), nl=False)
    except (FileNotFoundError, TypeError, ValueError) as exc:
        fail(str(exc))


@app.command(
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
    from ...config.registry import create_named_group

    try:
        create_named_group(
            group_token=group.value,
            name=name,
            set_values=list(set_values or []),
        )
    except (FileExistsError, FileNotFoundError, TypeError, ValueError) as exc:
        fail(str(exc))
    typer.echo(f"created {group.value} {name}")


@app.command(
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
    from ...config.registry import update_named_group

    try:
        update_named_group(
            group_token=group.value,
            name=name,
            set_values=list(set_values or []),
            unset_paths=list(unset_paths or []),
        )
    except (FileNotFoundError, TypeError, ValueError) as exc:
        fail(str(exc))
    typer.echo(f"updated {group.value} {name}")


@app.command(
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
    from ...config.registry import delete_named_group

    try:
        delete_named_group(group_token=group.value, name=name, force=force)
    except (FileNotFoundError, TypeError, ValueError) as exc:
        fail(str(exc))
    typer.echo(f"deleted {group.value} {name}")
