"""Static catalog root-kind registry and persistence helpers."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Generic, TypeVar, cast

from sqlalchemy import Table, and_, inspect, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import RowMapping
from sqlalchemy.sql.elements import ColumnElement

from ...core.errors import SpiceOperatorError
from ..artifact import load_artifact_manifest
from ..corpus import load_dataset_manifest
from ..engine import RootKind, create_sqlite_engine, ensure_table_shapes
from ..layout import (
    ARTIFACTS_ROOT_NAME,
    CORPORA_ROOT_NAME,
    STUDIES_ROOT_NAME,
    artifact_root_path,
    corpus_root_path,
    study_root_path,
)
from ..selectors import ArtifactSelector, DatasetSelector, StudySelector
from ..study_manifest import load_study_manifest
from .records import CatalogArtifactRecord, CatalogDatasetRecord, CatalogRecord, CatalogStudyRecord
from .schema import artifact_index, dataset_index, metadata, study_index

RecordT = TypeVar("RecordT", bound=CatalogRecord)


@dataclass(frozen=True, slots=True)
class CatalogRootKindSpec(Generic[RecordT]):
    root_kind: RootKind
    label: str
    record_type: type[RecordT]
    table: Table
    key_field: str
    parent_name: str
    default_order: tuple[str, ...]
    root_path: Callable[[Path, RecordT], Path]
    manifest_to_record: Callable[[Path, Path], RecordT]
    resolve_record: Callable[[Path, str], RecordT]
    path_fields: frozenset[str] = frozenset({"root_path", "state_db_path"})
    nullable_fields: frozenset[str] = frozenset()

    @property
    def field_names(self) -> tuple[str, ...]:
        return tuple(field.name for field in fields(self.record_type))

    def record_key(self, record: CatalogRecord) -> str:
        return str(getattr(self.require_record(record), self.key_field))

    def require_record(self, record: CatalogRecord) -> RecordT:
        if not isinstance(record, self.record_type):
            raise TypeError(
                f"catalog spec for {self.root_kind} cannot handle {type(record).__name__}"
            )
        return record

    def to_row(self, record: CatalogRecord) -> dict[str, object]:
        concrete = self.require_record(record)
        return {
            field_name: str(value) if isinstance(value, Path) else value
            for field_name in self.field_names
            for value in (getattr(concrete, field_name),)
        }

    def from_row(self, row: RowMapping) -> RecordT:
        payload: dict[str, object | None] = {}
        for field_name in self.field_names:
            value = row[field_name]
            if field_name in self.path_fields:
                payload[field_name] = Path(str(value))
            elif value is None and field_name in self.nullable_fields:
                payload[field_name] = None
            else:
                payload[field_name] = str(value)
        return self.record_type(**cast(Any, payload))

    def to_payload(self, record: CatalogRecord) -> dict[str, object | None]:
        return self.to_row(record)

    def from_payload(self, payload: dict[str, object | None]) -> RecordT:
        fields_set = set(self.field_names)
        payload_keys = set(payload)
        missing = sorted(fields_set - payload_keys)
        extra = sorted(payload_keys - fields_set)
        if missing:
            raise SpiceOperatorError(
                f"remote catalog record is missing fields: {', '.join(missing)}"
            )
        if extra:
            raise SpiceOperatorError(f"remote catalog record has extra fields: {', '.join(extra)}")
        values: dict[str, object | None] = {}
        for name in self.field_names:
            value = payload[name]
            if value is None:
                if name not in self.nullable_fields:
                    raise SpiceOperatorError(f"remote catalog record field {name} cannot be null")
                values[name] = None
                continue
            if name in self.path_fields:
                values[name] = Path(_require_string(name, value))
            else:
                values[name] = _require_string(name, value)
        return self.record_type(**cast(Any, values))

    def upsert(self, catalog_path: Path, record: CatalogRecord) -> None:
        _upsert_record(catalog_path, spec=self, values=self.to_row(record))

    def delete(self, catalog_path: Path, record: CatalogRecord) -> None:
        _delete_record(catalog_path, spec=self, key=self.record_key(record))

    def list_records(
        self,
        catalog_path: Path,
        *,
        filters: dict[str, str | None],
        order_by: tuple[str, ...] | None = None,
    ) -> list[RecordT]:
        return [
            self.from_row(row)
            for row in _select_rows(
                catalog_path,
                table=self.table,
                filters=[
                    self.table.c[name] == value
                    for name, value in filters.items()
                    if value is not None
                ],
                order_by=[self.table.c[name] for name in (order_by or self.default_order)],
            )
        ]


def ensure_catalog_db(path: Path) -> None:
    engine = _create_engine(path, create_dirs=True)
    try:
        metadata.create_all(engine)
        with engine.begin() as conn:
            ensure_table_shapes(conn, tables=tuple(spec.table for spec in all_root_kind_specs()))
    finally:
        engine.dispose()


def _build_dataset_record(root_path: Path, db_path: Path) -> CatalogDatasetRecord:
    manifest = load_dataset_manifest(db_path)
    return CatalogDatasetRecord(
        dataset_id=manifest.dataset.id,
        dataset_name=manifest.dataset.name,
        chain_name=manifest.chain.name,
        root_path=root_path,
        state_db_path=db_path,
    )


def _build_study_record(root_path: Path, db_path: Path) -> CatalogStudyRecord:
    manifest = load_study_manifest(db_path)
    return CatalogStudyRecord(
        study_id=manifest.study_id,
        study_name=manifest.study_name,
        dataset_id=manifest.dataset_id,
        dataset_name=manifest.dataset_name,
        chain_name=manifest.chain_name,
        features_id=manifest.features.id,
        prediction_id=manifest.prediction.id,
        model_id=manifest.model.id,
        problem_id=manifest.problem.id,
        root_path=root_path,
        state_db_path=db_path,
    )


def _build_artifact_record(root_path: Path, db_path: Path) -> CatalogArtifactRecord:
    manifest = load_artifact_manifest(db_path)
    return CatalogArtifactRecord(
        artifact_id=manifest.artifact_id,
        dataset_id=manifest.dataset_id,
        dataset_name=manifest.dataset_name,
        chain_name=manifest.chain_name,
        features_id=manifest.features_id,
        prediction_id=manifest.prediction_id,
        model_id=manifest.model.id,
        problem_id=manifest.problem_id,
        variant=manifest.variant.value,
        study_id=manifest.study_id,
        study_name=None if manifest.study is None else manifest.study.name,
        root_path=root_path,
        state_db_path=db_path,
    )


def _dataset_root_path(storage_root: Path, record: CatalogDatasetRecord) -> Path:
    return corpus_root_path(
        storage_root,
        chain_name=record.chain_name,
        corpus_id=record.dataset_id,
    )


def _study_root_path(storage_root: Path, record: CatalogStudyRecord) -> Path:
    return study_root_path(
        storage_root,
        chain_name=record.chain_name,
        study_id=record.study_id,
    )


def _artifact_root_path(storage_root: Path, record: CatalogArtifactRecord) -> Path:
    return artifact_root_path(
        storage_root,
        chain_name=record.chain_name,
        artifact_id=record.artifact_id,
    )


def _resolve_dataset(storage_root: Path, root_id: str) -> CatalogDatasetRecord:
    from .index import resolve_dataset_record

    return resolve_dataset_record(storage_root, selector=DatasetSelector(dataset_id=root_id))


def _resolve_study(storage_root: Path, root_id: str) -> CatalogStudyRecord:
    from .index import resolve_study_record

    return resolve_study_record(storage_root, selector=StudySelector(study_id=root_id))


def _resolve_artifact(storage_root: Path, root_id: str) -> CatalogArtifactRecord:
    from .index import resolve_artifact_record

    return resolve_artifact_record(storage_root, selector=ArtifactSelector(artifact_id=root_id))


DATASET_ROOT_SPEC = CatalogRootKindSpec[CatalogDatasetRecord](
    root_kind=RootKind.CORPUS,
    label="dataset",
    record_type=CatalogDatasetRecord,
    table=dataset_index,
    key_field="dataset_id",
    parent_name=CORPORA_ROOT_NAME,
    default_order=("chain_name", "dataset_name"),
    root_path=_dataset_root_path,
    manifest_to_record=_build_dataset_record,
    resolve_record=_resolve_dataset,
)
STUDY_ROOT_SPEC = CatalogRootKindSpec[CatalogStudyRecord](
    root_kind=RootKind.STUDY,
    label="study",
    record_type=CatalogStudyRecord,
    table=study_index,
    key_field="study_id",
    parent_name=STUDIES_ROOT_NAME,
    default_order=(
        "chain_name",
        "dataset_name",
        "features_id",
        "prediction_id",
        "model_id",
        "problem_id",
        "study_name",
    ),
    root_path=_study_root_path,
    manifest_to_record=_build_study_record,
    resolve_record=_resolve_study,
)
ARTIFACT_ROOT_SPEC = CatalogRootKindSpec[CatalogArtifactRecord](
    root_kind=RootKind.ARTIFACT,
    label="artifact",
    record_type=CatalogArtifactRecord,
    table=artifact_index,
    key_field="artifact_id",
    parent_name=ARTIFACTS_ROOT_NAME,
    default_order=(
        "chain_name",
        "dataset_name",
        "features_id",
        "prediction_id",
        "model_id",
        "problem_id",
        "variant",
    ),
    root_path=_artifact_root_path,
    manifest_to_record=_build_artifact_record,
    resolve_record=_resolve_artifact,
    nullable_fields=frozenset({"study_id", "study_name"}),
)

_SPECS_BY_ROOT_KIND = {
    RootKind.CORPUS: DATASET_ROOT_SPEC,
    RootKind.STUDY: STUDY_ROOT_SPEC,
    RootKind.ARTIFACT: ARTIFACT_ROOT_SPEC,
}
_ROOT_KIND_BY_RECORD_TYPE = {
    CatalogDatasetRecord: RootKind.CORPUS,
    CatalogStudyRecord: RootKind.STUDY,
    CatalogArtifactRecord: RootKind.ARTIFACT,
}


def all_root_kind_specs() -> tuple[CatalogRootKindSpec[Any], ...]:
    return (DATASET_ROOT_SPEC, STUDY_ROOT_SPEC, ARTIFACT_ROOT_SPEC)


def spec_for_root_kind(root_kind: RootKind) -> CatalogRootKindSpec[Any]:
    return _SPECS_BY_ROOT_KIND[root_kind]


def spec_for_record(record: CatalogRecord) -> CatalogRootKindSpec[Any]:
    return spec_for_root_kind(_ROOT_KIND_BY_RECORD_TYPE[type(record)])


def _create_engine(path: Path, *, create_dirs: bool = False):
    return create_sqlite_engine(path, create_dirs=create_dirs)


def _upsert_record(
    path: Path,
    *,
    spec: CatalogRootKindSpec[Any],
    values: dict[str, object],
) -> None:
    ensure_catalog_db(path)
    engine = _create_engine(path)
    now = _now_timestamp()
    payload = {
        **values,
        "created_at": now,
        "updated_at": now,
    }
    try:
        key_column = spec.table.c[spec.key_field]
        statement = sqlite_insert(spec.table).values(**payload)
        with engine.begin() as conn:
            conn.execute(
                statement.on_conflict_do_update(
                    index_elements=[key_column],
                    set_={
                        key: value
                        for key, value in payload.items()
                        if key not in {key_column.name, "created_at"}
                    },
                )
            )
    finally:
        engine.dispose()


def _delete_record(path: Path, *, spec: CatalogRootKindSpec[Any], key: str) -> None:
    if not path.is_file():
        return
    engine = _create_engine(path)
    try:
        if not inspect(engine).has_table(spec.table.name):
            return
        with engine.begin() as conn:
            conn.execute(spec.table.delete().where(spec.table.c[spec.key_field] == key))
    finally:
        engine.dispose()


def _select_rows(
    path: Path,
    *,
    table: Table,
    filters: list[ColumnElement[bool]],
    order_by: list[ColumnElement[Any]],
) -> list[RowMapping]:
    if not path.is_file():
        return []
    engine = _create_engine(path)
    try:
        if not inspect(engine).has_table(table.name):
            return []
        statement = select(table)
        if filters:
            statement = statement.where(and_(*filters))
        if order_by:
            statement = statement.order_by(*order_by)
        with engine.connect() as conn:
            return list(conn.execute(statement).mappings().all())
    finally:
        engine.dispose()


def _now_timestamp() -> int:
    return int(time.time())


def _require_string(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise SpiceOperatorError(f"remote catalog record field {name} must be a string")
    return value
