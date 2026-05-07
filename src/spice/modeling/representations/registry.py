"""Representation Adapter registry."""

from __future__ import annotations

from .base import CompiledRepresentationContract
from .sequence_inputs import SEQUENCE_INPUT_REPRESENTATION_ID, prepare_sequence_input

_REPRESENTATION_PREPARE_IMPLS = {
    SEQUENCE_INPUT_REPRESENTATION_ID: prepare_sequence_input,
}


def compile_representation_contract(
    representation_id: str = SEQUENCE_INPUT_REPRESENTATION_ID,
) -> CompiledRepresentationContract:
    prepare_impl = _REPRESENTATION_PREPARE_IMPLS.get(representation_id)
    if prepare_impl is None:
        raise ValueError(f"Unknown representation_id: {representation_id}")
    return CompiledRepresentationContract(
        representation_id=representation_id,
        prepare_impl=prepare_impl,
    )
