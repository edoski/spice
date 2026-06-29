"""Training artifact runtime helpers and feature-graph validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch

from ..core.constants import MODEL_STATE_FILENAME
from ..core.files import write_path_atomic
from ..prediction import compile_prediction_contract
from ..semantics import ArtifactSemantics
from ..storage.artifact import load_artifact_manifest, write_artifact_manifest
from .dataset_builders import PreparedTrainingDataset
from .families.registry import build_model
from .models import TemporalModel
from .pipeline import TrainingSpec
from .results import TrainingArtifactManifest


@dataclass(slots=True)
class LoadedTrainingArtifact:
    manifest: TrainingArtifactManifest
    model: TemporalModel


def build_training_artifact_manifest(
    prepared: PreparedTrainingDataset,
    *,
    spec: TrainingSpec,
) -> TrainingArtifactManifest:
    return TrainingArtifactManifest(
        artifact_id=spec.artifact_id,
        sequence=spec.training.sequence,
        prediction=spec.prediction,
        chain_name=spec.chain.name,
        corpus_id=spec.corpus_id,
        corpus_name=spec.corpus_name,
        training_source=spec.training_source,
        problem=spec.problem,
        variant=spec.variant,
        study=spec.study,
        study_id=spec.study_id,
        features=spec.features,
        model=spec.model,
        split=spec.split,
        training=spec.training,
        scaler=prepared.scaler,
        sequence_runtime_metadata=prepared.sequence_runtime_metadata,
        temporal_capability=prepared.temporal_capability,
        semantics=ArtifactSemantics(
            problem=spec.problem_contract.semantics,
            execution_policy=spec.problem_contract.execution_policy.semantics,
            feature=spec.feature_contract.semantics,
            prediction=spec.prediction_contract.semantics,
            temporal_capability=prepared.temporal_capability.semantics,
        ),
    )


def load_training_artifact(artifact_dir: Path) -> LoadedTrainingArtifact:
    manifest = load_artifact_manifest(artifact_dir / ".spice" / "state.sqlite")
    prediction_contract = compile_prediction_contract(
        prediction_id=manifest.prediction.id,
        family_id=manifest.prediction.family_id,
    )
    model = build_model(
        manifest.n_features,
        prediction_contract.build_output_spec(manifest.action_width),
        manifest.model,
    )
    state_dict = torch.load(
        artifact_dir / MODEL_STATE_FILENAME,
        map_location="cpu",
        weights_only=True,
    )
    model.load_state_dict(state_dict)
    model.eval()
    return LoadedTrainingArtifact(
        manifest=manifest,
        model=model,
    )


def persist_training_artifact(
    artifact_dir: Path,
    *,
    manifest: TrainingArtifactManifest,
    model: TemporalModel,
) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    write_artifact_manifest(
        artifact_dir / ".spice" / "state.sqlite",
        manifest=manifest,
    )
    cpu_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}

    def _write(tmp_path: Path) -> None:
        torch.save(cpu_state, tmp_path)

    write_path_atomic(artifact_dir / MODEL_STATE_FILENAME, _write)
