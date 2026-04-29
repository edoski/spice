from __future__ import annotations

from pathlib import Path

from spice.config import (
    AcquireWorkflowSelection,
    EvaluateWorkflowSelection,
    TrainWorkflowSelection,
    TuneWorkflowSelection,
    WorkflowTask,
    coerce_problem_spec,
)
from spice.config.registry import load_named_group
from spice.config.selections import (
    workflow_selection_fields,
    workflow_selection_payload,
    workflow_selection_type,
)


def test_workflow_selection_type_maps_each_workflow() -> None:
    assert workflow_selection_type(WorkflowTask.ACQUIRE) is AcquireWorkflowSelection
    assert workflow_selection_type(WorkflowTask.TRAIN) is TrainWorkflowSelection
    assert workflow_selection_type(WorkflowTask.TUNE) is TuneWorkflowSelection
    assert workflow_selection_type(WorkflowTask.EVALUATE) is EvaluateWorkflowSelection


def test_workflow_selection_payload_keeps_only_supported_non_null_fields() -> None:
    payload = workflow_selection_payload(
        WorkflowTask.TRAIN,
        {
            "surface": "current_row_fee_dynamics",
            "model": "lstm",
            "trial_count": 3,
            "provider": "publicnode",
            "storage_root": Path("outputs"),
            "features": None,
        },
    )

    assert payload == {
        "surface": "current_row_fee_dynamics",
        "model": "lstm",
        "storage_root": Path("outputs"),
    }


def test_inline_problem_spec_is_valid_for_all_workflow_selections() -> None:
    problem = coerce_problem_spec(load_named_group("current_row_nominal", "problem"))

    for workflow in WorkflowTask:
        selection_type = workflow_selection_type(workflow)
        selection = selection_type.model_validate(
            {
                "surface": "current_row_fee_dynamics",
                "problem": problem,
            }
        )

        assert "problem" in workflow_selection_fields(workflow)
        assert selection.problem == problem
