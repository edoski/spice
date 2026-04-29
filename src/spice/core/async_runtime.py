"""Interruptible asyncio runtime helpers."""

from __future__ import annotations

import asyncio
import signal
from collections.abc import Coroutine
from typing import Any


def run_interruptibly(coro: Coroutine[Any, Any, None]) -> None:
    """Run a coroutine from synchronous code and translate SIGINT into interruption."""

    loop = asyncio.new_event_loop()
    task = loop.create_task(coro)
    interrupted = False
    previous_sigint = None

    def _handle_sigint(signum: int, frame: object) -> None:
        del signum, frame
        nonlocal interrupted
        interrupted = True
        if not task.done():
            loop.call_soon_threadsafe(task.cancel)

    try:
        asyncio.set_event_loop(loop)
        try:
            previous_sigint = signal.getsignal(signal.SIGINT)
            signal.signal(signal.SIGINT, _handle_sigint)
        except ValueError:
            previous_sigint = None
        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError as exc:
            if interrupted:
                raise KeyboardInterrupt from exc
            raise
        except KeyboardInterrupt:
            interrupted = True
            if not task.done():
                task.cancel()
                try:
                    loop.run_until_complete(task)
                except (asyncio.CancelledError, KeyboardInterrupt):
                    pass
            raise
    finally:
        if previous_sigint is not None:
            try:
                signal.signal(signal.SIGINT, previous_sigint)
            except ValueError:
                pass
        pending = [
            pending_task for pending_task in asyncio.all_tasks(loop) if not pending_task.done()
        ]
        for pending_task in pending:
            pending_task.cancel()
        if pending:
            try:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except (asyncio.CancelledError, KeyboardInterrupt):
                pass
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
        asyncio.set_event_loop(None)
        loop.close()
