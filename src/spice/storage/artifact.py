# pyright: strict

"""Artifact-root SQLite persistence."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, cast

from sqlalchemy import select
from sqlalchemy.engine import Engine

from ..core.errors import MissingStateError
from ..modeling.result_codecs import (
    artifact_manifest_from_payload,
    artifact_manifest_payload,
    simulation_run_from_payload,
    simulation_run_payload,
    simulation_summary_from_payload,
    simulation_summary_payload,
    training_epoch_from_payload,
    training_epoch_payload,
    training_summary_from_payload,
    training_summary_payload,
)
from .engine import RootKind, create_state_engine, ensure_state_db, table_exists, touch_meta
from .payloads import PayloadCodec, SequencePayloadStore, SingletonPayloadStore
from .schema import (
    ARTIFACT_TABLES,
    artifact_manifest,
    simulation_runs,
    simulation_summary,
    training_epochs,
    training_summary,
)

if TYPE_CHECKING:
    from ..modeling.results import (
        LoadedSimulationSummary,
        LoadedTrainingSummary,
        SimulationRuntimeSummary,
        TrainingArtifactManifest,
        TrainingEpochRecord,
        TrainingRuntimeSummary,
    )
    from ..prediction import PredictionSimulationRun

_RAW_PAYLOAD_CODEC = PayloadCodec[dict[str, object]](
    encode=lambda payload: payload,
    decode=lambda payload: payload,
)

_ARTIFACT_MANIFEST_STORE = SingletonPayloadStore(
    table=artifact_manifest,
    codec=PayloadCodec(
        encode=artifact_manifest_payload,
        decode=artifact_manifest_from_payload,
    ),
)
_TRAINING_SUMMARY_STORE = SingletonPayloadStore(
    table=training_summary,
    codec=_RAW_PAYLOAD_CODEC,
)
_SIMULATION_SUMMARY_STORE = SingletonPayloadStore(
    table=simulation_summary,
    codec=_RAW_PAYLOAD_CODEC,
)
_TRAINING_EPOCH_STORE = SequencePayloadStore(
    table=training_epochs,
    codec=_RAW_PAYLOAD_CODEC,
)
_SIMULATION_RUN_STORE = SequencePayloadStore(
    table=simulation_runs,
    codec=_RAW_PAYLOAD_CODEC,
)


def write_artifact_manifest(
    db_path: Path,
    *,
    manifest: TrainingArtifactManifest,
    root_kind: RootKind,
) -> None:
    """Persist the canonical artifact manifest before any runtime summaries are written."""

    ensure_state_db(db_path, root_kind=root_kind, tables=ARTIFACT_TABLES)
    engine = create_state_engine(db_path)
    try:
        with engine.begin() as conn:
            _ARTIFACT_MANIFEST_STORE.upsert(conn, manifest)
            touch_meta(conn, root_kind=root_kind)
    finally:
        engine.dispose()


def load_artifact_manifest(db_path: Path) -> TrainingArtifactManifest:
    """Load the canonical artifact manifest that owns persisted artifact provenance."""

    engine = create_state_engine(db_path)
    try:
        with engine.connect() as conn:
            manifest = _ARTIFACT_MANIFEST_STORE.load(conn)
        if manifest is None:
            raise MissingStateError(f"Missing artifact manifest: {db_path}")
        return manifest
    finally:
        engine.dispose()


def write_training_state(
    db_path: Path,
    *,
    root_kind: RootKind,
    summary: TrainingRuntimeSummary,
    epoch_rows: list[TrainingEpochRecord],
) -> None:
    """Persist training runtime summary plus ordered epoch history for one artifact root."""

    ensure_state_db(db_path, root_kind=root_kind, tables=ARTIFACT_TABLES)
    engine = create_state_engine(db_path)
    try:
        with engine.begin() as conn:
            _TRAINING_SUMMARY_STORE.upsert(conn, training_summary_payload(summary))
            _TRAINING_EPOCH_STORE.replace(
                conn,
                [
                    {"epoch": record.epoch, "payload": training_epoch_payload(record)}
                    for record in epoch_rows
                ],
            )
            touch_meta(conn, root_kind=root_kind)
    finally:
        engine.dispose()


def load_training_summary(db_path: Path) -> LoadedTrainingSummary | None:
    """Load the training read model as manifest plus runtime summary."""

    if not table_exists(db_path, training_summary.name):
        return None
    from ..modeling.results import LoadedTrainingSummary

    engine = create_state_engine(db_path)
    try:
        with engine.connect() as conn:
            manifest = _ARTIFACT_MANIFEST_STORE.load(conn)
            payload = _TRAINING_SUMMARY_STORE.load(conn)
        if manifest is None or payload is None:
            return None
        return LoadedTrainingSummary(
            manifest=manifest,
            runtime=training_summary_from_payload(payload),
        )
    finally:
        engine.dispose()


def list_training_epochs(db_path: Path) -> list[TrainingEpochRecord]:
    if not table_exists(db_path, training_epochs.name):
        return []
    engine = create_state_engine(db_path)
    try:
        with engine.connect() as conn:
            rows = (
                conn.execute(
                    select(training_epochs.c.epoch, training_epochs.c.payload).order_by(
                        training_epochs.c.epoch
                    )
                )
                .mappings()
                .all()
            )
        return [
            training_epoch_from_payload(_payload_mapping(row["payload"]), epoch=int(row["epoch"]))
            for row in rows
        ]
    finally:
        engine.dispose()


def write_simulation_state(
    db_path: Path,
    *,
    root_kind: RootKind,
    summary: SimulationRuntimeSummary,
) -> None:
    """Persist simulation runtime summary plus ordered run rows for one artifact root."""

    ensure_state_db(db_path, root_kind=root_kind, tables=ARTIFACT_TABLES)
    engine = create_state_engine(db_path)
    try:
        with engine.begin() as conn:
            _SIMULATION_SUMMARY_STORE.upsert(conn, simulation_summary_payload(summary))
            _SIMULATION_RUN_STORE.replace(
                conn,
                [
                    {"ordinal": ordinal, "payload": simulation_run_payload(run)}
                    for ordinal, run in enumerate(summary.runs, start=1)
                ],
            )
            touch_meta(conn, root_kind=root_kind)
    finally:
        engine.dispose()


def load_simulation_summary(db_path: Path) -> LoadedSimulationSummary | None:
    """Load the simulation read model as manifest plus runtime summary."""

    if not table_exists(db_path, simulation_summary.name):
        return None
    from ..modeling.results import LoadedSimulationSummary

    engine = create_state_engine(db_path)
    try:
        with engine.connect() as conn:
            manifest = _ARTIFACT_MANIFEST_STORE.load(conn)
            payload = _SIMULATION_SUMMARY_STORE.load(conn)
            runs = list_simulation_runs(db_path, engine=engine)
        if manifest is None or payload is None:
            return None
        return LoadedSimulationSummary(
            manifest=manifest,
            runtime=simulation_summary_from_payload(payload, runs=runs),
        )
    finally:
        engine.dispose()


def list_simulation_runs(
    db_path: Path,
    *,
    engine: Engine | None = None,
) -> list[PredictionSimulationRun]:
    if not table_exists(db_path, simulation_runs.name):
        return []
    owns_engine = engine is None
    active_engine = create_state_engine(db_path) if engine is None else engine
    try:
        with active_engine.connect() as conn:
            rows = (
                conn.execute(select(simulation_runs.c.payload).order_by(simulation_runs.c.ordinal))
                .mappings()
                .all()
            )
        return [simulation_run_from_payload(_payload_mapping(row["payload"])) for row in rows]
    finally:
        if owns_engine:
            active_engine.dispose()


def _payload_mapping(payload: object) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        raise TypeError("Artifact payload must be a mapping")
    mapping = cast(Mapping[object, object], payload)
    return {str(key): value for key, value in mapping.items()}
