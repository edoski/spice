"""Direct problem-compiler dispatch for the fixed in-repo compilers."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from ...core.specs import lookup_local_spec, require_mapping_id
from .base import ProblemCompilerConfig

if TYPE_CHECKING:
    from ...config.models import ChainRuntimeSpec, ProblemSpec
    from ...features import CompiledFeatureContract
    from ..contracts import CompiledProblemContract
    from ..realization import CompiledRealizationPolicyContract


class CompileProblemFn(Protocol):
    def __call__(
        self,
        problem: ProblemSpec,
        feature_contract: CompiledFeatureContract,
        realization_policy: CompiledRealizationPolicyContract,
        chain_runtime: ChainRuntimeSpec | None,
    ) -> CompiledProblemContract: ...


@dataclass(frozen=True, slots=True)
class ProblemCompilerSpec:
    config_type: type[ProblemCompilerConfig]
    compile_problem: CompileProblemFn
    runtime_metadata_payload: Callable[[object], dict[str, object]]
    runtime_metadata_from_payload: Callable[[Mapping[str, object]], object]


def _compile_timestamp_future_window(
    problem: ProblemSpec,
    feature_contract: CompiledFeatureContract,
    realization_policy: CompiledRealizationPolicyContract,
    chain_runtime: ChainRuntimeSpec | None,
) -> CompiledProblemContract:
    from .timestamp_future_window import compile_problem

    return compile_problem(
        problem,
        feature_contract,
        realization_policy,
        chain_runtime,
    )


def _compile_estimated_block(
    problem: ProblemSpec,
    feature_contract: CompiledFeatureContract,
    realization_policy: CompiledRealizationPolicyContract,
    chain_runtime: ChainRuntimeSpec | None,
) -> CompiledProblemContract:
    from .estimated_block import compile_problem

    return compile_problem(
        problem,
        feature_contract,
        realization_policy,
        chain_runtime,
    )


def _timestamp_future_window_runtime_metadata_payload(metadata: object) -> dict[str, object]:
    from .timestamp_future_window import runtime_metadata_payload

    return runtime_metadata_payload(metadata)


def _estimated_block_runtime_metadata_payload(metadata: object) -> dict[str, object]:
    from .estimated_block import runtime_metadata_payload

    return runtime_metadata_payload(metadata)


def _timestamp_future_window_runtime_metadata_from_payload(
    payload: Mapping[str, object],
) -> object:
    from .timestamp_future_window import runtime_metadata_from_payload

    return runtime_metadata_from_payload(payload)


def _estimated_block_runtime_metadata_from_payload(payload: Mapping[str, object]) -> object:
    from .estimated_block import runtime_metadata_from_payload

    return runtime_metadata_from_payload(payload)


def _problem_compiler_specs() -> dict[str, ProblemCompilerSpec]:
    from .estimated_block import EstimatedBlockCompilerConfig
    from .timestamp_future_window import TimestampFutureWindowCompilerConfig

    return {
        "timestamp_future_window": ProblemCompilerSpec(
            config_type=TimestampFutureWindowCompilerConfig,
            compile_problem=_compile_timestamp_future_window,
            runtime_metadata_payload=_timestamp_future_window_runtime_metadata_payload,
            runtime_metadata_from_payload=_timestamp_future_window_runtime_metadata_from_payload,
        ),
        "estimated_block": ProblemCompilerSpec(
            config_type=EstimatedBlockCompilerConfig,
            compile_problem=_compile_estimated_block,
            runtime_metadata_payload=_estimated_block_runtime_metadata_payload,
            runtime_metadata_from_payload=_estimated_block_runtime_metadata_from_payload,
        ),
    }


def problem_compiler_spec(compiler_id: str) -> ProblemCompilerSpec:
    return lookup_local_spec(
        _problem_compiler_specs(),
        compiler_id,
        "problem.compiler.id",
    )


def coerce_problem_compiler_config(
    payload: Mapping[str, object] | ProblemCompilerConfig,
) -> ProblemCompilerConfig:
    if isinstance(payload, ProblemCompilerConfig):
        raw_payload = payload.model_dump(mode="json")
        compiler_id = payload.id
    else:
        raw_payload = dict(payload)
        compiler_id = require_mapping_id(raw_payload, "problem.compiler.id")
    return problem_compiler_spec(compiler_id).config_type.model_validate(raw_payload)


def compile_problem(
    problem: ProblemSpec,
    feature_contract: CompiledFeatureContract,
    realization_policy: CompiledRealizationPolicyContract,
    chain_runtime: ChainRuntimeSpec | None,
) -> CompiledProblemContract:
    compiler_id = problem.compiler.id
    return problem_compiler_spec(compiler_id).compile_problem(
        problem,
        feature_contract,
        realization_policy,
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
