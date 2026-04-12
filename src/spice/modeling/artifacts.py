"""Training artifact persistence and feature-graph validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import torch
from pydantic import BaseModel, ConfigDict, SerializeAsAny

from ..core.config import ArtifactVariant, ChainConfig, ModelConfig, StudyConfig
from ..core.constants import (
    ARTIFACT_MANIFEST_FILENAME,
    MODEL_STATE_FILENAME,
)
from ..core.files import write_path_atomic
from ..core.json import write_json
from ..data.normalization import ScalerStats
from ..features import FeatureSelection, feature_graph_fingerprint, validate_feature_selection
from .models import TemporalModel
from .pipeline import PreparedTrainingDataset, TrainingSpec
from .registry import build_model, coerce_model_config


class ArtifactModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TrainingArtifactManifest(ArtifactModel):
    kind: Literal["training_artifact"] = "training_artifact"
    chain: ChainConfig
    dataset_id: str
    variant: ArtifactVariant
    study: StudyConfig | None = None
    max_delay_seconds: int
    lookback_seconds: int
    sample_count: int
    lookback_steps: int
    max_extra_wait_steps: int
    action_count: int
    feature_set_id: str
    n_features: int
    feature_names: list[str]
    feature_graph_fingerprint: str
    model: SerializeAsAny[ModelConfig]
    scaler: ScalerStats


@dataclass(slots=True)
class LoadedTrainingArtifact:
    manifest: TrainingArtifactManifest
    model: TemporalModel


def feature_selection_from_manifest(manifest: TrainingArtifactManifest) -> FeatureSelection:
    selection = FeatureSelection(
        feature_set_id=manifest.feature_set_id,
        feature_names=tuple(manifest.feature_names),
    )
    validate_feature_selection(selection.feature_set_id, selection.feature_names)
    return selection


def validate_artifact_feature_graph(
    manifest: TrainingArtifactManifest,
    *,
    requested_feature_set_id: str | None = None,
) -> FeatureSelection:
    selection = feature_selection_from_manifest(manifest)
    if (
        requested_feature_set_id is not None
        and requested_feature_set_id != selection.feature_set_id
    ):
        raise ValueError(
            "Configured feature_set.id does not match the trained artifact: "
            f"expected {selection.feature_set_id}, got {requested_feature_set_id}"
        )
    current_fingerprint = feature_graph_fingerprint(selection.feature_names)
    if current_fingerprint != manifest.feature_graph_fingerprint:
        raise ValueError(
            "Current feature graph does not match the trained artifact manifest"
        )
    return selection


def build_training_artifact_manifest(
    prepared: PreparedTrainingDataset,
    *,
    spec: TrainingSpec,
) -> TrainingArtifactManifest:
    return TrainingArtifactManifest(
        chain=spec.chain,
        dataset_id=spec.dataset_id,
        variant=spec.variant,
        study=spec.study,
        max_delay_seconds=spec.max_delay_seconds,
        lookback_seconds=spec.lookback_seconds,
        sample_count=spec.sample_count,
        lookback_steps=prepared.geometry.lookback_steps,
        max_extra_wait_steps=prepared.geometry.max_extra_wait_steps,
        action_count=prepared.geometry.action_count,
        feature_set_id=prepared.feature_set_id,
        n_features=prepared.n_features,
        feature_names=list(prepared.feature_names),
        feature_graph_fingerprint=prepared.feature_graph_fingerprint,
        model=spec.model,
        scaler=prepared.scaler,
    )


def write_training_artifact(
    artifact_dir: Path,
    *,
    manifest: TrainingArtifactManifest,
    model: TemporalModel,
) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    write_json(artifact_dir / ARTIFACT_MANIFEST_FILENAME, manifest)
    cpu_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
    write_path_atomic(
        artifact_dir / MODEL_STATE_FILENAME,
        lambda tmp_path: torch.save(cpu_state, tmp_path),
    )


def load_training_artifact(artifact_dir: Path) -> LoadedTrainingArtifact:
    payload = json.loads((artifact_dir / ARTIFACT_MANIFEST_FILENAME).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Training artifact manifest must be a mapping")
    payload["model"] = coerce_model_config(payload["model"])
    manifest = TrainingArtifactManifest.model_validate(payload)
    model = build_model(manifest.n_features, manifest.action_count, manifest.model)
    state_dict = torch.load(artifact_dir / MODEL_STATE_FILENAME, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()
    return LoadedTrainingArtifact(manifest=manifest, model=model)
