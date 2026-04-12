"""Optuna-backed study state helpers."""

from __future__ import annotations

from pathlib import Path

import optuna
from optuna.storages import RDBStorage

from ..config import TuneConfig, TunedParameterSet
from ..modeling.registry import coerce_tuned_parameter_set
from ..workflows._tuning import (
    STUDY_CONTEXT_KEY,
    TRIAL_BEST_EPOCH_KEY,
    TRIAL_PARAMS_KEY,
    TuningStudySummary,
    TuningTrialRecord,
    build_study_summary,
    build_trial_record,
    study_context_payload,
)
from .engine import STUDY_ROOT_KIND, db_url, ensure_state_db


def study_storage(db_path: Path) -> RDBStorage:
    return RDBStorage(
        url=db_url(db_path),
        engine_kwargs={"connect_args": {"timeout": 5}},
    )


def create_or_load_study(db_path: Path, *, config: TuneConfig) -> optuna.Study:
    ensure_state_db(db_path, root_kind=STUDY_ROOT_KIND, tables=())
    study = optuna.create_study(
        study_name=config.study.name,
        storage=study_storage(db_path),
        direction=config.tuning.direction,
        load_if_exists=True,
        sampler=optuna.samplers.TPESampler(seed=config.tuning.sampler_seed),
        pruner=(
            optuna.pruners.MedianPruner()
            if config.tuning.enable_pruning
            else optuna.pruners.NopPruner()
        ),
    )
    study.set_user_attr(STUDY_CONTEXT_KEY, study_context_payload(config))
    return study


def load_study(db_path: Path, *, study_name: str) -> optuna.Study:
    ensure_state_db(db_path, root_kind=STUDY_ROOT_KIND, tables=())
    return optuna.load_study(study_name=study_name, storage=study_storage(db_path))


def load_best_params(
    db_path: Path,
    *,
    study_name: str,
    model_id: str,
) -> TunedParameterSet:
    study = load_study(db_path, study_name=study_name)
    payload = study.best_trial.user_attrs.get(TRIAL_PARAMS_KEY)
    if not isinstance(payload, dict):
        raise FileNotFoundError(f"Best tuning params are required but missing: {db_path}")
    return coerce_tuned_parameter_set(payload, model_id=model_id)


def load_study_summary(db_path: Path, *, config: TuneConfig) -> TuningStudySummary:
    study = load_study(db_path, study_name=config.study.name)
    return build_study_summary(config, study)


def list_trial_records(db_path: Path, *, study_name: str, model_id: str) -> list[TuningTrialRecord]:
    study = load_study(db_path, study_name=study_name)
    return [build_trial_record(trial, model_id=model_id) for trial in study.trials]


def study_payload(db_path: Path, *, study_name: str, model_id: str) -> dict[str, object]:
    study = load_study(db_path, study_name=study_name)
    context = study.user_attrs.get(STUDY_CONTEXT_KEY)
    try:
        best_value = study.best_value
        best_trial_number = study.best_trial.number
    except ValueError:
        best_value = None
        best_trial_number = None
    payload: dict[str, object] = {
        "study_name": study.study_name,
        "direction": study.direction.name,
        "best_value": best_value,
        "best_trial_number": best_trial_number,
        "spice_context": context if isinstance(context, dict) else None,
        "trials": [
            {
                "number": trial.number,
                "state": trial.state.name,
                "value": trial.value,
                "best_epoch": trial.user_attrs.get(TRIAL_BEST_EPOCH_KEY),
                "params": coerce_tuned_parameter_set(
                    trial.user_attrs.get(TRIAL_PARAMS_KEY, {}),
                    model_id=model_id,
                ).model_dump(mode="json", exclude_none=True)
                if isinstance(trial.user_attrs.get(TRIAL_PARAMS_KEY), dict)
                else None,
            }
            for trial in study.trials
        ],
    }
    return payload
