"""Typed tuning-space and tuned-parameter helpers."""

from __future__ import annotations

from ..config.models import (
    ProblemSpec,
    TunedParameterSet,
    TunedProblemParams,
    TunedTrainingParams,
    TuningProblemSearchSpace,
    TuningSpaceConfig,
    TuningTrainingSearchSpace,
)
from ..core.errors import ConfigResolutionError
from ..core.specs import (
    owner_payload,
    owner_payload_id,
    require_spec_config,
    validate_owner_config,
)
from .families.base import ModelTuningSpaceConfig, TunedModelParams
from .families.registry import model_spec


def coerce_tuning_space_config(
    payload: object,
    *,
    model_config,
    problem_config: ProblemSpec | None = None,
) -> TuningSpaceConfig | None:
    if payload is None:
        return None
    if isinstance(payload, TuningSpaceConfig):
        training_payload = payload.training
        problem_payload = payload.problem
        model_payload = payload.model
    else:
        raw_payload = owner_payload(
            payload,
            owner="tuning_space",
            config_type=TuningSpaceConfig,
        )
        if "model" not in raw_payload:
            raise ConfigResolutionError("tuning_space.model is required")
        training_payload = raw_payload.get("training")
        problem_payload = raw_payload.get("problem")
        model_payload = raw_payload["model"]
    raw_model_payload, model_id = owner_payload_id(
        model_payload,
        owner="tuning_space.model",
        config_type=ModelTuningSpaceConfig,
        id_label="tuning_space.model.id",
    )
    spec = model_spec(model_id)
    if model_id != model_config.id:
        raise ConfigResolutionError("tuning_space.model.id must match model.id")
    training = (
        None
        if training_payload is None
        else training_payload
        if isinstance(training_payload, TuningTrainingSearchSpace)
        else validate_owner_config(
            owner_payload(
                training_payload,
                owner="tuning_space.training",
                config_type=TuningTrainingSearchSpace,
            ),
            TuningTrainingSearchSpace,
        )
    )
    problem = (
        None
        if problem_payload is None
        else _coerce_problem_tuning_space(problem_payload, problem_config=problem_config)
    )
    model: ModelTuningSpaceConfig[str]
    if isinstance(model_payload, spec.tuning_space_type):
        model = require_spec_config(
            model_payload,
            spec.tuning_space_type,
            "tuning_space.model",
        )
    else:
        model = validate_owner_config(raw_model_payload, spec.tuning_space_type)
    if spec.validate_tuning_space is not None:
        spec.validate_tuning_space(model_config, model)
    return TuningSpaceConfig(
        training=training,
        problem=problem,
        model=model,
    )


def coerce_tuned_parameter_set(
    payload: object,
    *,
    model_id: str | None = None,
) -> TunedParameterSet:
    if isinstance(payload, TunedParameterSet):
        training_payload = payload.training
        problem_payload = payload.problem
        model_payload = payload.model
    else:
        raw_payload = owner_payload(
            payload,
            owner="tuned parameters",
            config_type=TunedParameterSet,
        )
        training_payload = raw_payload.get("training")
        problem_payload = raw_payload.get("problem")
        model_payload = raw_payload.get("model")
    training = (
        None
        if training_payload is None
        else training_payload
        if isinstance(training_payload, TunedTrainingParams)
        else validate_owner_config(
            owner_payload(
                training_payload,
                owner="tuned parameters.training",
                config_type=TunedTrainingParams,
            ),
            TunedTrainingParams,
        )
    )
    problem = (
        None
        if problem_payload is None
        else problem_payload
        if isinstance(problem_payload, TunedProblemParams)
        else validate_owner_config(
            owner_payload(
                problem_payload,
                owner="tuned parameters.problem",
                config_type=TunedProblemParams,
            ),
            TunedProblemParams,
        )
    )
    model: TunedModelParams[str] | None = None
    if model_payload is not None:
        raw_model_payload, resolved_model_id = owner_payload_id(
            model_payload,
            owner="tuned model params",
            config_type=TunedModelParams,
            id_label="model.id",
        )
        spec = model_spec(resolved_model_id)
        if isinstance(model_payload, spec.tuned_params_type):
            model = require_spec_config(
                model_payload,
                spec.tuned_params_type,
                "tuned model params",
            )
        else:
            model = validate_owner_config(raw_model_payload, spec.tuned_params_type)
        if model_id is not None and resolved_model_id != model_id:
            raise ConfigResolutionError("Tuned model params id does not match model.id")
    if (
        isinstance(payload, TunedParameterSet)
        and training is payload.training
        and problem is payload.problem
        and model is payload.model
    ):
        return payload
    return TunedParameterSet(training=training, problem=problem, model=model)


def _coerce_problem_tuning_space(
    payload: object,
    *,
    problem_config: ProblemSpec | None,
) -> TuningProblemSearchSpace:
    if problem_config is None:
        raise ConfigResolutionError(
            "problem_config is required when tuning_space.problem is provided"
        )
    if isinstance(payload, TuningProblemSearchSpace):
        return payload
    return validate_owner_config(
        owner_payload(
            payload,
            owner="tuning_space.problem",
            config_type=TuningProblemSearchSpace,
        ),
        TuningProblemSearchSpace,
    )
