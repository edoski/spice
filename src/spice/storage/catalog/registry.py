"""Static catalog root-kind metadata."""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Generic, TypeVar

from sqlalchemy import Table

from ..engine import RootKind
from ..layout import ARTIFACTS_ROOT_NAME, CORPORA_ROOT_NAME, STUDIES_ROOT_NAME
from .records import CatalogArtifactRecord, CatalogCorpusRecord, CatalogRecord, CatalogStudyRecord
from .schema import artifact_index, corpus_index, study_index

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
    count_field: str
    nullable_fields: frozenset[str] = frozenset()

    @property
    def field_names(self) -> tuple[str, ...]:
        return tuple(field.name for field in fields(self.record_type))

    def require_record(self, record: CatalogRecord) -> RecordT:
        if not isinstance(record, self.record_type):
            raise TypeError(
                f"catalog spec for {self.root_kind} cannot handle {type(record).__name__}"
            )
        return record

    def root_path_for_record(self, storage_root: Path, record: CatalogRecord) -> Path:
        typed_record = self.require_record(record)
        return (
            storage_root
            / self.parent_name
            / typed_record.chain_name
            / str(getattr(typed_record, self.key_field))
        )


DATASET_ROOT_SPEC: CatalogRootKindSpec[CatalogCorpusRecord] = CatalogRootKindSpec(
    root_kind=RootKind.CORPUS,
    label="corpus",
    record_type=CatalogCorpusRecord,
    table=corpus_index,
    key_field="corpus_id",
    parent_name=CORPORA_ROOT_NAME,
    default_order=("chain_name", "corpus_name"),
    count_field="dataset_roots",
)
STUDY_ROOT_SPEC: CatalogRootKindSpec[CatalogStudyRecord] = CatalogRootKindSpec(
    root_kind=RootKind.STUDY,
    label="study",
    record_type=CatalogStudyRecord,
    table=study_index,
    key_field="study_id",
    parent_name=STUDIES_ROOT_NAME,
    default_order=(
        "chain_name",
        "corpus_name",
        "features_id",
        "prediction_id",
        "model_id",
        "problem_id",
        "study_name",
    ),
    count_field="study_roots",
)
ARTIFACT_ROOT_SPEC: CatalogRootKindSpec[CatalogArtifactRecord] = CatalogRootKindSpec(
    root_kind=RootKind.ARTIFACT,
    label="artifact",
    record_type=CatalogArtifactRecord,
    table=artifact_index,
    key_field="artifact_id",
    parent_name=ARTIFACTS_ROOT_NAME,
    default_order=(
        "chain_name",
        "corpus_name",
        "features_id",
        "prediction_id",
        "model_id",
        "problem_id",
        "variant",
    ),
    count_field="artifact_roots",
    nullable_fields=frozenset({"study_id", "study_name"}),
)

_SPECS_BY_ROOT_KIND = {
    RootKind.CORPUS: DATASET_ROOT_SPEC,
    RootKind.STUDY: STUDY_ROOT_SPEC,
    RootKind.ARTIFACT: ARTIFACT_ROOT_SPEC,
}
_ROOT_KIND_BY_RECORD_TYPE = {
    CatalogCorpusRecord: RootKind.CORPUS,
    CatalogStudyRecord: RootKind.STUDY,
    CatalogArtifactRecord: RootKind.ARTIFACT,
}


def all_root_kind_specs() -> tuple[CatalogRootKindSpec[Any], ...]:
    return (DATASET_ROOT_SPEC, STUDY_ROOT_SPEC, ARTIFACT_ROOT_SPEC)


def spec_for_root_kind(root_kind: RootKind) -> CatalogRootKindSpec[Any]:
    return _SPECS_BY_ROOT_KIND[root_kind]


def spec_for_record(record: CatalogRecord) -> CatalogRootKindSpec[Any]:
    return spec_for_root_kind(_ROOT_KIND_BY_RECORD_TYPE[type(record)])


def catalog_record_root_kind(record: CatalogRecord) -> RootKind:
    return _ROOT_KIND_BY_RECORD_TYPE[type(record)]


def catalog_root_parent_path(storage_root: Path, root_kind: RootKind) -> Path:
    return storage_root / spec_for_root_kind(root_kind).parent_name
