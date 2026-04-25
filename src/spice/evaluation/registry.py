"""Evaluator config coercion and contract registry."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from ..core.errors import ConfigResolutionError
from ..core.specs import lookup_local_spec, require_spec_config
from .anchor_basefee import compile_anchor_basefee_evaluator_contract
from .config import (
    AnchorBasefeeEvaluatorConfig,
    EvaluatorConfig,
    ReplayEvaluatorConfig,
    ZeroStopRolloutEvaluatorConfig,
)
from .contracts import CompiledEvaluatorContract
from .replay import compile_replay_evaluator_contract
from .zero_stop_rollout import compile_zero_stop_rollout_evaluator_contract


@dataclass(frozen=True, slots=True)
class EvaluatorSpec:
    config_type: type[EvaluatorConfig]
    compile_contract: Callable[[Any], CompiledEvaluatorContract]


_EVALUATOR_SPECS: dict[str, EvaluatorSpec] = {
    "replay": EvaluatorSpec(
        config_type=ReplayEvaluatorConfig,
        compile_contract=compile_replay_evaluator_contract,
    ),
    "zero_stop_rollout": EvaluatorSpec(
        config_type=ZeroStopRolloutEvaluatorConfig,
        compile_contract=compile_zero_stop_rollout_evaluator_contract,
    ),
    "anchor_basefee": EvaluatorSpec(
        config_type=AnchorBasefeeEvaluatorConfig,
        compile_contract=compile_anchor_basefee_evaluator_contract,
    ),
}


def evaluator_spec(engine: str) -> EvaluatorSpec:
    return lookup_local_spec(_EVALUATOR_SPECS, engine, "evaluation.engine")


def coerce_evaluator_config(
    payload: Mapping[str, object] | EvaluatorConfig,
) -> EvaluatorConfig:
    if isinstance(payload, EvaluatorConfig):
        raw_payload = payload.model_dump(mode="json", exclude_none=True)
        engine = payload.engine
    elif isinstance(payload, Mapping):
        raw_payload = dict(payload)
        raw_engine = raw_payload.get("engine")
        if not isinstance(raw_engine, str):
            raise ConfigResolutionError("evaluation.engine is required")
        if not raw_engine:
            raise ConfigResolutionError("evaluation.engine must be a non-empty string")
        engine = raw_engine
    else:
        raise ConfigResolutionError("evaluation must be a mapping or config model")
    try:
        return evaluator_spec(engine).config_type.model_validate(raw_payload)
    except ValueError as exc:
        raise ConfigResolutionError(str(exc)) from exc


def compile_evaluator_contract(
    evaluator_config: EvaluatorConfig,
) -> CompiledEvaluatorContract:
    spec = evaluator_spec(evaluator_config.engine)
    config = require_spec_config(
        evaluator_config,
        spec.config_type,
        "evaluation config",
    )
    return spec.compile_contract(config)
