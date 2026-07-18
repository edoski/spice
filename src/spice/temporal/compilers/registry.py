"""Legacy problem-config and runtime-metadata decoding."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from ...core.specs import coerce_spec_config, lookup_local_spec
from .base import ProblemCompilerConfig


@dataclass(frozen=True, slots=True)
class ProblemCompilerSpec:
    config_type: type[ProblemCompilerConfig]
    runtime_metadata_from_payload: Callable[[Mapping[str, object]], object]


def _observed_time_window_runtime_metadata_from_payload(
    payload: Mapping[str, object],
) -> object:
    from .observed_time_window import runtime_metadata_from_payload

    return runtime_metadata_from_payload(payload)


def _problem_compiler_specs() -> dict[str, ProblemCompilerSpec]:
    from .observed_time_window import ObservedTimeWindowCompilerConfig

    return {
        "observed_time_window": ProblemCompilerSpec(
            config_type=ObservedTimeWindowCompilerConfig,
            runtime_metadata_from_payload=(
                _observed_time_window_runtime_metadata_from_payload
            ),
        ),
    }


def problem_compiler_spec(compiler_id: str) -> ProblemCompilerSpec:
    return lookup_local_spec(
        _problem_compiler_specs(),
        compiler_id,
        "problem.compiler.id",
    )


def coerce_problem_compiler_config(payload: object) -> ProblemCompilerConfig:
    return coerce_spec_config(
        payload,
        owner="problem.compiler",
        base_config_type=ProblemCompilerConfig,
        id_label="problem.compiler.id",
        lookup_spec=problem_compiler_spec,
        spec_config_type=lambda spec: spec.config_type,
    )


def problem_runtime_metadata_from_compiler_payload(
    compiler_id: str,
    payload: Mapping[str, object],
) -> object:
    return problem_compiler_spec(compiler_id).runtime_metadata_from_payload(payload)
