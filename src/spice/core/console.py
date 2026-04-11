"""Rich-backed logging and progress reporting."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Protocol

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


def configure_logging(console: Console) -> logging.Logger:
    logger = logging.getLogger("spice")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.addHandler(
        RichHandler(
            console=console,
            show_path=False,
            markup=False,
            rich_tracebacks=True,
            log_time_format="[%X]",
        )
    )
    logger.propagate = False
    return logger


class Reporter(Protocol):
    def log(self, message: str, *, level: str = "info") -> None: ...
    def start_pull(self, *, label: str, total_chunks: int | None) -> None: ...
    def update_pull(
        self,
        *,
        completed_chunks: int,
        total_chunks: int | None,
        latest_output: str | None = None,
    ) -> None: ...
    def finish_pull(self, *, output_dir: Path) -> None: ...
    def start_enrich(self, *, total_files: int, total_blocks: int) -> None: ...
    def update_enrich(
        self,
        *,
        completed_files: int,
        completed_blocks: int,
        total_files: int,
        total_blocks: int,
    ) -> None: ...
    def finish_enrich(self, *, output_dir: Path) -> None: ...
    def close(self) -> None: ...


class NullReporter:
    """Silent reporter used by library entrypoints."""

    def log(self, message: str, *, level: str = "info") -> None:
        return None

    def start_pull(self, *, label: str, total_chunks: int | None) -> None:
        return None

    def update_pull(
        self,
        *,
        completed_chunks: int,
        total_chunks: int | None,
        latest_output: str | None = None,
    ) -> None:
        return None

    def finish_pull(self, *, output_dir: Path) -> None:
        return None

    def start_enrich(self, *, total_files: int, total_blocks: int) -> None:
        return None

    def update_enrich(
        self,
        *,
        completed_files: int,
        completed_blocks: int,
        total_files: int,
        total_blocks: int,
    ) -> None:
        return None

    def finish_enrich(self, *, output_dir: Path) -> None:
        return None

    def close(self) -> None:
        return None


class RichReporter(NullReporter):
    """TTY-aware progress reporter for the CLI."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self.logger = configure_logging(self.console)
        self.enabled = self.console.is_terminal
        self.progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            disable=not self.enabled,
            transient=False,
        )
        self.progress.start()
        self._pull_task: TaskID | None = None
        self._enrich_files_task: TaskID | None = None
        self._enrich_blocks_task: TaskID | None = None
        self._last_pull_output_at = 0.0

    def log(self, message: str, *, level: str = "info") -> None:
        getattr(self.logger, level)(message)

    def start_pull(self, *, label: str, total_chunks: int | None) -> None:
        if self.enabled:
            self._pull_task = self.progress.add_task(
                label,
                total=total_chunks,
                start=total_chunks is None,
            )
        self.log(f"pull started: {label}")

    def update_pull(
        self,
        *,
        completed_chunks: int,
        total_chunks: int | None,
        latest_output: str | None = None,
    ) -> None:
        if self.enabled and self._pull_task is not None:
            task = self.progress.tasks[self._pull_task]
            if total_chunks is not None and completed_chunks > 0 and not task.started:
                self.progress.start_task(self._pull_task)
            self.progress.update(self._pull_task, completed=completed_chunks, total=total_chunks)
        if latest_output:
            now = time.monotonic()
            if now - self._last_pull_output_at >= 10.0:
                self.log(latest_output)
                self._last_pull_output_at = now

    def finish_pull(self, *, output_dir: Path) -> None:
        if self.enabled and self._pull_task is not None:
            task = self.progress.tasks[self._pull_task]
            task_total = task.total
            if task_total is not None:
                if not task.started:
                    self.progress.start_task(self._pull_task)
                self.progress.update(self._pull_task, completed=task_total)
        self.log(f"pull finished: {output_dir}")

    def start_enrich(self, *, total_files: int, total_blocks: int) -> None:
        if self.enabled:
            self._enrich_files_task = self.progress.add_task("enrich files", total=total_files)
            self._enrich_blocks_task = self.progress.add_task("enrich blocks", total=total_blocks)
        self.log(
            f"enrichment started: total_files={total_files} total_missing_blocks={total_blocks}"
        )

    def update_enrich(
        self,
        *,
        completed_files: int,
        completed_blocks: int,
        total_files: int,
        total_blocks: int,
    ) -> None:
        if (
            self.enabled
            and self._enrich_files_task is not None
            and self._enrich_blocks_task is not None
        ):
            self.progress.update(
                self._enrich_files_task,
                completed=completed_files,
                total=total_files,
            )
            self.progress.update(
                self._enrich_blocks_task,
                completed=completed_blocks,
                total=total_blocks,
            )

    def finish_enrich(self, *, output_dir: Path) -> None:
        if self.enabled:
            if self._enrich_files_task is not None:
                task_total = self.progress.tasks[self._enrich_files_task].total
                if task_total is not None:
                    self.progress.update(self._enrich_files_task, completed=task_total)
            if self._enrich_blocks_task is not None:
                task_total = self.progress.tasks[self._enrich_blocks_task].total
                if task_total is not None:
                    self.progress.update(self._enrich_blocks_task, completed=task_total)
        self.log(f"enrichment finished: {output_dir}")

    def close(self) -> None:
        self.progress.stop()

    def __enter__(self) -> RichReporter:
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        self.close()
