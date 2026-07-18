"""Explicit runtime configuration models."""

from __future__ import annotations

from enum import StrEnum
from typing import Self
from urllib.parse import urlparse

from pydantic import (
    Field,
    SerializeAsAny,
    field_validator,
    model_validator,
)

from ..core.config_model import ConfigModel as _ConfigModel
from ..core.errors import ConfigResolutionError
from ..core.specs import owner_payload, validate_owner_config
from ..core.validation import validate_path_segment
from ..features import validate_feature_selection
from ..temporal.compilers import ProblemCompilerConfig
from ..temporal.execution_policy import ExecutionPolicyConfig


class WorkflowTask(StrEnum):
    ACQUIRE = "acquire"


def _validate_http_endpoint_url(value: str, *, label: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{label} must be an http:// or https:// URL")
    return value


class ChainRuntimeSpec(_ConfigModel):
    chain_id: int = Field(gt=0)
    uses_poa_extra_data: bool
    nominal_block_time_seconds: float = Field(gt=0.0)


class ChainSpec(_ConfigModel):
    name: str
    runtime: ChainRuntimeSpec

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return validate_path_segment(value, label="chain.name")


class ProblemSpec(_ConfigModel):
    id: str
    lookback_seconds: int = Field(gt=0)
    max_delay_seconds: int = Field(gt=0)
    compiler: SerializeAsAny[ProblemCompilerConfig]
    execution_policy: SerializeAsAny[ExecutionPolicyConfig]

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return validate_path_segment(value, label="problem.id")


def coerce_problem_spec(payload: object) -> ProblemSpec:
    from ..temporal.compilers import coerce_problem_compiler_config

    raw_payload = owner_payload(payload, owner="problem", config_type=ProblemSpec)
    raw_compiler = (
        payload.compiler if isinstance(payload, ProblemSpec) else raw_payload.get("compiler")
    )
    if raw_compiler is None:
        raise ConfigResolutionError("problem.compiler is required")
    raw_execution_policy = (
        payload.execution_policy
        if isinstance(payload, ProblemSpec)
        else raw_payload.get("execution_policy")
    )
    if raw_execution_policy is None:
        raise ConfigResolutionError("problem.execution_policy is required")
    from ..temporal.execution_policy import coerce_execution_policy_config

    compiler = coerce_problem_compiler_config(raw_compiler)
    execution_policy = coerce_execution_policy_config(raw_execution_policy)
    if (
        isinstance(payload, ProblemSpec)
        and compiler is payload.compiler
        and execution_policy is payload.execution_policy
    ):
        return payload
    raw_payload["compiler"] = compiler
    raw_payload["execution_policy"] = execution_policy
    return validate_owner_config(raw_payload, ProblemSpec)


class SplitConfig(_ConfigModel):
    train_fraction: float = Field(gt=0.0, lt=1.0)
    validation_fraction: float = Field(ge=0.0, lt=1.0)

    @model_validator(mode="after")
    def validate_split(self) -> Self:
        if self.train_fraction + self.validation_fraction >= 1.0:
            raise ValueError("train_fraction + validation_fraction must be less than 1")
        return self


class SequenceConfig(_ConfigModel):
    min_length: int = Field(gt=0)
    max_length: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        if self.max_length < self.min_length:
            raise ValueError("training.sequence.max_length must be >= min_length")
        return self


class AcquisitionRpcConfig(_ConfigModel):
    batch_size: int = Field(gt=0)
    concurrency: int = Field(gt=0)
    min_batch_size: int = Field(gt=0)
    concurrency_rungs: list[int] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_runtime(self) -> Self:
        if self.min_batch_size > self.batch_size:
            raise ValueError("acquisition.rpc.min_batch_size must be <= batch_size")
        if sorted(self.concurrency_rungs) != self.concurrency_rungs:
            raise ValueError("acquisition.rpc.concurrency_rungs must be sorted ascending")
        if len(set(self.concurrency_rungs)) != len(self.concurrency_rungs):
            raise ValueError("acquisition.rpc.concurrency_rungs must not contain duplicates")
        if any(value <= 0 for value in self.concurrency_rungs):
            raise ValueError("acquisition.rpc.concurrency_rungs values must be positive")
        if self.concurrency not in self.concurrency_rungs:
            raise ValueError("acquisition.rpc.concurrency must be present in concurrency_rungs")
        return self


class AcquisitionConfig(_ConfigModel):
    dry_run: bool = False
    chunk_size: int = Field(gt=0)
    rpc: AcquisitionRpcConfig


class FeaturesConfig(_ConfigModel):
    id: str
    outputs: list[str] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return validate_path_segment(value, label="features.id")

    @field_validator("outputs")
    @classmethod
    def validate_outputs(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("features.outputs must not contain duplicates")
        return value

    @model_validator(mode="after")
    def validate_feature_selection(self) -> Self:
        validate_feature_selection(self.id, tuple(self.outputs))
        return self


def coerce_features_config(payload: object) -> FeaturesConfig:
    if isinstance(payload, FeaturesConfig):
        return payload
    return validate_owner_config(
        owner_payload(payload, owner="features", config_type=FeaturesConfig),
        FeaturesConfig,
    )


class ProviderEndpointConfig(_ConfigModel):
    url: str
    reference: str | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return _validate_http_endpoint_url(value, label="provider.endpoints.url")


class ProviderTransportConfig(_ConfigModel):
    timeout_seconds: float = Field(gt=0.0)
    retry_count: int = Field(ge=0)
    backoff_factor: float = Field(ge=0.0)


class ResolvedRpcEndpointConfig(_ConfigModel):
    provider_name: str
    url: str
    reference: str
    timeout_seconds: float = Field(gt=0.0)
    retry_count: int = Field(ge=0)
    backoff_factor: float = Field(ge=0.0)

    @field_validator("provider_name")
    @classmethod
    def validate_provider_name(cls, value: str) -> str:
        return validate_path_segment(value, label="rpc_endpoint.provider_name")

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return _validate_http_endpoint_url(value, label="rpc_endpoint.url")


class ProviderSpec(_ConfigModel):
    name: str
    transport: ProviderTransportConfig
    acquisition: AcquisitionConfig | None = None
    endpoints: dict[str, ProviderEndpointConfig]

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return validate_path_segment(value, label="provider.name")

    @model_validator(mode="after")
    def validate_chain_coverage(self) -> Self:
        if not self.endpoints:
            raise ValueError("provider.endpoints must not be empty")
        for name in self.endpoints:
            validate_path_segment(name, label="provider.endpoints key")
        return self

    def endpoint_config_for(self, chain_name: str) -> ProviderEndpointConfig:
        try:
            return self.endpoints[chain_name]
        except KeyError as exc:
            raise ConfigResolutionError(
                f"provider {self.name} does not define endpoint for {chain_name}"
            ) from exc


class AcquireConfig(WorkflowConfig):
    workflow: WorkflowTask = WorkflowTask.ACQUIRE
    problem: ProblemSpec
    features: FeaturesConfig
    rpc_endpoint: ResolvedRpcEndpointConfig
    acquisition: AcquisitionConfig
