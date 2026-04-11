"""Project-wide constants."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

DEFAULT_WINDOW_START_DATE = date(2025, 11, 9)
DEFAULT_WINDOW_END_DATE = date(2025, 11, 9)
DEFAULT_WINDOW_START_TIMESTAMP = int(
    datetime.combine(DEFAULT_WINDOW_START_DATE, time.min, tzinfo=UTC).timestamp()
)
DEFAULT_WINDOW_END_TIMESTAMP = int(
    datetime.combine(
        DEFAULT_WINDOW_END_DATE + timedelta(days=1),
        time.min,
        tzinfo=UTC,
    ).timestamp()
)

ARTIFACT_MANIFEST_FILENAME = "artifact.json"
MODEL_STATE_FILENAME = "model.pt"
