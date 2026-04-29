from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from spice.cli import selection as cli_selection
from spice.config import TrainWorkflowSelection, WorkflowTask
from spice.config.selections import workflow_selection_payload
from spice.core.errors import SpiceOperatorError


def test_cli_selection_builds_model_workflow_plan_and_resolves_config(monkeypatch) -> None:
    calls: list[tuple[WorkflowTask, object]] = []
    resolved_config = SimpleNamespace(id="resolved")

    def fake_resolve(task: WorkflowTask, selection) -> object:
        calls.append((task, selection))
        return resolved_config

    monkeypatch.setattr(cli_selection, "resolve_workflow_config", fake_resolve)

    plan = cli_selection.build_model_workflow_command_plan(
        task=WorkflowTask.TRAIN,
        selection_type=TrainWorkflowSelection,
        submit=False,
        dependency=None,
        detach=False,
        storage_root=Path("/tmp/spice"),
        surface="current_row_fee_dynamics",
        chain="ethereum",
        problem=None,
        features=None,
        objective=None,
        evaluation=None,
        model=None,
        tuning_space=None,
        training=None,
        split=None,
        tuning=None,
        study="default",
        variant="baseline",
    )

    assert plan.task is WorkflowTask.TRAIN
    assert plan.submit is False
    assert plan.config is resolved_config
    assert len(calls) == 1
    _, selection = calls[0]
    assert isinstance(selection, TrainWorkflowSelection)
    assert selection.surface == "current_row_fee_dynamics"
    assert selection.study == "default"
    assert selection.variant == "baseline"
    assert selection.storage_root == Path("/tmp/spice")


def test_cli_selection_payload_filters_unsupported_and_null_values() -> None:
    assert workflow_selection_payload(
        WorkflowTask.TRAIN,
        {
            "surface": "current_row_fee_dynamics",
            "provider": "publicnode",
            "study": None,
            "variant": "baseline",
        },
    ) == {"surface": "current_row_fee_dynamics", "variant": "baseline"}


def test_cli_submit_validation_rejects_local_storage_override() -> None:
    with pytest.raises(SpiceOperatorError, match="--storage-root"):
        cli_selection.validate_submission_flags(
            submit=True,
            dependency=None,
            detach=False,
            storage_root=Path("/tmp/spice"),
        )


def test_cli_submit_validation_rejects_submit_only_flags_for_local_run() -> None:
    with pytest.raises(SpiceOperatorError, match="--dependency and --detach"):
        cli_selection.validate_submission_flags(
            submit=False,
            dependency="afterok:123",
            detach=False,
            storage_root=None,
        )


def test_cli_submit_selection_drops_storage_root(monkeypatch) -> None:
    calls: list[TrainWorkflowSelection] = []

    def fake_resolve(_task: WorkflowTask, selection) -> object:
        calls.append(selection)
        return SimpleNamespace(id="resolved")

    monkeypatch.setattr(cli_selection, "resolve_workflow_config", fake_resolve)

    cli_selection.build_model_workflow_command_plan(
        task=WorkflowTask.TRAIN,
        selection_type=TrainWorkflowSelection,
        submit=True,
        dependency=None,
        detach=False,
        storage_root=None,
        surface="current_row_fee_dynamics",
        chain=None,
        problem=None,
        features=None,
        objective=None,
        evaluation=None,
        model=None,
        tuning_space=None,
        training=None,
        split=None,
        tuning=None,
        study=None,
        variant="baseline",
    )

    assert calls[0].storage_root is None
