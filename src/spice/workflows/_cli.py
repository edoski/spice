"""Shared CLI helpers for workflow entrypoints."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..core.config import ExperimentConfig, WorkflowTask, load_params_config


def load_cli_config(
    task: WorkflowTask | str,
    *,
    prog: str,
    argv: list[str] | None = None,
) -> ExperimentConfig:
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument("--params", type=Path, default=Path("params.yaml"))
    parser.add_argument("overrides", nargs="*")
    args = parser.parse_args(argv)
    return load_params_config(task, params_path=args.params, overrides=args.overrides)
