from __future__ import annotations

import pytest
import yaml

from spice.benchmarks.plan_materialization import materialize_benchmark_plan
from spice.config.models import EvaluateConfig, TrainConfig, TuneConfig, WorkflowTask
from spice.core.errors import ConfigResolutionError

ETH_DATASET_ID = "cor_9a73b1e88edb488afb1e"
EVALUATION_WINDOW = {"start": "2026-02-03T14:00:00Z", "duration_seconds": 7200}


def _with_evaluation_windows(payload: object) -> object:
    if isinstance(payload, dict):
        if payload.get("workflow") == "evaluate":
            step_set = payload.setdefault("set", {})
            if isinstance(step_set, dict):
                step_set.setdefault("evaluation_window", EVALUATION_WINDOW)
        for value in payload.values():
            _with_evaluation_windows(value)
    elif isinstance(payload, list):
        for value in payload:
            _with_evaluation_windows(value)
    return payload


def _write_benchmark(conf_root, name: str, payload: dict[str, object]) -> None:
    path = conf_root / "benchmark" / f"{name}.yaml"
    _with_evaluation_windows(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_benchmark_dimensions_expand_tuned_train_and_artifact_from(
    isolate_conf_root,
) -> None:
    conf_root = isolate_conf_root()
    _write_benchmark(
        conf_root,
        "dimension_case",
        {
            "cases": [
                {
                    "id": "window_sweep",
                    "base": {
                        "surface": "current_row_fee_dynamics",
                        "training": "default",
                        "split": "default",
                        "tuning": "extensive",
                        "study": "window_sweep",
                    },
                    "dimensions": {
                        "data": [{"set": {"chain": "ethereum", "corpus_id": ETH_DATASET_ID}}],
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
                            {"ref": "current_row_recent_median"},
                            {
                                "grid": {
                                    "base": "current_row_nominal",
                                    "fields": {
                                        "lookback_seconds": [600],
                                    },
                                }
                            },
                        ],
                    },
                    "steps": [
                        {
                            "id": "tune",
                            "workflow": "tune",
                            "set": {
                                "trial_count": 3,
                            },
                        },
                        {
                            "id": "train_tuned",
                            "workflow": "train",
                            "after": ["tune"],
                            "set": {"variant": "tuned"},
                        },
                        {
                            "id": "evaluate_tuned",
                            "workflow": "evaluate",
                            "after": ["train_tuned"],
                            "artifact_from": "train_tuned",
                            "set": {
                                "evaluator": "poisson_replay",
                                "delay_seconds": 36,
                            },
                        },
                    ],
                },
            ],
        },
    )

    plan = materialize_benchmark_plan("dimension_case")

    assert len(plan) == 12
    train = next(entry for entry in plan if entry.step_id == "train_tuned")
    grid_tune = next(
        entry
        for entry in plan
        if entry.step_id == "tune"
        and "problems-current_row_nominal__lookback_seconds-600" in entry.run_id
    )
    evaluate = next(
        entry
        for entry in plan
        if entry.step_id == "evaluate_tuned"
        and "models-model-lstm__tuning_space-lstm_large_capacity" in entry.run_id
        and "problems-current_row_nominal__lookback_seconds-600" in entry.run_id
    )
    assert isinstance(train.config, TrainConfig)
    assert train.config.study_id is not None
    assert isinstance(grid_tune.config, TuneConfig)
    assert grid_tune.config.problem.id == "current_row_nominal__lookback_seconds-600"
    assert grid_tune.config.problem.lookback_seconds == 600
    assert isinstance(evaluate.config, EvaluateConfig)
    assert evaluate.dependencies.artifact_from_run_id == evaluate.dependencies.local_run_ids[0]
    assert evaluate.config.corpus_id == ETH_DATASET_ID
    assert evaluate.config.artifact_id.startswith("art_")
    assert evaluate.config.delay_seconds == 36


def test_packaged_benchmark_yamls_keep_expected_shapes() -> None:
    expected_counts = {
        "large_capacity_hpo": 27,
        "priority_fee_ablation": 36,
        "safe_baseline_grid": 18,
        "delay_degradation_sweep": 180,
        "elapsed_position_ablation": 36,
        "lookback_window_sweep": 54,
        "slot_spacing_sweep": 36,
    }

    for name, expected_count in expected_counts.items():
        plan = materialize_benchmark_plan(name)
        evaluate_entries = [
            entry for entry in plan if entry.workflow is WorkflowTask.EVALUATE
        ]
        train_entries = [entry for entry in plan if entry.workflow is WorkflowTask.TRAIN]

        assert len(plan) == expected_count
        assert evaluate_entries
        assert train_entries
        assert all(isinstance(entry.config, EvaluateConfig) for entry in evaluate_entries)
        assert all(
            entry.dependencies.artifact_from_run_id in entry.dependencies.local_run_ids
            for entry in evaluate_entries
        )

def test_benchmark_rejects_step_local_evaluate_training_fields(isolate_conf_root) -> None:
    conf_root = isolate_conf_root()
    _write_benchmark(
        conf_root,
        "bad_evaluate",
        {
            "cases": [
                {
                    "id": "bad",
                    "base": {"surface": "current_row_fee_dynamics"},
                    "steps": [
                        {
                            "id": "evaluate",
                            "workflow": "evaluate",
                            "set": {"variant": "baseline"},
                        }
                    ],
                }
            ]
        },
    )

    with pytest.raises(ConfigResolutionError, match="does not support fields: variant"):
        materialize_benchmark_plan("bad_evaluate")


def test_benchmark_rejects_invalid_problem_grid(isolate_conf_root) -> None:
    conf_root = isolate_conf_root()
    _write_benchmark(
        conf_root,
        "invalid_grid",
        {
            "cases": [
                {
                    "id": "bad",
                    "base": {"surface": "current_row_fee_dynamics"},
                    "dimensions": {
                        "problems": [
                            {
                                "grid": {
                                    "base": "current_row_nominal",
                                    "fields": {"lookback_seconds": [0]},
                                }
                            }
                        ]
                    },
                    "steps": [{"id": "tune", "workflow": "tune"}],
                }
            ]
        },
    )

    with pytest.raises(ConfigResolutionError, match="values must be positive"):
        materialize_benchmark_plan("invalid_grid")


def test_benchmark_rejects_step_dependency_cycles(isolate_conf_root) -> None:
    conf_root = isolate_conf_root()
    _write_benchmark(
        conf_root,
        "cycle",
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
        },
    )

    with pytest.raises(ConfigResolutionError, match="future step"):
        materialize_benchmark_plan("cycle")


@pytest.mark.parametrize(
    "steps",
    [
        (
            [
                {"id": "train", "workflow": "train"},
                {"id": "train", "workflow": "train"},
            ],
        ),
        (
            [
                {"id": "evaluate", "workflow": "evaluate", "after": ["missing"]},
            ],
        ),
        (
            [
                {"id": "evaluate", "workflow": "evaluate", "after": ["evaluate"]},
            ],
        ),
        (
            [
                {"id": "evaluate", "workflow": "evaluate", "artifact_from": "missing"},
            ],
        ),
        (
            [
                {"id": "evaluate", "workflow": "evaluate", "artifact_from": "train"},
                {"id": "train", "workflow": "train"},
            ],
        ),
        (
            [
                {"id": "evaluate", "workflow": "evaluate", "artifact_from": "evaluate"},
            ],
        ),
    ],
)
def test_benchmark_dependency_validation_rejects_invalid_dependencies(
    isolate_conf_root,
    steps,
) -> None:
    conf_root = isolate_conf_root()
    _write_benchmark(
        conf_root,
        "bad_dependencies",
        {
            "cases": [
                {
                    "id": "bad",
                    "base": {"surface": "current_row_fee_dynamics"},
                    "steps": steps,
                }
            ]
        },
    )

    with pytest.raises(ConfigResolutionError):
        materialize_benchmark_plan("bad_dependencies")
