"""Shared workflow helpers."""

from __future__ import annotations

import signal
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from ..core.reporting import Reporter
from ..core.runtime import ConsoleRuntime, create_console_runtime


@dataclass(slots=True)
class WorkflowSession:
    runtime: ConsoleRuntime
    reporter: Reporter


@dataclass(slots=True)
class _InterruptState:
    interrupted: bool = False


@contextmanager
def _capture_sigint() -> Iterator[_InterruptState]:
    state = _InterruptState()
    if not hasattr(signal, "SIGINT"):
        yield state
        return
    previous_handler = signal.getsignal(signal.SIGINT)

    def _handle_sigint(signum, frame) -> None:
        state.interrupted = True
        if previous_handler == signal.SIG_IGN:
            return
        if previous_handler == signal.SIG_DFL:
            signal.default_int_handler(signum, frame)
            return
        if callable(previous_handler):
            previous_handler(signum, frame)

    try:
        signal.signal(signal.SIGINT, _handle_sigint)
    except ValueError:
        yield state
        return
    try:
        yield state
    finally:
        try:
            signal.signal(signal.SIGINT, previous_handler)
        except ValueError:
            pass


def _cleanup_after_interrupt(
    reporter: Reporter,
    *,
    label: str,
    cleanup: Callable[[], None],
) -> None:
    cleanup()
    reporter.close()
    reporter.log(f"{label} cancelled; partial outputs removed", level="warning")


@contextmanager
def abort_cleanup(
    reporter: Reporter,
    *,
    label: str,
    cleanup: Callable[[], None],
) -> Iterator[None]:
    with _capture_sigint() as interrupt_state:
        try:
            yield
        except BaseException as exc:
            if interrupt_state.interrupted or isinstance(exc, KeyboardInterrupt):
                _cleanup_after_interrupt(reporter, label=label, cleanup=cleanup)
            raise
        if interrupt_state.interrupted:
            _cleanup_after_interrupt(reporter, label=label, cleanup=cleanup)
            raise KeyboardInterrupt


@contextmanager
def managed_workflow(
    config: object,
    *,
    run_name: str,
    runtime: ConsoleRuntime | None = None,
    reporter: Reporter | None = None,
    default_runtime_factory: Callable[..., ConsoleRuntime] = create_console_runtime,
    nested: bool = False,
) -> Iterator[WorkflowSession]:
    del config, run_name, nested
    active_runtime = runtime or default_runtime_factory(reporter=reporter)
    owns_runtime = runtime is None
    try:
        with active_runtime.activate():
            yield WorkflowSession(
                runtime=active_runtime,
                reporter=active_runtime.reporter,
            )
    finally:
        if owns_runtime:
            active_runtime.close()
