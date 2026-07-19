"""Strict bounded-delay execution policy."""

from pydantic import field_validator

from .base import ExecutionPolicyConfig


class StrictDeadlineMissConfig(ExecutionPolicyConfig):
    id: str = "strict_deadline_miss"

    @field_validator("id")
    @classmethod
    def validate_strict_deadline_miss_id(cls, value: str) -> str:
        value = ExecutionPolicyConfig.validate_id(value)
        if value != "strict_deadline_miss":
            raise ValueError("problem.execution_policy.id must be strict_deadline_miss")
        return value
