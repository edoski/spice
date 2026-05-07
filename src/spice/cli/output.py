"""CLI-owned plain text and JSON output helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

import typer

from ..core.rendering import key_value_line
from ..core.reporting import Reporter

SectionRows = Sequence[tuple[str, list[tuple[str, str]]]]


def echo_json(payload: Mapping[str, object]) -> None:
    typer.echo(json.dumps(payload, sort_keys=True))


def echo_key_value(label: str, fields: Sequence[tuple[str, str]]) -> None:
    typer.echo(key_value_line(label, fields))


def echo_warning(message: str) -> None:
    typer.echo(f"warning: {message}", err=True)


def echo_sections(title: str, sections: SectionRows, *, err: bool = False) -> None:
    reporter = Reporter()
    if err:
        reporter.diagnostic_sections(title, list(sections))
        return
    reporter.sections(title, list(sections))
