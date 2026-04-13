"""Open registry for problem compiler specs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from .base import ProblemCompilerConfig, ProblemCompilerSpec

_PROBLEM_COMPILER_SPECS: dict[str, ProblemCompilerSpec[Any]] = {}
_BUILTINS_LOADED = False


def register_problem_compiler_spec(spec: ProblemCompilerSpec[Any]) -> None:
    existing = _PROBLEM_COMPILER_SPECS.get(spec.id)
    if existing is not None:
        raise ValueError(f"Duplicate problem compiler spec id: {spec.id}")
    _PROBLEM_COMPILER_SPECS[spec.id] = spec


def _ensure_builtin_problem_compilers_loaded() -> None:
    global _BUILTINS_LOADED
    if _BUILTINS_LOADED:
        return
    from . import estimated_block, timestamp_native  # noqa: F401

    _BUILTINS_LOADED = True


def problem_compiler_spec(compiler_id: str) -> ProblemCompilerSpec[Any]:
    _ensure_builtin_problem_compilers_loaded()
    try:
        return _PROBLEM_COMPILER_SPECS[compiler_id]
    except KeyError as exc:
        known = ", ".join(sorted(_PROBLEM_COMPILER_SPECS))
        raise ValueError(
            f"Unknown problem.compiler.id: {compiler_id}. Known compilers: {known}"
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
        raise ValueError("problem.compiler.id is required")
    return cast(str, value)
