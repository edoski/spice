from __future__ import annotations

import signal

import pytest

from spice.workflows._shared import abort_cleanup


class _Recorder:
    def __init__(self) -> None:
        self.closed = False
        self.logs: list[tuple[str, str]] = []

    def close(self) -> None:
        self.closed = True

    def log(self, message: str, *, level: str = "info") -> None:
        self.logs.append((level, message))


def test_abort_cleanup_cleans_up_when_keyboard_interrupt_bubbles() -> None:
    reporter = _Recorder()
    cleaned: list[str] = []

    with pytest.raises(KeyboardInterrupt):
        with abort_cleanup(
            reporter,
            label="train",
            cleanup=lambda: cleaned.append("done"),
        ):
            raise KeyboardInterrupt

    assert cleaned == ["done"]
    assert reporter.closed is True
    assert reporter.logs == [("warning", "train cancelled; partial outputs removed")]


def test_abort_cleanup_cleans_up_when_interrupt_is_swallowed_inside_body() -> None:
    reporter = _Recorder()
    cleaned: list[str] = []

    with pytest.raises(KeyboardInterrupt):
        with abort_cleanup(
            reporter,
            label="tune",
            cleanup=lambda: cleaned.append("done"),
        ):
            handler = signal.getsignal(signal.SIGINT)
            assert callable(handler)
            try:
                handler(signal.SIGINT, None)
            except KeyboardInterrupt:
                pass

    assert cleaned == ["done"]
    assert reporter.closed is True
    assert reporter.logs == [("warning", "tune cancelled; partial outputs removed")]


def test_abort_cleanup_cleans_up_when_interrupt_turns_into_system_exit() -> None:
    reporter = _Recorder()
    cleaned: list[str] = []

    with pytest.raises(SystemExit) as exc_info:
        with abort_cleanup(
            reporter,
            label="train",
            cleanup=lambda: cleaned.append("done"),
        ):
            handler = signal.getsignal(signal.SIGINT)
            assert callable(handler)
            try:
                handler(signal.SIGINT, None)
            except KeyboardInterrupt:
                pass
            raise SystemExit(1)

    assert exc_info.value.code == 1
    assert cleaned == ["done"]
    assert reporter.closed is True
    assert reporter.logs == [("warning", "train cancelled; partial outputs removed")]
