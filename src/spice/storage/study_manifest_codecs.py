"""Strict payload codecs for study-root manifests."""

from __future__ import annotations

from typing import cast

from ..config.models import (
    PredictionConfig,
    ProblemSpec,
    SplitConfig,
    TrainingConfig,
    TuningSearchConfig,
    TuningSpaceConfig,
    coerce_features_config,
    coerce_problem_spec,
)
from ..core.errors import StateLayoutError
from ..evaluation import coerce_evaluator_config
from ..modeling.dataset_builders import coerce_dataset_builder_config
from ..modeling.families.base import ModelConfig
from ..modeling.families.registry import coerce_model_config
from ..modeling.tuned_config import coerce_tuning_space_config
from ..objectives import coerce_objective_config
from .identity import identity_payload, study_manifest_identity
from .payloads import PayloadCodec, PayloadRecord, decode_payload_record
from .semantics_codecs import STUDY_SEMANTICS_CODEC
from .artifact_codecs import TrainingSourcePayload
from .study_models import StudyManifest


class StudyDefinitionPayload(PayloadRecord):
    study_id: str
    dataset_builder: dict[str, object]
    prediction: dict[str, object]
    objective: dict[str, object]
    evaluator: dict[str, object] | None = None
    study_name: str
    chain_name: str
    corpus_id: str
    corpus_name: str
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

    @classmethod
    def from_manifest(cls, manifest: StudyManifest) -> StudyManifestPayload:
        payload = {
            **identity_payload(study_manifest_identity(manifest)),
            "semantics": STUDY_SEMANTICS_CODEC.encode(manifest.semantics),
        }
        definition = payload["definition"]
        if not isinstance(definition, dict):
            raise TypeError("study manifest definition did not serialize to a mapping")
        definition["training_source"] = TrainingSourcePayload.from_provenance(
            manifest.training_source
        ).model_dump(mode="json")
        return cls.model_validate(payload)

    def to_manifest(self) -> StudyManifest:
        definition = self.definition
        model = coerce_model_config(definition.model)
        problem = coerce_problem_spec(definition.problem)
        prediction = PredictionConfig.model_validate(definition.prediction)
        return StudyManifest(
            study_id=definition.study_id,
            dataset_builder=coerce_dataset_builder_config(definition.dataset_builder),
            prediction=prediction,
            objective=coerce_objective_config(definition.objective),
            evaluator=(
                None
                if definition.evaluator is None
                else coerce_evaluator_config(definition.evaluator)
            ),
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


def _encode_study_manifest(manifest: StudyManifest) -> dict[str, object]:
    payload = StudyManifestPayload.from_manifest(manifest).model_dump(
        mode="json",
        exclude_none=True,
    )
    return cast(dict[str, object], payload)


def _decode_study_manifest(payload: dict[str, object]) -> StudyManifest:
    return decode_payload_record(
        "study manifest",
        StudyManifestPayload,
        payload,
        lambda model: model.to_manifest(),
    )


STUDY_MANIFEST_CODEC: PayloadCodec[StudyManifest] = PayloadCodec(
    encode=_encode_study_manifest,
    decode=_decode_study_manifest,
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
