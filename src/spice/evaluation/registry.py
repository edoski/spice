"""Evaluator config coercion and contract compiler."""

from __future__ import annotations

from collections.abc import Mapping

from ..core.errors import ConfigResolutionError
from .config import EvaluatorConfig, PoissonReplayEvaluatorConfig
from .contracts import CompiledEvaluatorContract
from .replay import compile_poisson_replay_evaluator_contract


def coerce_evaluator_config(
    payload: Mapping[str, object] | EvaluatorConfig,
) -> EvaluatorConfig:
    if isinstance(payload, EvaluatorConfig):
        raw_payload = payload.model_dump(mode="json")
    elif isinstance(payload, Mapping):
        raw_payload = dict(payload)
    else:
        raise ConfigResolutionError("evaluation must be a mapping or config model")
    try:
        return PoissonReplayEvaluatorConfig.model_validate(raw_payload)
    except ValueError as exc:
        raise ConfigResolutionError(str(exc)) from exc


def compile_evaluator_contract(
    evaluator_config: EvaluatorConfig,
) -> CompiledEvaluatorContract:
    if not isinstance(evaluator_config, PoissonReplayEvaluatorConfig):
        raise ConfigResolutionError("evaluation config must be poisson_replay_2h")
    return compile_poisson_replay_evaluator_contract(evaluator_config)
