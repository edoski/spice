"""CLI adapter for operator-facing project errors."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

import click
import typer

from ..core.errors import SpiceOperatorError

CommandT = TypeVar("CommandT", bound=Callable[..., object])


def adapt_operator_errors(command: CommandT) -> CommandT:
    @wraps(command)
    def wrapper(*args: object, **kwargs: object) -> object:
        try:
            return command(*args, **kwargs)
        except SpiceOperatorError as exc:
            raise click.ClickException(str(exc)) from exc

    return cast(CommandT, wrapper)


class OperatorTyper(typer.Typer):
    def command(self, *args: Any, **kwargs: Any) -> Callable[[CommandT], CommandT]:
        register = super().command(*args, **kwargs)

        def decorator(command: CommandT) -> CommandT:
            register(adapt_operator_errors(command))
            return command

        return decorator
