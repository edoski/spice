"""Human-readable CLI reporting."""

from __future__ import annotations

import logging
import shlex
import sys
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from io import TextIOBase
from pathlib import Path

RenderableValue = str | int | float | Path


@dataclass(slots=True)
class _LoggerState:
    level: int
    handlers: list[logging.Handler]
    propagate: bool


class _ReporterLogHandler(logging.Handler):
    def __init__(self, reporter: Reporter) -> None:
        super().__init__(level=logging.WARNING)
        self._reporter = reporter

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)
        level = "error" if record.levelno >= logging.ERROR else "warning"
        self._reporter.milestone(message, level=level)


class Reporter:
    """One concrete stdout reporter for human-facing CLI output."""

    def __init__(self, *, stream: TextIOBase | None = None) -> None:
        self._stream = stream or sys.stdout
        self._activation_depth = 0
        self._root_state: _LoggerState | None = None
        self._pywarnings_state: _LoggerState | None = None
        self._handler: _ReporterLogHandler | None = None

    @contextmanager
    def activate(self) -> Iterator[Reporter]:
        first_entry = self._activation_depth == 0
        self._activation_depth += 1
        if first_entry:
            self._install_logging_bridge()
        try:
            yield self
        finally:
            self._activation_depth -= 1
            if first_entry and self._activation_depth == 0:
                self._restore_logging_bridge()

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

    def close(self) -> None:
        if self._activation_depth > 0:
            self._activation_depth = 0
            self._restore_logging_bridge()

    def _emit(self, line: str) -> None:
        print(line, file=self._stream)
        self._stream.flush()

    def _install_logging_bridge(self) -> None:
        root_logger = logging.getLogger()
        self._root_state = _LoggerState(
            level=root_logger.level,
            handlers=list(root_logger.handlers),
            propagate=root_logger.propagate,
        )
        self._handler = _ReporterLogHandler(self)
        root_logger.addHandler(self._handler)
        root_logger.setLevel(min(root_logger.level, logging.WARNING))
        root_logger.propagate = False

        pywarnings_logger = logging.getLogger("py.warnings")
        self._pywarnings_state = _LoggerState(
            level=pywarnings_logger.level,
            handlers=list(pywarnings_logger.handlers),
            propagate=pywarnings_logger.propagate,
        )
        pywarnings_logger.setLevel(logging.WARNING)
        pywarnings_logger.propagate = True
        logging.captureWarnings(True)

    def _restore_logging_bridge(self) -> None:
        logging.captureWarnings(False)

        if self._pywarnings_state is not None:
            pywarnings_logger = logging.getLogger("py.warnings")
            pywarnings_logger.handlers.clear()
            for handler in self._pywarnings_state.handlers:
                pywarnings_logger.addHandler(handler)
            pywarnings_logger.setLevel(self._pywarnings_state.level)
            pywarnings_logger.propagate = self._pywarnings_state.propagate
            self._pywarnings_state = None

        if self._root_state is not None:
            root_logger = logging.getLogger()
            if self._handler is not None:
                root_logger.removeHandler(self._handler)
            root_logger.setLevel(self._root_state.level)
            root_logger.handlers.clear()
            for handler in self._root_state.handlers:
                root_logger.addHandler(handler)
            root_logger.propagate = self._root_state.propagate
            self._root_state = None
        self._handler = None


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
