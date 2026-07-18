"""Strict payload codecs for study-root manifests."""

from __future__ import annotations

from ..config.models import (
    PredictionConfig,
    ProblemSpec,
    SequenceConfig,
    SplitConfig,
    TrainingConfig,
    TuningSearchConfig,
    TuningSpaceConfig,
    coerce_features_config,
    coerce_problem_spec,
)
from ..core.errors import StateLayoutError
from ..modeling.families.base import ModelConfig
from ..modeling.families.registry import coerce_model_config
from ..modeling.tuned_config import coerce_tuning_space_config
from .artifact_codecs import TrainingSourcePayload
from .payloads import PayloadRecord, decode_payload_record
from .semantics_codecs import STUDY_SEMANTICS_CODEC
from .study_models import StudyManifest


class StudyDefinitionPayload(PayloadRecord):
    study_id: str
    sequence: dict[str, object]
    prediction: dict[str, object]
    study_name: str
    chain_name: str
    corpus_id: str
    corpus_name: str
    training_cutoff_timestamp: int | None = None
    training_source: dict[str, object]
    problem: dict[str, object]
    features: dict[str, object]
    model: dict[str, object]
    split: dict[str, object]
    training: dict[str, object]
    tuning: dict[str, object]
    tuning_space: dict[str, object]


class StudyManifestPayload(PayloadRecord):
    definition: StudyDefinitionPayload
    sampler_name: str
    sampler_seed: int
    pruner_name: str
    enable_pruning: bool
    semantics: dict[str, object]

    def to_manifest(self) -> StudyManifest:
        definition = self.definition
        model = coerce_model_config(definition.model)
        problem = coerce_problem_spec(definition.problem)
        prediction = PredictionConfig.model_validate(definition.prediction)
        return StudyManifest(
            study_id=definition.study_id,
            sequence=SequenceConfig.model_validate(definition.sequence),
            prediction=prediction,
            study_name=definition.study_name,
            chain_name=definition.chain_name,
            corpus_id=definition.corpus_id,
            corpus_name=definition.corpus_name,
            training_source=TrainingSourcePayload.model_validate(
                definition.training_source,
                strict=True,
            ).to_provenance(),
            problem=problem,
            features=coerce_features_config(definition.features),
            model=model,
            split=SplitConfig.model_validate(definition.split),
            training=TrainingConfig.model_validate(definition.training),
            tuning=TuningSearchConfig.model_validate(definition.tuning),
            sampler_name=self.sampler_name,
            sampler_seed=self.sampler_seed,
            pruner_name=self.pruner_name,
            enable_pruning=self.enable_pruning,
            tuning_space=coerce_study_tuning_space(
                definition.tuning_space,
                model=model,
                problem=problem,
            ),
            semantics=STUDY_SEMANTICS_CODEC.decode(self.semantics),
        )


def _decode_study_manifest(payload: dict[str, object]) -> StudyManifest:
    return decode_payload_record(
        "study manifest",
        StudyManifestPayload,
        payload,
        lambda model: model.to_manifest(),
    )


def coerce_study_tuning_space(
    payload: object,
    *,
    model: ModelConfig[str],
    problem: ProblemSpec,
) -> TuningSpaceConfig:
    tuning_space = coerce_tuning_space_config(
        payload,
        model_config=model,
        problem_config=problem,
    )
    if tuning_space is None:
        raise StateLayoutError("Study tuning_space payload is required")
    return tuning_space
