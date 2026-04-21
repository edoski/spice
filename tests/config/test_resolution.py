from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
import yaml

from spice.config import TrainConfig, WorkflowRequest, WorkflowTask, resolve_workflow_config
from spice.config.registry import load_named_group
from spice.core.errors import ConfigResolutionError


def _write_preset(conf_root: Path, name: str, payload: dict[str, object]) -> None:
    path = conf_root / "preset" / f"{name}.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_named_spec_identity_is_enforced_on_normal_load_paths(isolate_conf_root) -> None:
    conf_root = isolate_conf_root()
    aliased_problem = conf_root / "problem" / "aliased_problem.yaml"
    aliased_problem.write_text(
        yaml.safe_dump(
            {
                "id": "different_problem",
                "lookback_seconds": 900,
                "sample_count": 400000,
                "max_delay_seconds": 36,
                "compiler": {
                    "id": "estimated_block",
                    "lookback_interval_source": "nominal_chain_runtime",
                    "candidate_interval_source": "calibrated",
                    "calibrated_interval_statistic": "mean",
                },
                "realization_policy": {"id": "strict_deadline_miss"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ConfigResolutionError,
        match="problem id must match spec name: aliased_problem",
    ):
        load_named_group("aliased_problem", "problem")


def test_preset_extends_merges_known_blocks_and_replaces_names(
    tmp_path: Path,
    isolate_conf_root,
) -> None:
    conf_root = isolate_conf_root()
    child_root = tmp_path / "child_outputs"
    _write_preset(
        conf_root,
        "child_train",
        {
            "extends": "icdcs_2026",
            "objective": "paper_profit_replay_2h",
            "training": {
                "batch_size": 64,
                "early_stopping": {"patience": 3},
            },
            "split": {"train_fraction": 0.7},
            "storage": {"root": str(child_root)},
            "study": {"name": "child-study"},
            "artifact": {"variant": "baseline"},
        },
    )

    config = cast(
        TrainConfig,
        resolve_workflow_config(
            WorkflowTask.TRAIN,
            WorkflowRequest(preset="child_train"),
        ),
    )

    assert config.objective.metric_id == "profit_over_baseline"
    assert config.objective.direction == "maximize"
    assert config.training.learning_rate == 0.0003
    assert config.training.batch_size == 64
    assert config.training.early_stopping.patience == 3
    assert config.training.early_stopping.min_delta == 0.0001
    assert config.split.train_fraction == 0.7
    assert config.split.validation_fraction == 0.1
    assert config.storage.root == child_root
    assert config.study.name == "child-study"
    assert config.artifact.variant.value == "baseline"


@pytest.mark.parametrize(
    ("name", "payload", "match"),
    [
        (
            "missing_parent",
            {"extends": "does_not_exist"},
            "Unknown preset: does_not_exist",
        ),
        (
            "cycle_a",
            {"extends": "cycle_b"},
            "Preset extends cycle: cycle_a -> cycle_b -> cycle_a",
        ),
        (
            "unknown_overlay",
            {"extends": "icdcs_2026", "training": {"unknown": 1}},
            "Unknown training preset fields: unknown",
        ),
    ],
)
def test_preset_overlay_reports_resolution_errors(
    tmp_path: Path,
    isolate_conf_root,
    name: str,
    payload: dict[str, object],
    match: str,
) -> None:
    conf_root = isolate_conf_root()
    _write_preset(conf_root, name, payload)
    if name == "cycle_a":
        _write_preset(conf_root, "cycle_b", {"extends": "cycle_a"})

    with pytest.raises(ConfigResolutionError, match=match):
        resolve_workflow_config(
            WorkflowTask.TRAIN,
            WorkflowRequest(preset=name, storage_root=tmp_path / "outputs"),
        )


def test_preset_parent_must_be_runnable(tmp_path: Path, isolate_conf_root) -> None:
    conf_root = isolate_conf_root()
    _write_preset(conf_root, "bad_parent", {"extends": "icdcs_2026", "delay_seconds": 999})
    _write_preset(conf_root, "child_bad_parent", {"extends": "bad_parent"})

    with pytest.raises(
        ConfigResolutionError,
        match="Parent preset bad_parent is not runnable for evaluate",
    ):
        resolve_workflow_config(
            WorkflowTask.TRAIN,
            WorkflowRequest(preset="child_bad_parent", storage_root=tmp_path / "outputs"),
        )
