from __future__ import annotations

import pytest

from spice.benchmarks.planning import plan_benchmark_workflow_selections
from spice.benchmarks.schema import BenchmarkSpec
from spice.config.models import WorkflowTask
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
                        "data": [
                            {
                                "set": {
                                    "chain": "ethereum",
                                    "dataset_id": "cor_9a73b1e88edb488afb1e",
                                }
                            }
                        ],
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
                            "id": "train_tuned",
                            "workflow": "train",
                            "after": ["tune", {"slurm": "afterok:999"}],
                            "set": {"variant": "tuned"},
                        },
                        {
                            "id": "evaluate_tuned",
                            "workflow": "evaluate",
                            "after": ["train_tuned"],
                            "artifact_from": "train_tuned",
                            "set": {"evaluation": "poisson_replay_2h", "delay_seconds": 36},
                        },
                    ],
                }
            ]
        }
    )

    selections = plan_benchmark_workflow_selections(spec)

    assert len(selections) == 12
    evaluate = next(
        selection
        for selection in selections
        if selection.step_id == "evaluate_tuned"
        and selection.dimension_labels["models"]
        == "model-lstm__tuning_space-lstm_large_capacity"
        and selection.dimension_labels["problems"]
        == "current_row_nominal__lookback_seconds-600"
    )
    assert evaluate.run_id == (
        "window_sweep."
        "data-chain-ethereum__dataset_id-cor_9a73b1e88edb488afb1e."
        "models-model-lstm__tuning_space-lstm_large_capacity."
        "problems-current_row_nominal__lookback_seconds-600."
        "evaluate_tuned"
    )
    assert evaluate.depends_on == (
        "window_sweep."
        "data-chain-ethereum__dataset_id-cor_9a73b1e88edb488afb1e."
        "models-model-lstm__tuning_space-lstm_large_capacity."
        "problems-current_row_nominal__lookback_seconds-600."
        "train_tuned",
    )
    assert evaluate.artifact_from == evaluate.depends_on[0]
    assert evaluate.external_dependencies == ()
    assert evaluate.workflow is WorkflowTask.EVALUATE
    assert evaluate.selection_payload["problem"] == "current_row_nominal__lookback_seconds-600"


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


def test_artifact_from_implies_dependency() -> None:
    spec = BenchmarkSpec.model_validate(
        {
            "cases": [
                {
                    "id": "implicit_dependency",
                    "base": {"surface": "current_row_fee_dynamics"},
                    "steps": [
                        {
                            "id": "train",
                            "workflow": "train",
                            "set": {
                                "dataset_id": "cor_9a73b1e88edb488afb1e",
                                "variant": "baseline",
                            },
                        },
                        {
                            "id": "evaluate",
                            "workflow": "evaluate",
                            "artifact_from": "train",
                            "set": {"evaluation": "poisson_replay_2h"},
                        },
                    ],
                }
            ]
        }
    )

    evaluate = next(
        selection
        for selection in plan_benchmark_workflow_selections(spec)
        if selection.step_id == "evaluate"
    )

    assert evaluate.artifact_from == "implicit_dependency.train"
    assert evaluate.depends_on == ("implicit_dependency.train",)


def test_planner_rejects_unknown_artifact_from_step() -> None:
    spec = BenchmarkSpec.model_validate(
        {
            "cases": [
                {
                    "id": "bad",
                    "base": {"surface": "current_row_fee_dynamics"},
                    "steps": [
                        {
                            "id": "evaluate",
                            "workflow": "evaluate",
                            "artifact_from": "missing",
                            "set": {"evaluation": "poisson_replay_2h"},
                        }
                    ],
                }
            ]
        }
    )

    with pytest.raises(ConfigResolutionError, match="unknown step missing"):
        plan_benchmark_workflow_selections(spec)


def test_planner_rejects_future_artifact_from_step() -> None:
    spec = BenchmarkSpec.model_validate(
        {
            "cases": [
                {
                    "id": "bad",
                    "base": {"surface": "current_row_fee_dynamics"},
                    "steps": [
                        {
                            "id": "evaluate",
                            "workflow": "evaluate",
                            "artifact_from": "train",
                            "set": {"evaluation": "poisson_replay_2h"},
                        },
                        {
                            "id": "train",
                            "workflow": "train",
                            "set": {
                                "dataset_id": "cor_9a73b1e88edb488afb1e",
                                "variant": "baseline",
                            },
                        },
                    ],
                }
            ]
        }
    )

    with pytest.raises(ConfigResolutionError, match="future step train"):
        plan_benchmark_workflow_selections(spec)
