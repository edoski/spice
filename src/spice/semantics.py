# pyright: strict

"""Typed seam semantics and root-level provenance bundles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .features import FeaturePrerequisites
    from .metrics import MetricDescriptor


@dataclass(frozen=True, slots=True)
class FeatureSemantics:
    """Normalized feature provenance derived once from the compiled feature contract."""

    features_id: str
    feature_names: tuple[str, ...]
    feature_graph_fingerprint: str
    feature_prerequisites: FeaturePrerequisites


@dataclass(frozen=True, slots=True)
class ProblemSemantics:
    """Normalized temporal-compiler provenance for one compiled problem contract."""

    compiler_id: str
    problem_id: str
    lookback_seconds: int
    max_delay_seconds: int


@dataclass(frozen=True, slots=True)
class ExecutionPolicySemantics:
    """Resolved execution-policy identity for persisted provenance."""

    execution_policy_id: str
    baseline_row_mode: Literal["first_candidate"]


@dataclass(frozen=True, slots=True)
class PredictionSemantics:
    """Family-owned prediction semantics that persist with studies and artifacts."""

    prediction_id: str
    prediction_family_id: str
    training_metric_descriptors: tuple[MetricDescriptor, ...]
    primary_metric_id: str
    direction: Literal["maximize", "minimize"]


@dataclass(frozen=True, slots=True)
class TemporalCapabilitySemantics:
    """Stable semantic projection of a trained artifact's temporal capability."""

    compiler_id: str
    max_delay_seconds: int
    action_width: int


@dataclass(frozen=True, slots=True)
class StudySemantics:
    """Canonical study provenance bundled from the compiled architectural seams."""

    problem: ProblemSemantics
    execution_policy: ExecutionPolicySemantics
    feature: FeatureSemantics
    prediction: PredictionSemantics


@dataclass(frozen=True, slots=True)
class ArtifactSemantics:
    """Canonical artifact provenance bundled from the compiled architectural seams."""

    problem: ProblemSemantics
    execution_policy: ExecutionPolicySemantics
    feature: FeatureSemantics
    prediction: PredictionSemantics
    temporal_capability: TemporalCapabilitySemantics
