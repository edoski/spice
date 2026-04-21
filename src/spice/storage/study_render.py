"""Compact study result rendering helpers."""

from __future__ import annotations

from ..config.models import TunedParameterSet
from ..core.rendering import metric_string
from .study_models import StudySummary


def study_result_fields(summary: StudySummary) -> list[tuple[str, str]]:
    best_trial = summary.best_trial
    fields = [
        ("complete", str(summary.trial_counts.complete)),
        ("pruned", str(summary.trial_counts.pruned)),
        ("failed", str(summary.trial_counts.failed)),
    ]
    if best_trial is None or best_trial.value is None:
        fields.extend([("best_trial", "none"), ("best_value", "none")])
        return fields
    fields.extend(
        [
            ("best_trial", str(best_trial.number + 1)),
            ("best_value", metric_string(best_trial.value)),
        ]
    )
    params = format_best_params(best_trial.params)
    if params != "none":
        fields.append(("best_params", params))
    return fields


def format_best_params(params: TunedParameterSet) -> str:
    flattened = flatten_mapping(params.model_dump(mode="json", exclude_none=True))
    if not flattened:
        return "none"
    return ",".join(f"{key}={value}" for key, value in flattened.items())


def flatten_mapping(
    payload: dict[str, object],
    *,
    prefix: str = "",
) -> dict[str, float | int]:
    flattened: dict[str, float | int] = {}
    for key, value in payload.items():
        qualified_key = key if not prefix else f"{prefix}.{key}"
        if isinstance(value, dict):
            flattened.update(flatten_mapping(value, prefix=qualified_key))
            continue
        if isinstance(value, bool):
            flattened[qualified_key] = int(value)
            continue
        if isinstance(value, (int, float)):
            flattened[qualified_key] = value
    return flattened
