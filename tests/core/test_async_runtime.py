from __future__ import annotations

import asyncio
import signal

import pytest

from spice.core.async_runtime import run_interruptibly


def test_run_interruptibly_restores_signal_handler() -> None:
    previous = signal.getsignal(signal.SIGINT)

    async def exercise() -> None:
        return None

    run_interruptibly(exercise())

    assert signal.getsignal(signal.SIGINT) == previous


def test_run_interruptibly_cleans_up_pending_tasks() -> None:
    cleaned_up = False

    async def pending() -> None:
        nonlocal cleaned_up
        try:
            await asyncio.Event().wait()
        finally:
            cleaned_up = True

    async def exercise() -> None:
        asyncio.create_task(pending())

    run_interruptibly(exercise())

    assert cleaned_up is True


def test_run_interruptibly_translates_cancelled_sigint_to_keyboard_interrupt(
    monkeypatch,
) -> None:
    original_signal = signal.signal

    async def exercise() -> None:
        await asyncio.Event().wait()

    fired = False

    def fake_signal(signum, handler):
        nonlocal fired
        previous = original_signal(signum, handler)
        if signum == signal.SIGINT and callable(handler) and not fired:
            fired = True
            asyncio.get_event_loop().call_soon(handler, signum, None)
        return previous

    monkeypatch.setattr(signal, "signal", fake_signal)

    with pytest.raises(KeyboardInterrupt):
        run_interruptibly(exercise())
