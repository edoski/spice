"""Derived timestamp-native problem contracts shared across workflows."""

from __future__ import annotations

from dataclasses import dataclass

from ..config.models import FeatureSetConfig, ProblemSpec
from ..features import feature_history_seconds
from .window import DelayWindow


@dataclass(frozen=True, slots=True)
class ProblemContract:
    problem_id: str
    feature_set_id: str
    lookback_seconds: int
    sample_count: int
    max_supported_delay_seconds: int
    feature_history_seconds: int

    @property
    def required_history_seconds(self) -> int:
        return self.lookback_seconds + self.feature_history_seconds

    @property
    def capability_window(self) -> DelayWindow:
        return DelayWindow(
            lookback_seconds=self.lookback_seconds,
            delay_seconds=self.max_supported_delay_seconds,
            feature_history_seconds=self.feature_history_seconds,
        )

    def window_for_delay(self, requested_delay_seconds: int) -> DelayWindow:
        if requested_delay_seconds <= 0:
            raise ValueError("requested_delay_seconds must be positive")
        if requested_delay_seconds > self.max_supported_delay_seconds:
            raise ValueError(
                "requested_delay_seconds exceeds problem capability: "
                f"{requested_delay_seconds} > {self.max_supported_delay_seconds}"
            )
        return DelayWindow(
            lookback_seconds=self.lookback_seconds,
            delay_seconds=requested_delay_seconds,
            feature_history_seconds=self.feature_history_seconds,
        )


def resolve_feature_contract(
    *,
    problem: ProblemSpec,
    feature_set_id: str,
    feature_names: tuple[str, ...],
) -> ProblemContract:
    return ProblemContract(
        problem_id=problem.id,
        feature_set_id=feature_set_id,
        lookback_seconds=problem.lookback_seconds,
        sample_count=problem.sample_count,
        max_supported_delay_seconds=problem.max_supported_delay_seconds,
        feature_history_seconds=feature_history_seconds(feature_names),
    )


def resolve_problem_contract(
    *,
    problem: ProblemSpec,
    feature_set: FeatureSetConfig,
) -> ProblemContract:
    return resolve_feature_contract(
        problem=problem,
        feature_set_id=feature_set.id,
        feature_names=tuple(feature_set.outputs),
    )
