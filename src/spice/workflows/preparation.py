"""Prepared workflow inputs and root resolution."""

from __future__ import annotations

from dataclasses import dataclass

from ..config.models import (
    TuneConfig,
    TunedParameterSet,
    TunedProblemParams,
)
from ..corpus.coverage import training_coverage_requirement, validate_corpus_coverage
from ..corpus.metadata import CorpusManifest
from ..modeling.pipeline import TrainingSpec, build_trial_training_spec
from ..modeling.tuning import apply_tuned_parameters
from ..storage.workflow_root_materialization import materialize_tune_roots
from ..storage.workflow_roots import TuneWorkflowRoots


@dataclass(frozen=True, slots=True)
class PreparedTuneWorkflow:
    config: TuneConfig
    roots: TuneWorkflowRoots
    corpus_manifest: CorpusManifest


def prepare_tune(config: TuneConfig) -> PreparedTuneWorkflow:
    roots = materialize_tune_roots(config)
    corpus_manifest = roots.corpus.load_manifest()
    coverage_spec = _build_tuning_coverage_spec(
        config,
        roots=roots,
        corpus_manifest=corpus_manifest,
    )
    _validate_training_coverage(corpus_manifest, spec=coverage_spec)
    return PreparedTuneWorkflow(
        config=config,
        roots=roots,
        corpus_manifest=corpus_manifest,
    )


def _build_tuning_coverage_spec(
    config: TuneConfig,
    *,
    roots: TuneWorkflowRoots,
    corpus_manifest: CorpusManifest,
) -> TrainingSpec:
    if (
        config.tuning_space.problem is None
        or config.tuning_space.problem.lookback_seconds is None
    ):
        return build_trial_training_spec(
            config,
            corpus=roots.corpus,
            study=roots.study,
            corpus_manifest=corpus_manifest,
        )
    return build_trial_training_spec(
        apply_tuned_parameters(
            config,
            TunedParameterSet(
                problem=TunedProblemParams(
                    lookback_seconds=max(config.tuning_space.problem.lookback_seconds)
                )
            ),
        ),
        corpus=roots.corpus,
        study=roots.study,
        corpus_manifest=corpus_manifest,
    )


def _validate_training_coverage(
    corpus_manifest: CorpusManifest,
    *,
    spec: TrainingSpec,
) -> None:
    validate_corpus_coverage(
        corpus_manifest,
        contract=spec.problem_contract,
        feature_contract=spec.feature_contract,
        requirement=training_coverage_requirement(spec.problem_contract),
    )
