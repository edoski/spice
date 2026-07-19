from __future__ import annotations

from io import StringIO
from types import SimpleNamespace
from typing import cast

from spice.modeling.tuning_execution import TuningTrialProgress

from spice.config import TuneConfig, WorkflowTask
from spice.core.reporting import Reporter
from spice.workflows import reporting as workflow_reporting
from spice.workflows import tune as tune_workflow
from tests.root_handle_helpers import corpus_handle, study_handle, tune_roots


def _load_test_tune_config(
    load_workflow_config,
    tmp_path,
    *,
    override: dict[str, object] | None = None,
) -> TuneConfig:
    return cast(
        TuneConfig,
        load_workflow_config(
            WorkflowTask.TUNE,
            workspace=tmp_path,
            surface="current_row_fee_dynamics",
            override=override,
        ),
    )


def test_tune_workflow_emits_per_trial_not_per_epoch_output(
    tmp_path,
    monkeypatch,
    load_workflow_config,
    model_workflow_override,
    tune_override,
) -> None:
    override = model_workflow_override() | tune_override()
    override["tuning"] = {
        "trial_count": 2,
        "timeout_seconds": None,
        "sampler_seed": 2026,
        "enable_pruning": False,
    }
    config = _load_test_tune_config(load_workflow_config, tmp_path, override=override)
    output = StringIO()
    reporter = Reporter(stream=output)

    corpus = corpus_handle(
        tmp_path / "outputs",
        chain_name=config.chain.name,
        corpus_id=cast(str, config.corpus_id),
        corpus_name=config.corpus.name,
    )
    study = study_handle(
        tmp_path / "outputs",
        corpus=corpus,
        study_id="std_test",
        study_name=config.study.name,
    )
    roots = tune_roots(tmp_path / "outputs", corpus=corpus, study=study)
    monkeypatch.setattr(
        tune_workflow,
        "prepare_tune",
        lambda _config: SimpleNamespace(
            roots=roots,
            corpus_manifest=SimpleNamespace(),
        ),
    )
    monkeypatch.setattr(
        tune_workflow,
        "open_tuning_execution",
        lambda *_args, **_kwargs: SimpleNamespace(
            manifest=object(),
            study=object(),
            existing_trial_count=0,
            target_trial_count=2,
            remaining_trial_count=2,
        ),
    )

    def fake_run_tuning_execution(_opened, *, callbacks, **_kwargs):
        callbacks.on_study_start(2)
        callbacks.on_trial_complete(
            TuningTrialProgress(
                number=0,
                total_trials=2,
                state="COMPLETE",
                value=0.2,
                best_epoch=2,
            )
        )
        callbacks.on_trial_complete(
            TuningTrialProgress(
                number=1,
                total_trials=2,
                state="COMPLETE",
                value=0.35,
                best_epoch=3,
            )
        )
        return object()

    monkeypatch.setattr(tune_workflow, "run_tuning_execution", fake_run_tuning_execution)
    mutations: list[str] = []

    def fake_record_study_root_mutation(*_args, mutation, **_kwargs):
        result = mutation()
        mutations.append(type(result).__name__)
        return SimpleNamespace(result=result)

    monkeypatch.setattr(
        tune_workflow,
        "record_study_root_mutation",
        fake_record_study_root_mutation,
    )
    monkeypatch.setattr(
        workflow_reporting,
        "study_result_fields",
        lambda _summary: [
            ("complete", "2"),
            ("pruned", "0"),
            ("failed", "0"),
            ("best_trial", "2"),
            ("best_value", "0.3500"),
        ],
    )

    tune_workflow.run(config, reporter=reporter)

    rendered = output.getvalue()
    assert "tune corpus=" in rendered
    assert "study started trials=2" in rendered
    assert "trial 1/2 complete value=0.2000 best_epoch=2" in rendered
    assert "trial 2/2 complete value=0.3500 best_epoch=3" in rendered
    assert "tune complete" in rendered
    assert mutations == ["SimpleNamespace", "object"]
    assert "fit epoch=" not in rendered
