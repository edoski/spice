"""Problem-owned execution policy seam."""

from __future__ import annotations

from pydantic import field_validator

from ...core.config_model import ConfigModel
from ...core.specs import lookup_local_spec, owner_payload, validate_owner_config
from ...core.validation import validate_path_segment


class ExecutionPolicyConfig(ConfigModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return validate_path_segment(value, label="problem.execution_policy.id")


_SUPPORTED_EXECUTION_POLICY_IDS = frozenset({"strict_deadline_miss"})


def _require_execution_policy_id(policy_id: str) -> str:
    return lookup_local_spec(
        {policy_id: policy_id for policy_id in _SUPPORTED_EXECUTION_POLICY_IDS},
        policy_id,
        "problem.execution_policy.id",
    )


def coerce_execution_policy_config(
    payload: object,
) -> ExecutionPolicyConfig:
    from .strict_deadline_miss import StrictDeadlineMissConfig

    if isinstance(payload, StrictDeadlineMissConfig):
        return payload
    raw_payload = owner_payload(
        payload,
        owner="problem.execution_policy",
        config_type=ExecutionPolicyConfig,
    )
    raw_config = validate_owner_config(raw_payload, ExecutionPolicyConfig)
    _require_execution_policy_id(raw_config.id)
    return validate_owner_config(raw_payload, StrictDeadlineMissConfig)
