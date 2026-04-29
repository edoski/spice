from __future__ import annotations

import pytest

from spice.config import (
    EvaluateConfig,
    TrainConfig,
    TuneConfig,
    WorkflowTask,
    resolve_workflow_config,
)
from spice.config.selections import workflow_selection_type
from spice.execution.remote_runner import workflow_config_from_json


@pytest.mark.parametrize(
    ("task", "expected_type"),
    [
        (WorkflowTask.TRAIN, TrainConfig),
        (WorkflowTask.TUNE, TuneConfig),
        (WorkflowTask.EVALUATE, EvaluateConfig),
    ],
)
def test_remote_runner_rehydrates_resolved_workflow_snapshots(
    task: WorkflowTask,
    expected_type: type[object],
) -> None:
    config = resolve_workflow_config(
        task,
        workflow_selection_type(task).model_validate({"surface": "current_row_fee_dynamics"}),
    )

    restored = workflow_config_from_json(
        task,
        config.model_dump_json(exclude_none=True),
    )

    assert isinstance(restored, expected_type)
    assert restored.model_dump(mode="json") == config.model_dump(mode="json")
