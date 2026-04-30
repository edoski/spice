from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace

import pytest

from spice.benchmarks import (
    BenchmarkPlanEntry,
    BenchmarkSubmissionRecord,
    append_submission_jsonl,
    collect_benchmark_run,
    create_benchmark_run_dir,
    write_plan_jsonl,
)
from spice.config import EvaluateConfig, StorageSpec, WorkflowTask
from spice.config.models import ArtifactVariant
from spice.config.registry import load_named_group
from spice.core.errors import SelectorResolutionError, SpiceOperatorError
from spice.evaluation.registry import coerce_evaluator_config


def _evaluate_config(tmp_path: Path) -> EvaluateConfig:
    return EvaluateConfig(
        storage=StorageSpec(root=tmp_path / "outputs"),
        artifact_id="artifact-1",
        dataset_id="dataset-1",
        evaluation=coerce_evaluator_config(load_named_group("poisson_replay_2h", "evaluation")),
        delay_seconds=36,
    )


def _write_evaluate_run(run_dir: Path, config) -> None:
    entry = BenchmarkPlanEntry(
        run_id="case.evaluate",
        case_id="case",
        step_id="evaluate",
        workflow=WorkflowTask.EVALUATE,
        depends_on=(),
        external_dependencies=(),
        artifact_from=None,
        selection={
            "artifact_id": config.artifact_id,
            "dataset_id": config.dataset_id,
            "evaluation": config.evaluation.id,
            "delay_seconds": config.delay_seconds,
        },
        config=config,
    )
    write_plan_jsonl(run_dir, [entry])
    append_submission_jsonl(
        run_dir,
        BenchmarkSubmissionRecord(
            run_id=entry.run_id,
            workflow=entry.workflow,
            job_id="57549",
            execution_ref="slurm:57549",
            git_commit="abc123",
            dependency=None,
            log_path="/tmp/spice-evaluate-57549.out",
        ),
    )


def _loaded_summary(config):
    return SimpleNamespace(
        evaluation_id="poisson_replay_2h-36s-storage",
        recorded_at=1_700_000_000,
        manifest=SimpleNamespace(
            artifact_id="artifact-1",
            chain_name="ethereum",
            dataset_name="icdcs_2026",
            features_id="core_fee_dynamics",
            model=SimpleNamespace(id="lstm"),
            problem_id="current_row_nominal",
            prediction_id="icdcs_2026",
            objective=SimpleNamespace(id="profit_poisson_replay_2h"),
            variant=ArtifactVariant.BASELINE,
            study=None,
        ),
        runtime=SimpleNamespace(
            delay_seconds=config.delay_seconds,
            evaluation_id=config.evaluation.id,
            sample_count=123,
            total_events=7,
            metrics=SimpleNamespace(
                values={
                    "profit_over_baseline": 0.12,
                    "cost_over_optimum": 1.5,
                    "baseline_cost_over_optimum": 1.7,
                }
            ),
        ),
    )


def test_benchmark_collect_writes_and_skips_duplicate_rows(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = _evaluate_config(tmp_path)
    run_dir = create_benchmark_run_dir(
        "collect_case",
        target="disi_l40",
        git_commit="abc123",
        runs_root=tmp_path / "outputs" / "benchmarks" / "runs",
    )
    _write_evaluate_run(run_dir, config)
    resolve_calls: list[object] = []

    def fake_resolve(config, *, session):
        resolve_calls.append(session)
        return SimpleNamespace(
            evaluation=_loaded_summary(config),
            training=SimpleNamespace(
                runtime=SimpleNamespace(
                    test_metrics=SimpleNamespace(
                        values={
                            "total_loss": 0.3,
                            "offset_accuracy": 0.8,
                            "macro_f1": 0.7,
                        }
                    )
                )
            ),
        )

    monkeypatch.setattr("spice.benchmarks.collection.open_execution_session", lambda _target: "s")
    monkeypatch.setattr("spice.benchmarks.collection.resolve_benchmark_evaluation", fake_resolve)
    ledger_path = tmp_path / "benchmarks" / "results.csv"

    records = collect_benchmark_run(
        run_dir=run_dir,
        target_name="disi_l40",
        ledger_path=ledger_path,
        write=True,
    )
    duplicate_records = collect_benchmark_run(
        run_dir=run_dir,
        target_name="disi_l40",
        ledger_path=ledger_path,
        write=True,
    )

    assert records[0].status == "ready"
    assert duplicate_records[0].status == "skipped"
    rows = list(csv.DictReader(ledger_path.open("r", encoding="utf-8", newline="")))
    assert len(rows) == 1
    assert rows[0]["git_commit"] == "abc123"
    assert rows[0]["execution_ref"] == "slurm:57549"
    assert rows[0]["surface"] == ""
    assert rows[0]["objective"] == "profit_poisson_replay_2h"
    assert rows[0]["profit_over_baseline"] == "0.12"
    assert rows[0]["total_loss"] == "0.3"
    assert rows[0]["offset_accuracy"] == "0.8"
    assert rows[0]["macro_f1"] == "0.7"
    assert rows[0]["log_fee_mae"] == ""
    assert resolve_calls == ["s", "s"]


def test_benchmark_collect_refuses_partial_ledger_write(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = _evaluate_config(tmp_path)
    run_dir = create_benchmark_run_dir(
        "missing_case",
        target="disi_l40",
        git_commit="abc123",
        runs_root=tmp_path / "outputs" / "benchmarks" / "runs",
    )
    _write_evaluate_run(run_dir, config)

    def missing_remote_artifact(_config, *, session):
        del session
        raise SelectorResolutionError(kind="artifact", records=[])

    monkeypatch.setattr("spice.benchmarks.collection.open_execution_session", lambda _target: "s")
    monkeypatch.setattr(
        "spice.benchmarks.collection.resolve_benchmark_evaluation",
        missing_remote_artifact,
    )
    ledger_path = tmp_path / "benchmarks" / "results.csv"

    with pytest.raises(SpiceOperatorError, match="Refusing partial"):
        collect_benchmark_run(
            run_dir=run_dir,
            target_name="disi_l40",
            ledger_path=ledger_path,
            write=True,
        )

    assert not ledger_path.exists()
