"""Strict request and definition values."""

from __future__ import annotations

from typing import Annotated, Literal, Self, TypeAlias

from pydantic import UUID4, BaseModel, ConfigDict, Field, TypeAdapter, model_validator

_PositiveInt: TypeAlias = Annotated[int, Field(strict=True, gt=0)]
_NonNegativeInt: TypeAlias = Annotated[int, Field(strict=True, ge=0)]
_PositiveFloat: TypeAlias = Annotated[
    float,
    Field(strict=True, gt=0.0, allow_inf_nan=False),
]
_NonNegativeFloat: TypeAlias = Annotated[
    float,
    Field(strict=True, ge=0.0, allow_inf_nan=False),
]
_Dropout: TypeAlias = Annotated[
    float,
    Field(strict=True, ge=0.0, lt=1.0, allow_inf_nan=False),
]
_FeatureName: TypeAlias = Annotated[str, Field(strict=True, min_length=1)]


class _FrozenRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")


def _validate_transformer_dimensions(model_width: int, attention_heads: int) -> None:
    if model_width % 2:
        raise ValueError("model_width must be even for sinusoidal positions")
    if model_width % attention_heads:
        raise ValueError("model_width must be divisible by attention_heads")


class CorpusDefinition(_FrozenRecord):
    chain_id: _PositiveInt
    first_block: _NonNegativeInt
    last_block: _NonNegativeInt

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        if self.last_block < self.first_block:
            raise ValueError("last_block must not precede first_block")
        return self


class CorpusRequest(_FrozenRecord):
    corpus_id: UUID4
    definition: CorpusDefinition


class OriginWindow(_FrozenRecord):
    role: Literal["training", "validation", "testing"]
    first_parent_block: _NonNegativeInt
    last_parent_block: _NonNegativeInt

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        if self.last_parent_block < self.first_parent_block:
            raise ValueError("last_parent_block must not precede first_parent_block")
        return self


class ExperimentSemantics(_FrozenRecord):
    training_window: OriginWindow
    validation_window: OriginWindow
    context_blocks: _PositiveInt
    horizon_blocks: _PositiveInt
    ordered_features: Annotated[tuple[_FeatureName, ...], Field(min_length=1)]
    classification_loss: Literal["unweighted", "corrected_inverse_frequency"]

    @model_validator(mode="after")
    def validate_semantics(self) -> Self:
        if self.training_window.role != "training":
            raise ValueError("training_window must carry role='training'")
        if self.validation_window.role != "validation":
            raise ValueError("validation_window must carry role='validation'")
        if (
            self.training_window.last_parent_block + self.horizon_blocks
            >= self.validation_window.first_parent_block
        ):
            raise ValueError("validation_window must follow complete training outcomes")
        if len(set(self.ordered_features)) != len(self.ordered_features):
            raise ValueError("ordered_features must not contain duplicates")
        return self


class LstmDefinition(_FrozenRecord):
    family: Literal["lstm"]
    projection: _PositiveInt
    hidden: _PositiveInt
    layers: _PositiveInt
    head_hidden: _PositiveInt
    dropout: _Dropout


class TransformerDefinition(_FrozenRecord):
    family: Literal["transformer"]
    model_width: _PositiveInt
    attention_heads: _PositiveInt
    transformer_layers: _PositiveInt
    feedforward_width: _PositiveInt
    head_hidden: _PositiveInt
    dropout: _Dropout

    @model_validator(mode="after")
    def validate_dimensions(self) -> Self:
        _validate_transformer_dimensions(self.model_width, self.attention_heads)
        return self


class TransformerLstmDefinition(_FrozenRecord):
    family: Literal["transformer_lstm"]
    model_width: _PositiveInt
    attention_heads: _PositiveInt
    transformer_layers: _PositiveInt
    feedforward_width: _PositiveInt
    lstm_hidden: _PositiveInt
    lstm_layers: _PositiveInt
    head_hidden: _PositiveInt
    dropout: _Dropout

    @model_validator(mode="after")
    def validate_dimensions(self) -> Self:
        _validate_transformer_dimensions(self.model_width, self.attention_heads)
        return self


ModelDefinition: TypeAlias = Annotated[
    LstmDefinition | TransformerDefinition | TransformerLstmDefinition,
    Field(discriminator="family"),
]


class LstmCapacity(_FrozenRecord):
    projection: _PositiveInt
    hidden: _PositiveInt
    layers: _PositiveInt
    head_hidden: _PositiveInt


class TransformerCapacity(_FrozenRecord):
    model_width: _PositiveInt
    attention_heads: _PositiveInt
    transformer_layers: _PositiveInt
    feedforward_width: _PositiveInt
    head_hidden: _PositiveInt

    @model_validator(mode="after")
    def validate_dimensions(self) -> Self:
        _validate_transformer_dimensions(self.model_width, self.attention_heads)
        return self


class TransformerLstmCapacity(_FrozenRecord):
    model_width: _PositiveInt
    attention_heads: _PositiveInt
    transformer_layers: _PositiveInt
    feedforward_width: _PositiveInt
    lstm_hidden: _PositiveInt
    lstm_layers: _PositiveInt
    head_hidden: _PositiveInt

    @model_validator(mode="after")
    def validate_dimensions(self) -> Self:
        _validate_transformer_dimensions(self.model_width, self.attention_heads)
        return self


class AdamWMethod(_FrozenRecord):
    learning_rate: _PositiveFloat
    weight_decay: _NonNegativeFloat


class FitMethod(_FrozenRecord):
    accumulation: Literal[1]
    gradient_clip_norm: _PositiveFloat
    scheduler: Literal["none"]
    seed: Literal[2026]
    max_epochs: Literal[36]
    validate_every_completed_epoch: Literal[1]
    patience: Literal[8]
    min_delta: _NonNegativeFloat
    improvement: Literal["strict_lower"]
    restore: Literal["earliest_best"]
    minimum_epoch_floor: Literal[False]

    @model_validator(mode="after")
    def validate_fixed_floats(self) -> Self:
        if self.gradient_clip_norm != 1.0:
            raise ValueError("gradient_clip_norm must equal 1.0")
        if self.min_delta != 0.0:
            raise ValueError("min_delta must equal 0.0")
        return self


class _MethodFields(_FrozenRecord):
    dropout: _Dropout
    optimizer: AdamWMethod
    training_batch: Literal[64]
    fit: FitMethod


class LstmMethod(_MethodFields):
    family: Literal["lstm"]
    capacity: LstmCapacity


class TransformerMethod(_MethodFields):
    family: Literal["transformer"]
    capacity: TransformerCapacity


class TransformerLstmMethod(_MethodFields):
    family: Literal["transformer_lstm"]
    capacity: TransformerLstmCapacity


Method: TypeAlias = Annotated[
    LstmMethod | TransformerMethod | TransformerLstmMethod,
    Field(discriminator="family"),
]


def _require_unique(label: str, values: tuple[object, ...]) -> None:
    if len(set(values)) != len(values):
        raise ValueError(f"{label} must not contain duplicates")


class _MethodSpaceFields(_FrozenRecord):
    dropouts: Annotated[tuple[_Dropout, ...], Field(min_length=1)]
    learning_rates: Annotated[tuple[_PositiveFloat, ...], Field(min_length=1)]
    weight_decays: Annotated[tuple[_NonNegativeFloat, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_unique_scalar_leaves(self) -> Self:
        _require_unique("dropouts", self.dropouts)
        _require_unique("learning_rates", self.learning_rates)
        _require_unique("weight_decays", self.weight_decays)
        return self


class LstmMethodSpace(_MethodSpaceFields):
    family: Literal["lstm"]
    capacities: Annotated[tuple[LstmCapacity, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_unique_capacities(self) -> Self:
        _require_unique("capacities", self.capacities)
        return self


class TransformerMethodSpace(_MethodSpaceFields):
    family: Literal["transformer"]
    capacities: Annotated[tuple[TransformerCapacity, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_unique_capacities(self) -> Self:
        _require_unique("capacities", self.capacities)
        return self


class TransformerLstmMethodSpace(_MethodSpaceFields):
    family: Literal["transformer_lstm"]
    capacities: Annotated[tuple[TransformerLstmCapacity, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_unique_capacities(self) -> Self:
        _require_unique("capacities", self.capacities)
        return self


MethodSpace: TypeAlias = Annotated[
    LstmMethodSpace | TransformerMethodSpace | TransformerLstmMethodSpace,
    Field(discriminator="family"),
]


class StudyDefinition(_FrozenRecord):
    experiment: ExperimentSemantics
    method_space: MethodSpace


class TrainingDefinition(_FrozenRecord):
    experiment: ExperimentSemantics
    model: ModelDefinition
    optimizer: AdamWMethod
    training_batch: Literal[64]
    fit: FitMethod


class BaselineSource(_FrozenRecord):
    kind: Literal["baseline"]
    corpus_id: UUID4
    training_definition: TrainingDefinition


class SelectedStudySource(_FrozenRecord):
    kind: Literal["selected_study"]
    corpus_id: UUID4
    study_id: UUID4
    experiment: ExperimentSemantics


TrainingSource: TypeAlias = Annotated[
    BaselineSource | SelectedStudySource,
    Field(discriminator="kind"),
]


class TrainRequest(_FrozenRecord):
    workflow: Literal["train"]
    artifact_id: UUID4
    source: TrainingSource


class TuneRequest(_FrozenRecord):
    workflow: Literal["tune"]
    study_id: UUID4
    corpus_id: UUID4
    study_definition: StudyDefinition


class EvaluateRequest(_FrozenRecord):
    workflow: Literal["evaluate"]
    evaluation_id: UUID4
    artifact_id: UUID4
    corpus_id: UUID4
    window: OriginWindow

    @model_validator(mode="after")
    def validate_window_role(self) -> Self:
        if self.window.role == "training":
            raise ValueError("evaluation window must carry role='validation' or role='testing'")
        return self


WorkflowRequest: TypeAlias = Annotated[
    TrainRequest | EvaluateRequest,
    Field(discriminator="workflow"),
]

WORKFLOW_REQUEST_ADAPTER = TypeAdapter(WorkflowRequest)
METHOD_ADAPTER = TypeAdapter(Method)
