from __future__ import annotations

import pytest
from typer.testing import CliRunner

from spice.cli import app
from spice.core.config import WorkflowTask

runner = CliRunner()


@pytest.mark.parametrize(
    ("command", "task_name", "target"),
    [
        ("acquire", WorkflowTask.ACQUIRE, "acquire"),
        ("train", WorkflowTask.TRAIN, "train"),
        ("tune", WorkflowTask.TUNE, "tune"),
        ("simulate", WorkflowTask.SIMULATE, "simulate"),
    ],
)
def test_root_cli_dispatches_subcommands(tmp_path, monkeypatch, command, task_name, target) -> None:
    captured: dict[str, object] = {}

    def _capture(config) -> None:
        captured["task"] = config.task
        captured["dataset_id"] = config.dataset.id

    monkeypatch.setattr(f"spice.cli.{target}.run", _capture)

    result = runner.invoke(
        app,
        [
            command,
            f"runtime.output_root={tmp_path / 'artifacts'}",
            "training.device=cpu",
            "training.max_epochs=1",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert captured["task"] is task_name
    assert captured["dataset_id"] == "icdcs_2025_11_09"
