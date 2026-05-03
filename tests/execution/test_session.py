from __future__ import annotations

import sys
from pathlib import Path
from subprocess import CompletedProcess
from types import SimpleNamespace
from typing import cast

from spice.config import TrainWorkflowSelection, WorkflowTask, resolve_workflow_config
from spice.execution.models import ExecutionWorkflowSpec
from spice.execution.session import ExecutionJobSubmission, ExecutionSession, ExecutionTarget


def _target(tmp_path: Path | None = None) -> ExecutionTarget:
    log_root = tmp_path or Path("/logs")
    return ExecutionTarget(
        name="disi_l40",
        spec=SimpleNamespace(
            ssh=SimpleNamespace(user="edoardo.galli3", host="giano.cs.unibo.it"),
            paths=SimpleNamespace(
                repo_root=Path("/repo"),
                venv_activate_path=Path("/venv/bin/activate"),
                storage_root=Path("/storage"),
                log_root=log_root,
                python_path=Path("/venv/bin/python"),
            ),
            workflows=SimpleNamespace(
                train=ExecutionWorkflowSpec(
                    partition="l40",
                    gpus=1,
                    cpus_per_task=4,
                    memory_gb=24,
                    time_limit="00:10:00",
                ),
            ),
            follow_by_default=True,
        ),
    )


def test_execution_session_quotes_full_command() -> None:
    session = ExecutionSession(_target())

    argv = session.build_shell_argv("mkdir -p /scratch/test && cat | sbatch")

    assert argv == [
        "ssh",
        "edoardo.galli3@giano.cs.unibo.it",
        "bash",
        "-lc",
        "'mkdir -p /scratch/test && cat | sbatch'",
    ]


def test_execution_session_run_command_passes_quoted_command(monkeypatch) -> None:
    session = ExecutionSession(_target())
    captured: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        captured["args"] = args[0]
        captured["kwargs"] = kwargs
        return CompletedProcess(args=args[0], returncode=0, stdout="", stderr="")

    monkeypatch.setattr("spice.execution.session.subprocess.run", fake_run)

    result = session.run_command("mkdir -p /scratch/test && cat | sbatch")

    assert result.returncode == 0
    assert captured["args"] == session.build_shell_argv("mkdir -p /scratch/test && cat | sbatch")


def test_execution_session_run_module_uses_target_python_and_repo(monkeypatch) -> None:
    session = ExecutionSession(_target())
    captured: dict[str, object] = {}

    def fake_run(_self, command: str, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return CompletedProcess(args=["ssh"], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(ExecutionSession, "run_command", fake_run)

    session.run_module("spice.storage.sync_cli", ["prepare-stage", "--replace"])

    assert captured["command"] == (
        "cd /repo && /venv/bin/python -m spice.storage.sync_cli prepare-stage --replace"
    )


def test_execution_session_rsync_delegates_to_subprocess(monkeypatch) -> None:
    session = ExecutionSession(_target())
    calls: list[list[str]] = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("spice.execution.session.subprocess.run", fake_run)

    session.rsync_to(source_root=Path("/local"), destination_root=Path("/remote"))
    session.rsync_from(source_root=Path("/remote"), destination_root=Path("/local"))

    assert calls == [
        [
            "rsync",
            "-a",
            "/local/",
            "edoardo.galli3@giano.cs.unibo.it:/remote/",
        ],
        [
            "rsync",
            "-a",
            "edoardo.galli3@giano.cs.unibo.it:/remote/",
            "/local/",
        ],
    ]


def test_execution_session_submit_workflow_forwards_sbatch_dependency(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session = ExecutionSession(_target(tmp_path))
    captured: dict[str, object] = {}

    def fake_run_command(_self, command: str, **kwargs):
        captured["command"] = command
        captured["input_text"] = kwargs.get("input_text")
        captured["check_action"] = kwargs.get("check_action")
        return CompletedProcess(
            args=["ssh", "giano"],
            returncode=0,
            stdout="Submitted batch job 12345\n",
            stderr="",
        )

    monkeypatch.setattr(ExecutionSession, "run_command", fake_run_command)

    submission = session.submit_workflow(
        WorkflowTask.TRAIN,
        config=resolve_workflow_config(
                WorkflowTask.TRAIN,
                TrainWorkflowSelection(
                    surface="current_row_fee_dynamics",
                    dataset_id="cor_9a73b1e88edb488afb1e",
                ),
            ),
        dependency="afterok:99999",
    )

    assert submission.job_id == "12345"
    assert captured["command"] == (
        f"mkdir -p {tmp_path} && mkdir -p /storage && cat | sbatch --dependency=afterok:99999"
    )
    assert captured["check_action"] == "submit train"
    assert isinstance(captured["input_text"], str)


def test_execution_session_follow_job_uses_quoted_tail_command(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session = ExecutionSession(_target(tmp_path))
    captured: dict[str, object] = {}

    class FakePopen:
        def __init__(self, args, *, text, stdout):
            captured["args"] = args
            captured["text"] = text
            captured["stdout"] = stdout

        def poll(self):
            return 0

        def terminate(self) -> None:
            return None

        def wait(self, timeout=None) -> int:
            return 0

    monkeypatch.setattr("spice.execution.session.subprocess.Popen", FakePopen)
    monkeypatch.setattr(ExecutionSession, "read_job_state", lambda _self, _submission: None)
    monkeypatch.setattr(
        ExecutionSession,
        "read_job_final_state",
        lambda _self, _submission: "COMPLETED",
    )
    submission = ExecutionJobSubmission(
        task=WorkflowTask.TRAIN,
        job_id="12345",
        log_path=tmp_path / "spice-train-12345.out",
    )

    state = session.follow_job(submission)

    assert state == "COMPLETED"
    argv = cast(list[str], captured["args"])
    assert argv[:3] == ["ssh", "edoardo.galli3@giano.cs.unibo.it", "bash"]
    assert str(submission.log_path) in argv[-1]
    assert "tail -n +1 -F" in argv[-1]
    assert captured["text"] is True
    assert captured["stdout"] is sys.stderr


def test_execution_session_remote_git_commit(monkeypatch) -> None:
    session = ExecutionSession(_target())

    def fake_run_command(_self, command: str, **kwargs):
        assert command == "cd /repo && git rev-parse HEAD"
        assert kwargs["check_action"] == "read remote git commit for disi_l40"
        return CompletedProcess(args=["ssh"], returncode=0, stdout="abc123\n", stderr="")

    monkeypatch.setattr(ExecutionSession, "run_command", fake_run_command)

    assert session.remote_git_commit() == "abc123"
