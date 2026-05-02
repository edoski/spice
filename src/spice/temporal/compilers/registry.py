"""Direct problem-compiler dispatch for the fixed in-repo compilers."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from ...core.specs import (
    lookup_local_spec,
    owner_payload_id,
    require_spec_config,
    validate_owner_config,
)
from .base import ProblemCompilerConfig

if TYPE_CHECKING:
    from ...config.models import ChainRuntimeSpec, ProblemSpec
    from ...features import CompiledFeatureContract
    from ..contracts import CompiledProblemContract
    from ..execution_policy import CompiledExecutionPolicyContract


class CompileProblemFn(Protocol):
    def __call__(
        self,
        problem: ProblemSpec,
        compiler_config: ProblemCompilerConfig,
        feature_contract: CompiledFeatureContract,
        execution_policy: CompiledExecutionPolicyContract,
        chain_runtime: ChainRuntimeSpec | None,
    ) -> CompiledProblemContract: ...


@dataclass(frozen=True, slots=True)
class ProblemCompilerSpec:
    config_type: type[ProblemCompilerConfig]
    compile_problem: CompileProblemFn
    runtime_metadata_payload: Callable[[object], dict[str, object]]
    runtime_metadata_from_payload: Callable[[Mapping[str, object]], object]


def _compile_observed_time_window(
    problem: ProblemSpec,
    compiler_config: ProblemCompilerConfig,
    feature_contract: CompiledFeatureContract,
    execution_policy: CompiledExecutionPolicyContract,
    chain_runtime: ChainRuntimeSpec | None,
) -> CompiledProblemContract:
    from .observed_time_window import ObservedTimeWindowCompilerConfig, compile_problem

    return compile_problem(
        problem,
        require_spec_config(
            compiler_config,
            ObservedTimeWindowCompilerConfig,
            "problem compiler config",
        ),
        feature_contract,
        execution_policy,
        chain_runtime,
    )


def _observed_time_window_runtime_metadata_payload(metadata: object) -> dict[str, object]:
    from .observed_time_window import runtime_metadata_payload

    return runtime_metadata_payload(metadata)


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
            compile_problem=_compile_observed_time_window,
            runtime_metadata_payload=_observed_time_window_runtime_metadata_payload,
            runtime_metadata_from_payload=_observed_time_window_runtime_metadata_from_payload,
        ),
    }


def problem_compiler_spec(compiler_id: str) -> ProblemCompilerSpec:
    return lookup_local_spec(
        _problem_compiler_specs(),
        compiler_id,
        "problem.compiler.id",
    )


def coerce_problem_compiler_config(
    payload: object,
) -> ProblemCompilerConfig:
    raw_payload, compiler_id = owner_payload_id(
        payload,
        owner="problem.compiler",
        config_type=ProblemCompilerConfig,
        id_label="problem.compiler.id",
    )
    spec = problem_compiler_spec(compiler_id)
    if isinstance(payload, spec.config_type):
        return payload
    return validate_owner_config(raw_payload, spec.config_type)


def compile_problem(
    problem: ProblemSpec,
    feature_contract: CompiledFeatureContract,
    execution_policy: CompiledExecutionPolicyContract,
    chain_runtime: ChainRuntimeSpec | None,
) -> CompiledProblemContract:
    compiler_id = problem.compiler.id
    spec = problem_compiler_spec(compiler_id)
    compiler_config = require_spec_config(
        problem.compiler,
        spec.config_type,
        "problem compiler config",
    )
    return spec.compile_problem(
        problem,
        compiler_config,
        feature_contract,
        execution_policy,
        chain_runtime,
    )


def problem_runtime_metadata_payload(
    compiler_id: str,
    metadata: object,
) -> dict[str, object]:
    return problem_compiler_spec(compiler_id).runtime_metadata_payload(metadata)


def problem_runtime_metadata_from_compiler_payload(
    compiler_id: str,
    payload: Mapping[str, object],
) -> object:
    return problem_compiler_spec(compiler_id).runtime_metadata_from_payload(payload)
