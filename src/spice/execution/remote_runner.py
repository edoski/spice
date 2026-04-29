"""Run one resolved workflow config inside the remote execution environment."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping

from ..config.hydration import hydrate_model_workflow_config
from ..config.models import (
    EvaluateConfig,
    TrainConfig,
    TuneConfig,
    WorkflowTask,
)
from ..config.resolution import WorkflowConfig
from ..core.errors import ConfigResolutionError


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
        raise ConfigResolutionError("resolved workflow snapshot must be a mapping")
    return hydrate_model_workflow_config(task, raw_payload)


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
