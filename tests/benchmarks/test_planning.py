from __future__ import annotations

import pytest

from spice.benchmarks.planning import plan_benchmark_workflow_selections
from spice.benchmarks.schema import BenchmarkSpec
from spice.config.models import ProblemSpec, WorkflowTask
from spice.core.errors import ConfigResolutionError


def test_planner_expands_dimensions_dependencies_and_problem_grids(
    isolate_conf_root,
) -> None:
    isolate_conf_root()
    spec = BenchmarkSpec.model_validate(
        {
            "cases": [
                {
                    "id": "window_sweep",
                    "base": {
                        "surface": "current_row_fee_dynamics",
                        "training": "default",
                        "split": "default",
                    },
                    "dimensions": {
                        "models": [
                            {"set": {"model": "lstm", "tuning_space": "lstm_large_capacity"}},
                            {
                                "set": {
                                    "model": "transformer",
                                    "tuning_space": "transformer_large_capacity",
                                }
                            },
                        ],
                        "problems": [
                            {
                                "grid": {
                                    "base": "current_row_nominal",
                                    "fields": {"lookback_seconds": [600, 900]},
                                }
                            }
                        ],
                    },
                    "steps": [
                        {
                            "id": "tune",
                            "workflow": "tune",
                            "set": {
                                "objective": "validation_total_loss",
                                "evaluation": "poisson_replay_2h",
                                "trial_count": 3,
                            },
                        },
                        {
                            "id": "evaluate",
                            "workflow": "evaluate",
                            "after": ["tune", {"slurm": "afterok:999"}],
                            "dimensions": {
                                "scoring": [
                                    {
                                        "set": {
                                            "objective": "profit_poisson_replay_2h",
                                            "evaluation": "poisson_replay_2h",
                                        }
                                    }
                                ],
                                "runtime": [
                                    {"set": {"variant": "tuned", "delay_seconds": 36}},
                                ],
                            },
                        },
                    ],
                }
            ]
        }
    )

    selections = plan_benchmark_workflow_selections(spec)

    assert len(selections) == 8
    evaluate = next(
        selection
        for selection in selections
        if selection.step_id == "evaluate"
        and selection.dimension_labels["models"]
        == "model-lstm__tuning_space-lstm_large_capacity"
        and selection.dimension_labels["problems"]
        == "current_row_nominal__lookback_seconds-600"
    )
    assert evaluate.run_id == (
        "window_sweep."
        "models-model-lstm__tuning_space-lstm_large_capacity."
        "problems-current_row_nominal__lookback_seconds-600."
        "scoring-objective-profit_poisson_replay_2h__evaluation-poisson_replay_2h."
        "runtime-variant-tuned__delay_seconds-36."
        "evaluate"
    )
    assert evaluate.depends_on == (
        "window_sweep."
        "models-model-lstm__tuning_space-lstm_large_capacity."
        "problems-current_row_nominal__lookback_seconds-600."
        "tune",
    )
    assert evaluate.external_dependencies == ("afterok:999",)
    assert evaluate.workflow is WorkflowTask.EVALUATE
    assert isinstance(evaluate.selection.problem, ProblemSpec)
    assert evaluate.selection.problem.id == "current_row_nominal__lookback_seconds-600"
    assert evaluate.selection_payload["problem"] == evaluate.selection.problem.id


def test_planner_rejects_future_step_dependencies() -> None:
    spec = BenchmarkSpec.model_validate(
        {
            "cases": [
                {
                    "id": "bad",
                    "base": {"surface": "current_row_fee_dynamics"},
                    "steps": [
                        {"id": "train", "workflow": "train", "after": ["evaluate"]},
                        {"id": "evaluate", "workflow": "evaluate", "after": ["train"]},
                    ],
                }
            ]
        }
    )

    with pytest.raises(ConfigResolutionError, match="future step"):
        plan_benchmark_workflow_selections(spec)
