"""Prediction-family specs for the fixed in-repo families."""

from __future__ import annotations

from ..core.specs import lookup_local_spec

_SUPPORTED_PREDICTION_FAMILY_IDS = frozenset({"min_block_fee_multitask"})

def _require_prediction_family_id(family_id: str) -> str:
    return lookup_local_spec(
        {family_id: family_id for family_id in _SUPPORTED_PREDICTION_FAMILY_IDS},
        family_id,
        "prediction.family_id",
    )


def validate_prediction_family_id(family_id: str) -> str:
    return _require_prediction_family_id(family_id)
