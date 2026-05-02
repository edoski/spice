"""Evaluator config coercion and contract compiler."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from ..core.specs import (
    lookup_local_spec,
    owner_payload_id,
    require_spec_config,
    validate_owner_config,
)
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
    payload: object,
) -> EvaluatorConfig:
    raw_payload, evaluator_id = owner_payload_id(
        payload,
        owner="evaluation",
        config_type=EvaluatorConfig,
        id_label="evaluation.id",
    )
    spec = lookup_local_spec(_EVALUATOR_SPECS, evaluator_id, "evaluation.id")
    if isinstance(payload, spec.config_type):
        return payload
    return validate_owner_config(raw_payload, spec.config_type)


def compile_evaluator_contract(
    evaluator_config: EvaluatorConfig,
) -> CompiledEvaluatorContract:
    spec = lookup_local_spec(_EVALUATOR_SPECS, evaluator_config.id, "evaluation.id")
    return spec.compile_contract(evaluator_config)


def _require_config(
    config: EvaluatorConfig,
    config_type: type[EvaluatorConfigT],
) -> EvaluatorConfigT:
    return require_spec_config(config, config_type, "evaluation config")
