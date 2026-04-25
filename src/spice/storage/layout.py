"""Deterministic workflow storage layout helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, overload

from .engine import state_db_path
from .identity import (
    artifact_storage_identity_from_config,
    study_storage_identity_from_config,
)
from .ids import artifact_storage_id, corpus_storage_id, study_storage_id

if TYPE_CHECKING:
    from ..config.models import AcquireConfig, ModelWorkflowConfig

_CATALOG_DB_FILENAME = "catalog.sqlite"
CORPORA_ROOT_NAME = "corpora"
STUDIES_ROOT_NAME = "studies"
ARTIFACTS_ROOT_NAME = "artifacts"
STATE_DIR_NAME = ".spice"


@dataclass(frozen=True, slots=True)
class WorkflowPaths:
    output_root: Path
    catalog_db: Path
    corpus_id: str
    corpus_root: Path
    history_dir: Path
    evaluation_dir: Path
    corpus_state_db: Path
    artifact_id: str | None = None
    artifact_root: Path | None = None
    checkpoint_dir: Path | None = None
    artifact_state_db: Path | None = None
    study_id: str | None = None
    study_root: Path | None = None
    study_state_db: Path | None = None


@dataclass(frozen=True, slots=True)
class WorkflowIdentity:
    corpus_id: str
    study_id: str | None = None
    artifact_id: str | None = None


def catalog_db_path(storage_root: Path) -> Path:
    return storage_root / STATE_DIR_NAME / _CATALOG_DB_FILENAME


def corpus_root_path(storage_root: Path, *, chain_name: str, corpus_id: str) -> Path:
    return storage_root / CORPORA_ROOT_NAME / chain_name / corpus_id


def study_root_path(storage_root: Path, *, chain_name: str, study_id: str) -> Path:
    return storage_root / STUDIES_ROOT_NAME / chain_name / study_id


def artifact_root_path(storage_root: Path, *, chain_name: str, artifact_id: str) -> Path:
    return storage_root / ARTIFACTS_ROOT_NAME / chain_name / artifact_id


def build_workflow_paths(
    *,
    output_root: Path,
    chain_name: str,
    identity: WorkflowIdentity,
) -> WorkflowPaths:
    catalog_db = catalog_db_path(output_root)
    corpus_root = corpus_root_path(
        output_root,
        chain_name=chain_name,
        corpus_id=identity.corpus_id,
    )
    study_root = (
        None
        if identity.study_id is None
        else study_root_path(output_root, chain_name=chain_name, study_id=identity.study_id)
    )
    artifact_root = (
        None
        if identity.artifact_id is None
        else artifact_root_path(
            output_root,
            chain_name=chain_name,
            artifact_id=identity.artifact_id,
        )
    )

    return WorkflowPaths(
        output_root=output_root,
        catalog_db=catalog_db,
        corpus_id=identity.corpus_id,
        corpus_root=corpus_root,
        history_dir=corpus_root / "history",
        evaluation_dir=corpus_root / "evaluation",
        corpus_state_db=state_db_path(corpus_root),
        artifact_id=identity.artifact_id,
        artifact_root=artifact_root,
        checkpoint_dir=None if artifact_root is None else artifact_root / "checkpoints",
        artifact_state_db=(
            None if artifact_root is None else state_db_path(artifact_root)
        ),
        study_id=identity.study_id,
        study_root=study_root,
        study_state_db=(
            None if study_root is None else state_db_path(study_root)
        ),
    )


@overload
def resolve_workflow_paths(
    config: AcquireConfig,
    *,
    study_id: str | None = None,
) -> WorkflowPaths: ...


@overload
def resolve_workflow_paths(
    config: ModelWorkflowConfig,
    *,
    study_id: str | None = None,
) -> WorkflowPaths: ...


def resolve_workflow_paths(
    config: object,
    *,
    study_id: str | None = None,
) -> WorkflowPaths:
    from ..config.models import AcquireConfig, ModelWorkflowConfig

    if isinstance(config, (AcquireConfig, ModelWorkflowConfig)):
        return build_workflow_paths(
            output_root=config.storage.root,
            chain_name=config.chain.name,
            identity=resolve_workflow_identity(config, study_id=study_id),
        )
    raise TypeError(f"Unsupported workflow config for path resolution: {type(config)!r}")


@overload
def resolve_workflow_identity(
    config: AcquireConfig,
    *,
    study_id: str | None = None,
) -> WorkflowIdentity: ...


@overload
def resolve_workflow_identity(
    config: ModelWorkflowConfig,
    *,
    study_id: str | None = None,
) -> WorkflowIdentity: ...


def resolve_workflow_identity(config: object, *, study_id: str | None = None) -> WorkflowIdentity:
    from ..config.models import (
        AcquireConfig,
        EvaluateConfig,
        ModelWorkflowConfig,
        TrainConfig,
        TuneConfig,
    )

    if isinstance(config, AcquireConfig):
        return WorkflowIdentity(
            corpus_id=corpus_storage_id(
                chain_name=config.chain.name,
                dataset_name=config.dataset.name,
                evaluation_date=config.dataset.evaluation_date,
            )
        )
    if not isinstance(config, ModelWorkflowConfig):
        raise TypeError(f"Unsupported workflow config for identity resolution: {type(config)!r}")

    corpus_id = corpus_storage_id(
        chain_name=config.chain.name,
        dataset_name=config.dataset.name,
        evaluation_date=config.dataset.evaluation_date,
    )
    tuning_mode = isinstance(config, TuneConfig)
    resolved_study_id = study_id
    needs_study_id = tuning_mode or config.artifact.variant.value == "tuned"
    if (
        resolved_study_id is None
        and needs_study_id
        and isinstance(config, (TuneConfig, TrainConfig, EvaluateConfig))
    ):
        resolved_study_id = study_storage_id(
            identity=study_storage_identity_from_config(config, corpus_id=corpus_id)
        )
    artifact_id: str | None = None
    if isinstance(config, (TrainConfig, EvaluateConfig)):
        artifact_id = artifact_storage_id(
            identity=artifact_storage_identity_from_config(
                config,
                corpus_id=corpus_id,
                study_id=resolved_study_id,
            )
        )
    return WorkflowIdentity(
        corpus_id=corpus_id,
        study_id=resolved_study_id,
        artifact_id=artifact_id,
    )
