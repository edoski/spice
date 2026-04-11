"""OS-specific power management helpers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def keep_system_awake() -> Iterator[None]:
    """Keep macOS awake for the lifetime of the current process when possible."""

    if sys.platform != "darwin":
        yield
        return

    caffeinate = shutil.which("caffeinate")
    if caffeinate is None:
        yield
        return

    watcher = subprocess.Popen(
        [caffeinate, "-i", "-w", str(os.getpid())],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        yield
    finally:
        if watcher.poll() is None:
            watcher.terminate()
            try:
                watcher.wait(timeout=1)
            except subprocess.TimeoutExpired:
                watcher.kill()
                watcher.wait()
