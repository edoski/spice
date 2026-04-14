"""Open registry for problem compiler specs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from ...core.components import ComponentCatalog
from ...core.errors import ConfigResolutionError
from .base import ProblemCompilerConfig, ProblemCompilerSpec

_PROBLEM_COMPILER_SPECS = ComponentCatalog[ProblemCompilerSpec[Any]](
    kind_label="problem compiler",
    entry_point_group="spice.problem_compilers",
)


def register_problem_compiler_spec(spec: ProblemCompilerSpec[Any]) -> None:
    _PROBLEM_COMPILER_SPECS.register(spec.id, spec)


def _load_builtin_problem_compilers() -> None:
    from . import estimated_block, timestamp_native  # noqa: F401


_PROBLEM_COMPILER_SPECS.configure_builtin_loader(_load_builtin_problem_compilers)


def problem_compiler_spec(compiler_id: str) -> ProblemCompilerSpec[Any]:
    try:
        return _PROBLEM_COMPILER_SPECS.get(compiler_id)
    except ConfigResolutionError as exc:
        raise ConfigResolutionError(
            str(exc).replace("problem compiler", "problem.compiler.id")
        ) from exc


def coerce_problem_compiler_config(
    payload: Mapping[str, object] | ProblemCompilerConfig,
) -> ProblemCompilerConfig:
    if isinstance(payload, ProblemCompilerConfig):
        raw_payload = payload.model_dump(mode="json")
        compiler_id = payload.id
    else:
        raw_payload = dict(payload)
        compiler_id = _mapping_problem_compiler_id(raw_payload)
    spec = problem_compiler_spec(compiler_id)
    return spec.config_type.model_validate(raw_payload)


def _mapping_problem_compiler_id(payload: Mapping[str, object]) -> str:
    value = payload.get("id")
    if not isinstance(value, str):
        raise ConfigResolutionError("problem.compiler.id is required")
    return cast(str, value)
