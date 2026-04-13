"""Artifact-root SQLAlchemy persistence."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from ..modeling.result_codecs import (
    artifact_manifest_from_row,
    artifact_manifest_values,
    simulation_run_from_row,
    simulation_run_values,
    simulation_summary_from_row,
    simulation_summary_values,
    training_epoch_from_row,
    training_epoch_values,
    training_summary_from_row,
    training_summary_values,
)
from .engine import RootKind, create_state_engine, ensure_state_db, table_exists, touch_meta
from .schema import (
    ARTIFACT_TABLES,
    artifact_manifest,
    simulation_runs,
    simulation_summary,
    training_epochs,
    training_summary,
)

if TYPE_CHECKING:
    from ..modeling.artifacts import TrainingArtifactManifest
    from ..modeling.results import (
        SimulationSummaryRecord,
        TrainingEpochRecord,
        TrainingSummary,
    )
    from ..modeling.simulation import SimulationRunSummary


def write_artifact_manifest(
    db_path: Path,
    *,
    manifest: TrainingArtifactManifest,
    root_kind: RootKind,
) -> None:
    ensure_state_db(db_path, root_kind=root_kind, tables=ARTIFACT_TABLES)
    engine = create_state_engine(db_path)
    try:
        with engine.begin() as conn:
            values = artifact_manifest_values(manifest)
            statement = sqlite_insert(artifact_manifest).values(**values)
            conn.execute(
                statement.on_conflict_do_update(
                    index_elements=[artifact_manifest.c.singleton],
                    set_={key: value for key, value in values.items() if key != "singleton"},
                )
            )
            touch_meta(conn, root_kind=root_kind)
    finally:
        engine.dispose()


def load_artifact_manifest(db_path: Path) -> TrainingArtifactManifest:
    engine = create_state_engine(db_path)
    try:
        with engine.connect() as conn:
            row = conn.execute(select(artifact_manifest)).mappings().first()
        if row is None:
            raise ValueError(f"Missing artifact manifest: {db_path}")
        return artifact_manifest_from_row(row)
    finally:
        engine.dispose()


def write_training_state(
    db_path: Path,
    *,
    root_kind: RootKind,
    summary: TrainingSummary,
    epoch_rows: list[TrainingEpochRecord],
) -> None:
    ensure_state_db(db_path, root_kind=root_kind, tables=ARTIFACT_TABLES)
    engine = create_state_engine(db_path)
    try:
        with engine.begin() as conn:
            values = training_summary_values(summary)
            statement = sqlite_insert(training_summary).values(**values)
            conn.execute(
                statement.on_conflict_do_update(
                    index_elements=[training_summary.c.singleton],
                    set_={key: value for key, value in values.items() if key != "singleton"},
                )
            )
            conn.execute(delete(training_epochs))
            if epoch_rows:
                conn.execute(
                    training_epochs.insert(),
                    [training_epoch_values(record) for record in epoch_rows],
                )
            touch_meta(conn, root_kind=root_kind)
    finally:
        engine.dispose()


def load_training_summary(db_path: Path) -> TrainingSummary | None:
    if not table_exists(db_path, training_summary.name):
        return None
    engine = create_state_engine(db_path)
    try:
        with engine.connect() as conn:
            row = conn.execute(select(training_summary)).mappings().first()
        if row is None:
            return None
        return training_summary_from_row(row)
    finally:
        engine.dispose()


def list_training_epochs(db_path: Path) -> list[TrainingEpochRecord]:
    if not table_exists(db_path, training_epochs.name):
        return []
    engine = create_state_engine(db_path)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                select(training_epochs).order_by(training_epochs.c.epoch)
            ).mappings().all()
        return [training_epoch_from_row(row) for row in rows]
    finally:
        engine.dispose()


def write_simulation_state(
    db_path: Path,
    *,
    root_kind: RootKind,
    summary: SimulationSummaryRecord,
) -> None:
    ensure_state_db(db_path, root_kind=root_kind, tables=ARTIFACT_TABLES)
    engine = create_state_engine(db_path)
    try:
        with engine.begin() as conn:
            values = simulation_summary_values(summary)
            statement = sqlite_insert(simulation_summary).values(**values)
            conn.execute(
                statement.on_conflict_do_update(
                    index_elements=[simulation_summary.c.singleton],
                    set_={key: value for key, value in values.items() if key != "singleton"},
                )
            )
            conn.execute(delete(simulation_runs))
            if summary.runs:
                conn.execute(
                    simulation_runs.insert(),
                    [
                        simulation_run_values(run, ordinal=ordinal)
                        for ordinal, run in enumerate(summary.runs, start=1)
                    ],
                )
            touch_meta(conn, root_kind=root_kind)
    finally:
        engine.dispose()


def load_simulation_summary(db_path: Path) -> SimulationSummaryRecord | None:
    if not table_exists(db_path, simulation_summary.name):
        return None
    engine = create_state_engine(db_path)
    try:
        with engine.connect() as conn:
            row = conn.execute(select(simulation_summary)).mappings().first()
        if row is None:
            return None
        return simulation_summary_from_row(row, runs=list_simulation_runs(db_path))
    finally:
        engine.dispose()


def list_simulation_runs(db_path: Path) -> list[SimulationRunSummary]:
    if not table_exists(db_path, simulation_runs.name):
        return []
    engine = create_state_engine(db_path)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                select(simulation_runs).order_by(simulation_runs.c.ordinal)
            ).mappings().all()
        return [simulation_run_from_row(row) for row in rows]
    finally:
        engine.dispose()
