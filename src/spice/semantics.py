# pyright: strict

"""Typed seam semantics and root-level provenance bundles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .core.reporting import StageMetricDescriptor
    from .features.families.base import FeaturePrerequisites
    from .prediction.base import MetricDescriptor


@dataclass(frozen=True, slots=True)
class FeatureSemantics:
    feature_set_id: str
    feature_family_id: str
    feature_names: tuple[str, ...]
    feature_graph_fingerprint: str
    feature_prerequisites: FeaturePrerequisites


@dataclass(frozen=True, slots=True)
class ProblemSemantics:
    compiler_id: str
    problem_id: str
    lookback_seconds: int
    sample_count: int
    max_delay_seconds: int


@dataclass(frozen=True, slots=True)
class PredictionSemantics:
    prediction_id: str
    prediction_family_id: str
    training_metric_descriptors: tuple[MetricDescriptor, ...]
    progress_metric_descriptors: tuple[StageMetricDescriptor, ...]
    simulation_metric_descriptors: tuple[MetricDescriptor, ...]
    primary_metric_id: str
    direction: Literal["maximize", "minimize"]
    supported_workflows: frozenset[str]


@dataclass(frozen=True, slots=True)
class RepresentationSemantics:
    representation_id: str


@dataclass(frozen=True, slots=True)
class CorpusSemantics:
    problem: ProblemSemantics
    feature: FeatureSemantics


@dataclass(frozen=True, slots=True)
class StudySemantics:
    problem: ProblemSemantics
    feature: FeatureSemantics
    prediction: PredictionSemantics
    representation: RepresentationSemantics


@dataclass(frozen=True, slots=True)
class ArtifactSemantics:
    problem: ProblemSemantics
    feature: FeatureSemantics
    prediction: PredictionSemantics
    representation: RepresentationSemantics
    max_candidate_slots: int
