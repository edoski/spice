"""Project environment helpers."""

from __future__ import annotations

from dotenv import load_dotenv

from spice_temporal.constants import PROJECT_ROOT


def load_project_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
