"""Evaluator config coercion and contract compiler."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TypeVar

from ..core.errors import ConfigResolutionError
from .config import (
    EvaluatorConfig,
    FullTemporalReplayEvaluatorConfig,
    PoissonReplayEvaluatorConfig,
)
from .contracts import CompiledEvaluatorContract
from .full_temporal_replay import compile_full_temporal_replay_evaluator_contract
from .poisson_replay import compile_poisson_replay_evaluator_contract

EvaluatorConfigT = TypeVar("EvaluatorConfigT", bound=EvaluatorConfig)


@dataclass(frozen=True, slots=True)
class _EvaluatorSpec:
    config_type: type[EvaluatorConfig]
    compile_contract: Callable[[EvaluatorConfig], CompiledEvaluatorContract]


_EVALUATOR_SPECS: dict[str, _EvaluatorSpec] = {
    "poisson_replay_2h": _EvaluatorSpec(
        config_type=PoissonReplayEvaluatorConfig,
        compile_contract=lambda config: compile_poisson_replay_evaluator_contract(
            _require_config(config, PoissonReplayEvaluatorConfig)
        ),
    ),
    "full_temporal_replay": _EvaluatorSpec(
        config_type=FullTemporalReplayEvaluatorConfig,
        compile_contract=lambda config: compile_full_temporal_replay_evaluator_contract(
            _require_config(config, FullTemporalReplayEvaluatorConfig)
        ),
    ),
}


def coerce_evaluator_config(
    payload: Mapping[str, object] | EvaluatorConfig,
) -> EvaluatorConfig:
    if isinstance(payload, EvaluatorConfig):
        raw_payload = payload.model_dump(mode="json")
    elif isinstance(payload, Mapping):
        raw_payload = dict(payload)
    else:
        raise ConfigResolutionError("evaluation must be a mapping or config model")
    evaluator_id = raw_payload.get("id")
    if not isinstance(evaluator_id, str):
        raise ConfigResolutionError("evaluation.id must be a string")
    spec = _EVALUATOR_SPECS.get(evaluator_id)
    if spec is None:
        raise ConfigResolutionError(
            "unknown evaluation.id "
            f"{evaluator_id}; expected one of: {', '.join(_EVALUATOR_SPECS)}"
        )
    try:
        return spec.config_type.model_validate(raw_payload)
    except ValueError as exc:
        raise ConfigResolutionError(str(exc)) from exc


def compile_evaluator_contract(
    evaluator_config: EvaluatorConfig,
) -> CompiledEvaluatorContract:
    spec = _EVALUATOR_SPECS.get(evaluator_config.id)
    if spec is None:
        raise ConfigResolutionError(
            "unknown evaluation.id "
            f"{evaluator_config.id}; expected one of: {', '.join(_EVALUATOR_SPECS)}"
        )
    return spec.compile_contract(evaluator_config)


def _require_config(
    config: EvaluatorConfig,
    config_type: type[EvaluatorConfigT],
) -> EvaluatorConfigT:
    if not isinstance(config, config_type):
        raise ConfigResolutionError(
            f"evaluation config {config.id} must be {config_type.__name__}"
        )
    return config
