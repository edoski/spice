"""Optuna tuning workflow."""

from __future__ import annotations

import shutil

import optuna
from optuna.trial import FrozenTrial, TrialState

from ..config import TuneConfig
from ..core.console import ConsoleRuntime, Reporter
from ..core.files import remove_path
from ..core.json import write_json
from ..modeling.execution import run_persisted_training
from ..modeling.registry import sample_tuned_parameters
from ._shared import (
    abort_cleanup,
    build_training_spec,
    epoch_metrics_to_dict,
    managed_workflow,
    trial_artifact_dir,
)
from ._tuning import (
    apply_tuned_parameters,
    build_best_params_report,
    build_study_report,
    build_trial_record,
    flatten_tuned_parameters,
    freeze_tuned_parameters_for_trial,
)


def _chain_label(chain_name: str) -> str:
    return chain_name.replace("_", " ").title()


def _format_best_params(params) -> str:
    flattened = flatten_tuned_parameters(params)
    if not flattened:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in flattened.items())


def _trial_status_message(trial: FrozenTrial) -> str:
    if trial.state == TrialState.COMPLETE:
        assert trial.value is not None
        return f"trial {trial.number + 1} complete: value={trial.value:.4f}"
    if trial.state == TrialState.PRUNED:
        return f"trial {trial.number + 1} pruned"
    return f"trial {trial.number + 1} failed"


def _objective(
    base_config: TuneConfig,
    trial: optuna.Trial,
    *,
    runtime: ConsoleRuntime,
    reporter: Reporter,
) -> float:
    assert base_config.tuning_space is not None
    params = sample_tuned_parameters(trial, tuning_space=base_config.tuning_space)
    freeze_tuned_parameters_for_trial(trial, params)
    config = apply_tuned_parameters(base_config, params)

    spec = build_training_spec(config)
    artifact_dir = trial_artifact_dir(config, trial.number)
    history_block_path = config.paths.history_dir
    with managed_workflow(
        config,
        run_name=f"trial-{trial.number:03d}",
        runtime=runtime,
        reporter=reporter,
        nested=True,
    ) as session:
        persisted = run_persisted_training(
            history_block_path,
            spec=spec,
            artifact_dir=artifact_dir,
            report_path=artifact_dir / "train_report.json",
            reporter=session.reporter,
            runtime=session.runtime,
        )
        metric_map = epoch_metrics_to_dict(persisted.best_validation_metrics)
        metric_value = metric_map[config.tuning.objective_metric.metric_name]
        trial.set_user_attr("best_epoch", persisted.training_run.training_result.best_epoch)
        trial.set_user_attr("artifact_dir", str(artifact_dir))
        if config.tuning.enable_pruning:
            trial.report(metric_value, step=persisted.training_run.training_result.best_epoch)
            if trial.should_prune():
                raise optuna.TrialPruned()
        return metric_value


def run(config: TuneConfig, *, reporter: Reporter | None = None) -> None:
    with managed_workflow(
        config,
        run_name=(
            "study-"
            f"{config.chain.name.value}-{config.model.id}-"
            f"{config.dataset.temporal.max_delay_seconds}s"
        ),
        reporter=reporter,
    ) as session:
        artifact_root = config.paths.artifact_root
        tuning_root = config.paths.tuning_root
        best_params_path = config.paths.tuning_best_params_path
        if artifact_root is None or tuning_root is None or best_params_path is None:
            raise ValueError("tuning workflow requires artifact output paths")
        with abort_cleanup(
            session.reporter,
            label="tune",
            cleanup=lambda: remove_path(artifact_root),
        ):
            if artifact_root.exists():
                shutil.rmtree(artifact_root)
            study_task = session.reporter.start_task(
                "tune study",
                total=config.tuning.trial_count,
                unit="trials",
            )

            def on_trial_complete(study: optuna.Study, frozen_trial: FrozenTrial) -> None:
                session.reporter.update_task(
                    study_task,
                    completed=frozen_trial.number + 1,
                    message=_trial_status_message(frozen_trial),
                )

            with session.runtime.optuna_logging():
                study = optuna.create_study(
                    study_name=config.study.id,
                    direction=config.tuning.direction,
                    pruner=(
                        optuna.pruners.MedianPruner()
                        if config.tuning.enable_pruning
                        else optuna.pruners.NopPruner()
                    ),
                    sampler=optuna.samplers.TPESampler(seed=config.tuning.sampler_seed),
                )
                study.optimize(
                    lambda trial: _objective(
                        config,
                        trial,
                        runtime=session.runtime,
                        reporter=session.reporter,
                    ),
                    n_trials=config.tuning.trial_count,
                    timeout=config.tuning.timeout_seconds,
                    callbacks=[on_trial_complete],
                )
            study_path = tuning_root / "study.json"
            trials_path = tuning_root / "trials.json"
            study_report = build_study_report(config, study)
            trial_records = [build_trial_record(trial) for trial in study.trials]
            write_task = session.reporter.start_task("write tuning summary")
            write_json(study_path, study_report)
            write_json(trials_path, tuple(trial_records))
            write_json(best_params_path, build_best_params_report(config, study))
            session.reporter.finish_task(write_task, message=str(best_params_path), silent=True)
            completed_trials = [
                trial for trial in study.trials if trial.state == TrialState.COMPLETE
            ]
            if completed_trials:
                session.reporter.finish_task(
                    study_task,
                    message=f"best_value={study.best_value:.4f}",
                )
            else:
                session.reporter.finish_task(study_task, message="no successful trials")
            best_trial = study_report.best_trial
            session.runtime.log_sectioned_summary(
                "tuning summary",
                [
                    (
                        "study",
                        [
                            ("id", study_report.study.id),
                            ("chain", _chain_label(study_report.chain.value)),
                            ("model", study_report.model_id),
                            ("trials", str(study_report.trial_counts.total)),
                        ],
                    ),
                    (
                        "best trial",
                        [
                            ("objective", study_report.objective_metric.value),
                            (
                                "value",
                                "n/a"
                                if best_trial is None or best_trial.value is None
                                else f"{best_trial.value:.4f}",
                            ),
                            (
                                "trial",
                                "n/a" if best_trial is None else str(best_trial.number + 1),
                            ),
                            (
                                "params",
                                "n/a"
                                if best_trial is None
                                else _format_best_params(best_trial.params),
                            ),
                        ],
                    ),
                    (
                        "artifacts",
                        [
                            ("study", str(study_path)),
                            ("best params", str(best_params_path)),
                        ],
                    ),
                ],
            )
