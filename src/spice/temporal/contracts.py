"""Compiled problem contracts shared across workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..config.models import FeatureSetConfig, ProblemSpec
from ..features import FeaturePrerequisites

if TYPE_CHECKING:
    from ..features import FeatureSelection, ResolvedFeatureTable
    from .compilers import CompilerRuntimeMetadata
    from .problem_store import CompiledProblemStore


@dataclass(frozen=True, slots=True)
class CompiledProblemContract:
    compiler_id: str
    problem_id: str
    feature_set_id: str
    feature_family_id: str
    lookback_seconds: int
    sample_count: int
    max_supported_delay_seconds: int
    feature_prerequisites: FeaturePrerequisites

    @property
    def required_history_seconds(self) -> int:
        return self.lookback_seconds + self.feature_prerequisites.history_seconds

    @property
    def warmup_rows(self) -> int:
        return self.feature_prerequisites.warmup_rows

    def initial_history_window_seconds(self, recent_block_interval_seconds: float | None) -> int:
        raise NotImplementedError

    def count_valid_capability_samples(self, feature_table: ResolvedFeatureTable) -> int:
        raise NotImplementedError

    def build_capability_store(
        self,
        feature_table: ResolvedFeatureTable,
    ) -> tuple[CompiledProblemStore, CompilerRuntimeMetadata]:
        raise NotImplementedError

    def build_requested_delay_store(
        self,
        feature_table: ResolvedFeatureTable,
        requested_delay_seconds: int,
        *,
        compiler_runtime_metadata: CompilerRuntimeMetadata,
        max_candidate_slots: int,
    ) -> CompiledProblemStore:
        raise NotImplementedError


def resolve_feature_contract(
    *,
    problem: ProblemSpec,
    selection: FeatureSelection,
) -> CompiledProblemContract:
    from .compilers.registry import problem_compiler_spec

    return problem_compiler_spec(problem.compiler.id).compile_problem(
        problem,
        selection,
    )


def resolve_problem_contract(
    *,
    problem: ProblemSpec,
    feature_set: FeatureSetConfig,
) -> CompiledProblemContract:
    from ..features import make_feature_selection

    return resolve_feature_contract(
        problem=problem,
        selection=make_feature_selection(
            feature_set_id=feature_set.id,
            feature_family_id=feature_set.family.id,
            feature_names=tuple(feature_set.outputs),
        ),
    )
