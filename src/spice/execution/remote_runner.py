"""Run one resolved workflow config inside the remote execution environment."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping

from ..config.models import (
    ArtifactConfig,
    ChainSpec,
    DatasetSpec,
    EvaluateConfig,
    PredictionConfig,
    SplitConfig,
    StorageSpec,
    StudyConfig,
    TrainConfig,
    TrainingConfig,
    TuneConfig,
    TuningConfig,
    WorkflowTask,
    coerce_feature_set_config,
    coerce_problem_spec,
)
from ..config.resolution import WorkflowConfig
from ..evaluation import EvaluatorConfig
from ..modeling.dataset_builders import coerce_dataset_builder_config
from ..modeling.families.registry import coerce_model_config
from ..modeling.tuned_config import coerce_tuning_space_config
from ..objectives import coerce_objective_config


def run_remote_workflow(task: WorkflowTask, config: WorkflowConfig) -> None:
    if task is WorkflowTask.TRAIN:
        from ..workflows import train

        if not isinstance(config, TrainConfig):
            raise TypeError("remote train requires TrainConfig")
        train.run(config)
        return
    if task is WorkflowTask.TUNE:
        from ..workflows import tune

        if not isinstance(config, TuneConfig):
            raise TypeError("remote tune requires TuneConfig")
        tune.run(config)
        return
    if task is WorkflowTask.EVALUATE:
        from ..workflows import evaluate

        if not isinstance(config, EvaluateConfig):
            raise TypeError("remote evaluate requires EvaluateConfig")
        evaluate.run(config)
        return
    raise ValueError(f"Unsupported remote workflow: {task.value}")


def workflow_config_from_json(task: WorkflowTask, payload: str) -> WorkflowConfig:
    raw_payload = json.loads(payload)
    if not isinstance(raw_payload, Mapping):
        raise TypeError("resolved workflow snapshot must be a mapping")
    resolved_payload = _model_workflow_payload(raw_payload)
    if task is WorkflowTask.TRAIN:
        return TrainConfig.model_validate(resolved_payload)
    if task is WorkflowTask.TUNE:
        return TuneConfig.model_validate(resolved_payload)
    if task is WorkflowTask.EVALUATE:
        return EvaluateConfig.model_validate(resolved_payload)
    raise ValueError(f"Unsupported remote workflow: {task.value}")


def _model_workflow_payload(payload: Mapping[str, object]) -> dict[str, object]:
    raw = dict(payload)
    problem = coerce_problem_spec(_mapping_field(raw, "problem"))
    model = coerce_model_config(_mapping_field(raw, "model"))
    tuning_space_payload = raw.get("tuning_space")
    tuning_space = (
        None
        if tuning_space_payload is None
        else coerce_tuning_space_config(
            _mapping_value(tuning_space_payload, label="tuning_space"),
            model_config=model,
            problem_config=problem,
        )
    )
    return {
        **raw,
        "chain": ChainSpec.model_validate(_mapping_field(raw, "chain")),
        "dataset": DatasetSpec.model_validate(_mapping_field(raw, "dataset")),
        "storage": StorageSpec.model_validate(_mapping_field(raw, "storage")),
        "problem": problem,
        "model": model,
        "dataset_builder": coerce_dataset_builder_config(
            _mapping_field(raw, "dataset_builder")
        ),
        "feature_set": coerce_feature_set_config(_mapping_field(raw, "feature_set")),
        "prediction": PredictionConfig.model_validate(_mapping_field(raw, "prediction")),
        "objective": coerce_objective_config(_mapping_field(raw, "objective")),
        "evaluation": _optional_evaluation(raw.get("evaluation")),
        "study": StudyConfig.model_validate(_mapping_field(raw, "study")),
        "artifact": ArtifactConfig.model_validate(_mapping_field(raw, "artifact")),
        "split": SplitConfig.model_validate(_mapping_field(raw, "split")),
        "training": TrainingConfig.model_validate(_mapping_field(raw, "training")),
        "tuning": _optional_tuning(raw.get("tuning")),
        "tuning_space": tuning_space,
    }


def _optional_evaluation(payload: object) -> EvaluatorConfig | None:
    if payload is None:
        return None
    return EvaluatorConfig.model_validate(_mapping_value(payload, label="evaluation"))


def _optional_tuning(payload: object) -> TuningConfig | None:
    if payload is None:
        return None
    return TuningConfig.model_validate(_mapping_value(payload, label="tuning"))


def _mapping_field(payload: Mapping[str, object], key: str) -> Mapping[str, object]:
    return _mapping_value(payload.get(key), label=key)


def _mapping_value(payload: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise TypeError(f"resolved workflow snapshot field {label} must be a mapping")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "task",
        choices=[
            task.value
            for task in WorkflowTask
            if task is not WorkflowTask.ACQUIRE
        ],
    )
    parser.add_argument("config_json")
    args = parser.parse_args()
    task = WorkflowTask(args.task)
    run_remote_workflow(task, workflow_config_from_json(task, args.config_json))


if __name__ == "__main__":
    main()
