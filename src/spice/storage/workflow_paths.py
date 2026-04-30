"""Workflow-config storage path resolution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .engine import state_db_path
from .ids import corpus_storage_id
from .layout import artifact_root_path, catalog_db_path, corpus_root_path, study_root_path


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
    artifact_state_db: Path | None = None
    study_id: str | None = None
    study_root: Path | None = None
    study_state_db: Path | None = None


@dataclass(frozen=True, slots=True)
class WorkflowIdentity:
    corpus_id: str
    study_id: str | None = None
    artifact_id: str | None = None


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
        artifact_state_db=(
            None if artifact_root is None else state_db_path(artifact_root)
        ),
        study_id=identity.study_id,
        study_root=study_root,
        study_state_db=(
            None if study_root is None else state_db_path(study_root)
        ),
    )


def resolve_workflow_paths(
    config: object,
) -> WorkflowPaths:
    from ..config.models import AcquireConfig

    if isinstance(config, AcquireConfig):
        return build_workflow_paths(
            output_root=config.storage.root,
            chain_name=config.chain.name,
            identity=resolve_workflow_identity(config),
        )
    raise TypeError(f"Unsupported workflow config for path resolution: {type(config)!r}")


def resolve_workflow_identity(config: object) -> WorkflowIdentity:
    from ..config.models import AcquireConfig

    if isinstance(config, AcquireConfig):
        return WorkflowIdentity(
            corpus_id=corpus_storage_id(
                chain_name=config.chain.name,
                dataset_name=config.dataset.name,
                evaluation_date=config.dataset.evaluation_date,
            )
        )
    raise TypeError(f"Unsupported workflow config for identity resolution: {type(config)!r}")
