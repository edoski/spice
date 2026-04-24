"""Current-row realized-window problem compiler."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import ceil
from typing import TYPE_CHECKING

from ...core.errors import ConfigResolutionError
from ...features import (
    CompiledFeatureContract,
    ResolvedFeatureTable,
)
from ..contracts import CompiledProblemContract
from ..problem_store import CompiledProblemStore
from ..realization import CompiledRealizationPolicyContract
from ..semantics import ActionSpaceMode, CandidateStartMode
from ._shared import build_timestamp_window_store
from .base import ProblemCompilerConfig

if TYPE_CHECKING:
    from ...config.models import ChainRuntimeSpec, ProblemSpec


class CurrentRowWindowCompilerConfig(ProblemCompilerConfig):
    id: str = "current_row_window"


@dataclass(frozen=True, slots=True)
class CurrentRowWindowRuntimeMetadata:
    pass


@dataclass(frozen=True, slots=True)
class CurrentRowWindowCompiledProblemContract(CompiledProblemContract):
    def initial_history_window_seconds(self, recent_block_interval_seconds: float | None) -> int:
        minimum_window = self.required_history_seconds + self.max_delay_seconds
        if recent_block_interval_seconds is None or recent_block_interval_seconds <= 0:
            return minimum_window
        warmup_seconds = ceil(self.warmup_rows * recent_block_interval_seconds)
        return max(
            minimum_window,
            self.required_history_seconds
            + self.max_delay_seconds
            + warmup_seconds
            + ceil(self.sample_count * recent_block_interval_seconds),
        )

    def count_valid_capability_samples(self, feature_table: ResolvedFeatureTable) -> int:
        store, _ = self.build_capability_store(feature_table)
        return store.n_samples

    def build_capability_store(
        self,
        feature_table: ResolvedFeatureTable,
    ) -> tuple[CompiledProblemStore, CurrentRowWindowRuntimeMetadata]:
        return (
            build_timestamp_window_store(
                feature_table,
                feature_prerequisites=self.feature_prerequisites,
                lookback_seconds=self.lookback_seconds,
                delay_seconds=self.max_delay_seconds,
                candidate_start_mode=self.candidate_start_mode,
                action_space_mode=self.action_space_mode,
                requires_post_window_row=self.realization_policy.requires_post_window_row,
            ),
            CurrentRowWindowRuntimeMetadata(),
        )

    def build_delay_store(
        self,
        feature_table: ResolvedFeatureTable,
        delay_seconds: int,
        *,
        compiler_runtime_metadata: object,
        max_candidate_slots: int,
    ) -> CompiledProblemStore:
        if not isinstance(compiler_runtime_metadata, CurrentRowWindowRuntimeMetadata):
            raise TypeError("current_row_window requires CurrentRowWindowRuntimeMetadata")
        if delay_seconds <= 0:
            raise ValueError("delay_seconds must be positive")
        if delay_seconds > self.max_delay_seconds:
            raise ValueError(
                "delay_seconds exceeds problem capability: "
                f"{delay_seconds} > {self.max_delay_seconds}"
            )
        return build_timestamp_window_store(
            feature_table,
            feature_prerequisites=self.feature_prerequisites,
            lookback_seconds=self.lookback_seconds,
            delay_seconds=delay_seconds,
            candidate_start_mode=self.candidate_start_mode,
            action_space_mode=self.action_space_mode,
            max_candidate_slots=max_candidate_slots,
            requires_post_window_row=self.realization_policy.requires_post_window_row,
        )


def runtime_metadata_payload(metadata: object) -> dict[str, object]:
    if not isinstance(metadata, CurrentRowWindowRuntimeMetadata):
        raise TypeError("current_row_window requires CurrentRowWindowRuntimeMetadata")
    return {}


def runtime_metadata_from_payload(payload: Mapping[str, object]) -> CurrentRowWindowRuntimeMetadata:
    if dict(payload):
        raise ConfigResolutionError(
            "current_row_window runtime metadata must be empty in artifact manifests"
        )
    return CurrentRowWindowRuntimeMetadata()


def compile_problem(
    problem: ProblemSpec,
    feature_contract: CompiledFeatureContract,
    realization_policy: CompiledRealizationPolicyContract,
    chain_runtime: ChainRuntimeSpec | None,
) -> CompiledProblemContract:
    del chain_runtime
    return CurrentRowWindowCompiledProblemContract(
        compiler_id="current_row_window",
        problem_id=problem.id,
        feature_set_id=feature_contract.feature_set_id,
        feature_family_id=feature_contract.feature_family_id,
        lookback_seconds=problem.lookback_seconds,
        sample_count=problem.sample_count,
        max_delay_seconds=problem.max_delay_seconds,
        feature_prerequisites=feature_contract.feature_prerequisites,
        realization_policy=realization_policy,
        candidate_start_mode=CandidateStartMode.CURRENT_ROW,
        action_space_mode=ActionSpaceMode.REALIZED_PER_SAMPLE,
    )
