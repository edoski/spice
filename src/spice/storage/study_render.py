"""Study summary rendering helpers."""

from __future__ import annotations

from ..config import TunedParameterSet
from .study_models import StudySummary


def study_summary_sections(
    summary: StudySummary,
) -> list[tuple[str, list[tuple[str, str]]]]:
    best_trial = summary.best_trial
    return [
        (
            "study",
            [
                ("name", summary.manifest.study_name),
                ("storage id", summary.manifest.study_id),
                ("chain", summary.manifest.chain_name),
                ("dataset", summary.manifest.dataset_name),
                ("problem", summary.manifest.problem_id),
                ("prediction", summary.manifest.prediction_id),
                ("model", summary.manifest.model_id),
                ("trials", str(summary.trial_counts.total)),
            ],
        ),
        (
            "best trial",
            [
                ("monitor", summary.manifest.semantics.prediction.primary_metric_id),
                (
                    "value",
                    "n/a"
                    if best_trial is None or best_trial.value is None
                    else f"{best_trial.value:.4f}",
                ),
                ("trial", "n/a" if best_trial is None else str(best_trial.number + 1)),
                ("params", "n/a" if best_trial is None else format_best_params(best_trial.params)),
            ],
        ),
    ]


def format_best_params(params: TunedParameterSet) -> str:
    flattened = flatten_mapping(params.model_dump(mode="json", exclude_none=True))
    if not flattened:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in flattened.items())


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
