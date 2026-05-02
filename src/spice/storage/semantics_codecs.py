"""Storage payload codecs for persisted semantic contracts."""

from __future__ import annotations

from typing import Any, TypeVar, cast

from pydantic import TypeAdapter, ValidationError

from ..core.errors import StateLayoutError
from ..features import FeaturePrerequisites
from ..prediction import MetricDescriptor
from ..semantics import ArtifactSemantics, StudySemantics

AdapterValueT = TypeVar("AdapterValueT")

_STUDY_SEMANTICS_ADAPTER = TypeAdapter(StudySemantics)
_ARTIFACT_SEMANTICS_ADAPTER = TypeAdapter(ArtifactSemantics)

_ADAPTER_NAMESPACE = {
    "FeaturePrerequisites": FeaturePrerequisites,
    "MetricDescriptor": MetricDescriptor,
}
for _adapter in (
    _STUDY_SEMANTICS_ADAPTER,
    _ARTIFACT_SEMANTICS_ADAPTER,
):
    _adapter.rebuild(_types_namespace=_ADAPTER_NAMESPACE)


def artifact_semantics_payload(semantics: ArtifactSemantics) -> dict[str, object]:
    return _adapter_payload(_ARTIFACT_SEMANTICS_ADAPTER, semantics)


def artifact_semantics_from_payload(payload: dict[str, object]) -> ArtifactSemantics:
    return cast(ArtifactSemantics, _adapter_value(_ARTIFACT_SEMANTICS_ADAPTER, payload))


def study_semantics_payload(semantics: StudySemantics) -> dict[str, object]:
    return _adapter_payload(_STUDY_SEMANTICS_ADAPTER, semantics)


def study_semantics_from_payload(payload: dict[str, object]) -> StudySemantics:
    return cast(StudySemantics, _adapter_value(_STUDY_SEMANTICS_ADAPTER, payload))


def _adapter_payload(adapter: object, value: object) -> dict[str, object]:
    payload = cast(TypeAdapter[Any], adapter).dump_python(value, mode="json")
    if not isinstance(payload, dict):
        raise StateLayoutError("Expected adapter to serialize to a mapping payload")
    return cast(dict[str, object], payload)


def _adapter_value(adapter: TypeAdapter[AdapterValueT], payload: object) -> AdapterValueT:
    try:
        return adapter.validate_python(payload)
    except (ValidationError, ValueError, TypeError) as exc:
        raise StateLayoutError(f"Invalid semantics payload: {exc}") from exc
