"""Workflow request handling and payload resolution."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeVar, cast, overload

from pydantic import Field, ValidationError

from ..core.errors import ConfigResolutionError
from ..modeling.families.base import ConfigModel, ModelConfig
from ..modeling.families.registry import coerce_model_config, coerce_tuning_space_config
from ..objectives import ObjectiveConfig, coerce_objective_config
from ._mapping import mapping_copy, require_mapping
from .models import (
    AcquireConfig,
    AcquisitionConfig,
    ArtifactConfig,
    ChainSpec,
    DatasetBuilderConfig,
    DatasetSpec,
    EvaluateConfig,
    EvaluationConfig,
    FeatureSetConfig,
    PredictionConfig,
    ProblemSpec,
    ProviderSpec,
    ResolvedRpcEndpointConfig,
    SplitConfig,
    StorageSpec,
    StudyConfig,
    TrainConfig,
    TrainingConfig,
    TuneConfig,
    TuningConfig,
    TuningSpaceConfig,
    WorkflowTask,
    coerce_dataset_builder_config,
    coerce_feature_set_config,
    coerce_prediction_config,
    coerce_problem_spec,
)
from .presets import workflow_payload
from .registry import list_group_names, load_named_group

_MODEL_GROUP = "model"
_TUNING_SPACE_GROUP = "tuning_space"

ModelT = TypeVar("ModelT", bound=ConfigModel)
WorkflowConfig = AcquireConfig | TrainConfig | TuneConfig | EvaluateConfig


class WorkflowRequest(ConfigModel):
    preset: str | None = None
    chain: str | None = None
    study: str | None = None
    variant: str | None = None
    delay_seconds: int | None = Field(default=None, gt=0)
    trial_count: int | None = Field(default=None, gt=0)
    storage_root: Path | None = None
    dry_run: bool | None = None


@dataclass(frozen=True, slots=True)
class _ResolvedModelWorkflowBase:
    dataset: DatasetSpec
    chain: ChainSpec
    storage: StorageSpec
    problem: ProblemSpec
    model: ModelConfig[str]
    dataset_builder: DatasetBuilderConfig
    feature_set: FeatureSetConfig
    prediction: PredictionConfig
    objective: ObjectiveConfig
    study: StudyConfig
    artifact: ArtifactConfig


@dataclass(frozen=True, slots=True)
class _ResolvedModelWorkflowSpine:
    training: TrainingConfig
    split: SplitConfig
    tuning: TuningConfig | None
    tuning_space: TuningSpaceConfig | None


def load_named_tuning_space(
    name: str,
    *,
    model_config: ModelConfig[str],
    problem_config: ProblemSpec,
    prediction_config: PredictionConfig,
) -> TuningSpaceConfig:
    tuning_space = coerce_tuning_space_config(
        load_named_group(name, _TUNING_SPACE_GROUP),
        model_config=model_config,
        problem_config=problem_config,
        prediction_config=prediction_config,
    )
    if tuning_space is None:
        raise ConfigResolutionError(f"tuning space {name} resolved to None")
    return tuning_space


@overload
def resolve_workflow_config(
    workflow_kind: Literal[WorkflowTask.ACQUIRE],
    request: WorkflowRequest,
) -> AcquireConfig: ...


@overload
def resolve_workflow_config(
    workflow_kind: Literal[WorkflowTask.TRAIN],
    request: WorkflowRequest,
) -> TrainConfig: ...


@overload
def resolve_workflow_config(
    workflow_kind: Literal[WorkflowTask.TUNE],
    request: WorkflowRequest,
) -> TuneConfig: ...


@overload
def resolve_workflow_config(
    workflow_kind: Literal[WorkflowTask.EVALUATE],
    request: WorkflowRequest,
) -> EvaluateConfig: ...


def resolve_workflow_config(
    workflow_kind: WorkflowTask,
    request: WorkflowRequest,
) -> WorkflowConfig:
    """Resolve one workflow request into one validated workflow config."""

    try:
        payload = workflow_payload(
            workflow=workflow_kind,
            preset=request.preset,
            chain=request.chain,
            study=request.study,
            variant=request.variant,
            delay_seconds=request.delay_seconds,
            trial_count=request.trial_count,
            storage_root=request.storage_root,
            dry_run=request.dry_run,
            validate_parent=_validate_parent_preset,
        )
        return _resolve_payload_for_workflow(workflow_kind, payload)
    except ConfigResolutionError:
        raise
    except (ValidationError, ValueError, TypeError) as exc:
        raise ConfigResolutionError(str(exc)) from exc


def _validate_parent_preset(name: str, payload: dict[str, object]) -> None:
    for workflow in WorkflowTask:
        try:
            _resolve_payload_for_workflow(workflow, dict(payload))
        except (ConfigResolutionError, ValidationError, ValueError, TypeError) as exc:
            raise ConfigResolutionError(
                f"Parent preset {name} is not runnable for {workflow.value}: {exc}"
            ) from exc


def _resolve_payload_for_workflow(
    workflow: WorkflowTask,
    payload: dict[str, object],
) -> WorkflowConfig:
    if workflow is WorkflowTask.ACQUIRE:
        return _resolve_acquire_config(payload)
    if workflow is WorkflowTask.TRAIN:
        return _resolve_train_config(payload)
    if workflow is WorkflowTask.TUNE:
        return _resolve_tune_config(payload)
    if workflow is WorkflowTask.EVALUATE:
        return _resolve_evaluate_config(payload)
    raise ConfigResolutionError(f"Unsupported workflow: {workflow.value}")


def _require_payload_key(payload: Mapping[str, object], key: str) -> object:
    if key not in payload:
        raise ConfigResolutionError(f"Missing required workflow config field: {key}")
    return payload[key]


def resolve_named_or_inline(raw: object, *, group: str, model_type: type[ModelT]) -> ModelT:
    return _resolve_named_or_mapping(
        raw,
        group=group,
        label=group,
        parse_mapping=model_type.model_validate,
    )


def _resolve_named_or_mapping(
    raw: object,
    *,
    group: str,
    label: str,
    parse_mapping: Callable[[dict[str, object]], ModelT],
) -> ModelT:
    if isinstance(raw, str):
        return parse_mapping(load_named_group(raw, group))
    if isinstance(raw, Mapping):
        return parse_mapping(mapping_copy(cast(Mapping[object, object], raw)))
    raise ConfigResolutionError(f"{label} must be provided as a spec name or mapping")


def resolve_inline(raw: object, *, label: str, model_type: type[ModelT]) -> ModelT:
    return model_type.model_validate(require_mapping(raw, label=label))


def resolve_problem(raw: object) -> ProblemSpec:
    return _resolve_named_or_mapping(
        raw,
        group="problem",
        label="problem",
        parse_mapping=coerce_problem_spec,
    )


def resolve_feature_set(raw: object) -> FeatureSetConfig:
    return _resolve_named_or_mapping(
        raw,
        group="feature_set",
        label="feature_set",
        parse_mapping=coerce_feature_set_config,
    )


def resolve_dataset_builder(raw: object) -> DatasetBuilderConfig:
    return _resolve_named_or_mapping(
        raw,
        group="dataset_builder",
        label="dataset_builder",
        parse_mapping=coerce_dataset_builder_config,
    )


def resolve_evaluation(raw: object) -> EvaluationConfig:
    return resolve_named_or_inline(raw, group="evaluation", model_type=EvaluationConfig)


def resolve_objective(raw: object) -> ObjectiveConfig:
    return _resolve_named_or_mapping(
        raw,
        group="objective",
        label="objective",
        parse_mapping=coerce_objective_config,
    )


def resolve_prediction(raw: object) -> PredictionConfig:
    return _resolve_named_or_mapping(
        raw,
        group="prediction",
        label="prediction",
        parse_mapping=coerce_prediction_config,
    )


def _resolve_model(raw: object) -> ModelConfig[str]:
    return _resolve_named_or_mapping(
        raw,
        group=_MODEL_GROUP,
        label="model",
        parse_mapping=coerce_model_config,
    )


def _resolve_tuning_space(
    raw: object,
    *,
    model_config: ModelConfig[str],
    problem_config: ProblemSpec,
    prediction_config: PredictionConfig,
) -> TuningSpaceConfig:
    if isinstance(raw, str):
        return load_named_tuning_space(
            raw,
            model_config=model_config,
            problem_config=problem_config,
            prediction_config=prediction_config,
        )
    if isinstance(raw, Mapping):
        resolved = coerce_tuning_space_config(
            mapping_copy(cast(Mapping[object, object], raw)),
            model_config=model_config,
            problem_config=problem_config,
            prediction_config=prediction_config,
        )
        if resolved is None:
            raise ConfigResolutionError("tuning_space is required for tune")
        return resolved
    raise ConfigResolutionError("tuning_space must be provided as a spec name or mapping")


def _resolve_tuning_definition(
    payload: dict[str, object],
    *,
    model_config: ModelConfig[str],
    problem_config: ProblemSpec,
    prediction_config: PredictionConfig,
) -> tuple[TuningConfig, TuningSpaceConfig]:
    tuning_spec = resolve_inline(
        _require_payload_key(payload, "tuning"),
        label="tuning",
        model_type=TuningConfig,
    )
    tuning_space_spec = _resolve_tuning_space(
        _require_payload_key(payload, "tuning_space"),
        model_config=model_config,
        problem_config=problem_config,
        prediction_config=prediction_config,
    )
    return tuning_spec, tuning_space_spec


def resolve_storage(raw: object | None) -> StorageSpec:
    if raw is None:
        return StorageSpec()
    if isinstance(raw, (str, Path)):
        return StorageSpec(root=Path(raw))
    return StorageSpec.model_validate(require_mapping(raw, label="storage"))


def _resolve_common(payload: dict[str, object]) -> tuple[DatasetSpec, ChainSpec, StorageSpec]:
    dataset = resolve_named_or_inline(
        _require_payload_key(payload, "dataset"),
        group="dataset",
        model_type=DatasetSpec,
    )
    chain = resolve_named_or_inline(
        _require_payload_key(payload, "chain"),
        group="chain",
        model_type=ChainSpec,
    )
    storage = resolve_storage(payload.get("storage"))
    return dataset, chain, storage


def _resolve_rpc_endpoint(
    payload: dict[str, object],
    *,
    chain: ChainSpec,
) -> ResolvedRpcEndpointConfig:
    raw_provider = _require_payload_key(payload, "provider")
    if not isinstance(raw_provider, str):
        raise ConfigResolutionError("provider must be provided as a named provider spec")

    provider = ProviderSpec.model_validate(load_named_group(raw_provider, "provider"))
    unknown_chains = sorted(set(provider.endpoints) - set(list_group_names("chain")))
    if unknown_chains:
        raise ConfigResolutionError(
            f"provider {provider.name} declares unknown chains: {', '.join(unknown_chains)}"
        )
    endpoint = provider.endpoint_config_for(chain.name)
    return ResolvedRpcEndpointConfig(
        provider_name=provider.name,
        url=endpoint.url,
        reference=endpoint.reference or endpoint.url,
        timeout_seconds=provider.transport.timeout_seconds,
        retry_count=provider.transport.retry_count,
        backoff_factor=provider.transport.backoff_factor,
    )


def _resolve_model_workflow_base(payload: dict[str, object]) -> _ResolvedModelWorkflowBase:
    dataset, chain, storage = _resolve_common(payload)
    return _ResolvedModelWorkflowBase(
        dataset=dataset,
        chain=chain,
        storage=storage,
        problem=resolve_problem(_require_payload_key(payload, "problem")),
        model=_resolve_model(_require_payload_key(payload, "model")),
        dataset_builder=resolve_dataset_builder(_require_payload_key(payload, "dataset_builder")),
        feature_set=resolve_feature_set(_require_payload_key(payload, "feature_set")),
        prediction=resolve_prediction(_require_payload_key(payload, "prediction")),
        objective=resolve_objective(_require_payload_key(payload, "objective")),
        study=_resolve_study(payload.get("study")),
        artifact=_resolve_artifact(payload.get("artifact")),
    )


def _resolve_study(raw: object) -> StudyConfig:
    if isinstance(raw, Mapping):
        return StudyConfig.model_validate(raw)
    if isinstance(raw, str):
        return StudyConfig(name=raw)
    return StudyConfig()


def _resolve_artifact(raw: object) -> ArtifactConfig:
    if isinstance(raw, Mapping):
        return ArtifactConfig.model_validate(raw)
    return ArtifactConfig()


def _resolve_model_workflow_spine(
    payload: dict[str, object],
    *,
    base: _ResolvedModelWorkflowBase,
    require_tuning: bool,
    allow_tuned_variant: bool,
) -> _ResolvedModelWorkflowSpine:
    training = resolve_inline(
        _require_payload_key(payload, "training"),
        label="training",
        model_type=TrainingConfig,
    )
    split = resolve_inline(
        _require_payload_key(payload, "split"),
        label="split",
        model_type=SplitConfig,
    )
    if require_tuning or (allow_tuned_variant and base.artifact.variant.value == "tuned"):
        tuning, tuning_space = _resolve_tuning_definition(
            payload,
            model_config=base.model,
            problem_config=base.problem,
            prediction_config=base.prediction,
        )
        return _ResolvedModelWorkflowSpine(
            training=training,
            split=split,
            tuning=tuning,
            tuning_space=tuning_space,
        )
    return _ResolvedModelWorkflowSpine(
        training=training,
        split=split,
        tuning=None,
        tuning_space=None,
    )


def _resolve_acquire_config(payload: dict[str, object]) -> AcquireConfig:
    dataset_spec, chain_spec, storage_spec = _resolve_common(payload)
    problem_spec = resolve_problem(_require_payload_key(payload, "problem"))
    rpc_endpoint = _resolve_rpc_endpoint(payload, chain=chain_spec)
    feature_set_spec = resolve_feature_set(_require_payload_key(payload, "feature_set"))
    acquisition_spec = resolve_inline(
        _require_payload_key(payload, "acquisition"),
        label="acquisition",
        model_type=AcquisitionConfig,
    )
    return AcquireConfig(
        chain=chain_spec,
        dataset=dataset_spec,
        storage=storage_spec,
        problem=problem_spec,
        feature_set=feature_set_spec,
        rpc_endpoint=rpc_endpoint,
        acquisition=acquisition_spec,
    )


def _resolve_train_config(payload: dict[str, object]) -> TrainConfig:
    base = _resolve_model_workflow_base(payload)
    spine = _resolve_model_workflow_spine(
        payload,
        base=base,
        require_tuning=False,
        allow_tuned_variant=True,
    )
    return TrainConfig(
        chain=base.chain,
        dataset=base.dataset,
        storage=base.storage,
        problem=base.problem,
        model=base.model,
        dataset_builder=base.dataset_builder,
        feature_set=base.feature_set,
        prediction=base.prediction,
        objective=base.objective,
        study=base.study,
        artifact=base.artifact,
        training=spine.training,
        split=spine.split,
        tuning=spine.tuning,
        tuning_space=spine.tuning_space,
    )


def _resolve_tune_config(payload: dict[str, object]) -> TuneConfig:
    base = _resolve_model_workflow_base(payload)
    spine = _resolve_model_workflow_spine(
        payload,
        base=base,
        require_tuning=True,
        allow_tuned_variant=False,
    )
    assert spine.tuning is not None
    assert spine.tuning_space is not None
    return TuneConfig(
        chain=base.chain,
        dataset=base.dataset,
        storage=base.storage,
        problem=base.problem,
        model=base.model,
        dataset_builder=base.dataset_builder,
        feature_set=base.feature_set,
        prediction=base.prediction,
        objective=base.objective,
        study=base.study,
        artifact=base.artifact,
        training=spine.training,
        split=spine.split,
        tuning=spine.tuning,
        tuning_space=spine.tuning_space,
    )


def _resolve_evaluate_config(payload: dict[str, object]) -> EvaluateConfig:
    base = _resolve_model_workflow_base(payload)
    spine = _resolve_model_workflow_spine(
        payload,
        base=base,
        require_tuning=False,
        allow_tuned_variant=True,
    )
    evaluation_spec = resolve_evaluation(_require_payload_key(payload, "evaluation"))
    delay_raw = _require_payload_key(payload, "delay_seconds")
    if not isinstance(delay_raw, int):
        raise ConfigResolutionError("delay_seconds must be an integer")
    return EvaluateConfig(
        chain=base.chain,
        dataset=base.dataset,
        storage=base.storage,
        problem=base.problem,
        model=base.model,
        dataset_builder=base.dataset_builder,
        feature_set=base.feature_set,
        prediction=base.prediction,
        objective=base.objective,
        study=base.study,
        artifact=base.artifact,
        training=spine.training,
        split=spine.split,
        evaluation=evaluation_spec,
        delay_seconds=delay_raw,
        tuning=spine.tuning,
        tuning_space=spine.tuning_space,
    )
