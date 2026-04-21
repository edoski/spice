"""Human-readable CLI reporting."""

from __future__ import annotations

import shlex
import sys
from collections.abc import Iterable
from io import TextIOBase
from pathlib import Path

RenderableValue = str | int | float | Path


class Reporter:
    """One concrete stdout reporter for human-facing CLI output."""

    def __init__(self, *, stream: TextIOBase | None = None) -> None:
        self._stream = stream or sys.stdout

    def header(
        self,
        name: str,
        facts: Iterable[tuple[str, RenderableValue]] = (),
    ) -> None:
        self._emit(" ".join([name, *(_field(key, value) for key, value in facts)]).strip())

    def milestone(self, message: str, *, level: str = "info") -> None:
        prefix = ""
        if level == "warning":
            prefix = "warning: "
        elif level == "error":
            prefix = "error: "
        self._emit(f"{prefix}{message}")

    def result(
        self,
        name: str,
        fields: Iterable[tuple[str, RenderableValue]] = (),
        *,
        status: str = "complete",
    ) -> None:
        parts = [name, status]
        parts.extend(_field(key, value) for key, value in fields)
        self._emit(" ".join(parts))

    def sections(
        self,
        title: str,
        sections: Iterable[tuple[str, Iterable[tuple[str, RenderableValue]]]],
    ) -> None:
        self._emit(title)
        for section_title, rows in sections:
            self._emit(f"{section_title}:")
            for label, value in rows:
                self._emit(f"  {label}: {_stringify(value)}")

    def _emit(self, line: str) -> None:
        print(line, file=self._stream)
        self._stream.flush()


def _stringify(value: RenderableValue) -> str:
    text = str(value).replace("\n", " ").strip()
    return text


def _field(key: str, value: RenderableValue) -> str:
    rendered = _stringify(value)
    if not rendered:
        return f"{key}=''"
    if any(char.isspace() for char in rendered):
        rendered = shlex.quote(rendered)
    return f"{key}={rendered}"
