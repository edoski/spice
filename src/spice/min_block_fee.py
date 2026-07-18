# pyright: strict

"""Architecture-neutral minimum-block-fee target, loss, and decode contract."""

from __future__ import annotations

import typing as _typing
from dataclasses import dataclass as _dataclass

import numpy as _np
import torch as _torch
import torch.nn.functional as _functional
from numpy.typing import NDArray as _NDArray
from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict as _ConfigDict
from pydantic import Field as _Field

__all__ = [
    "TargetState",
    "ClassificationLossState",
    "MinBlockFeeOutput",
    "MinBlockFeeLoss",
    "fit_target_state",
    "standardize_target",
    "target_natural_log",
    "fit_classification_loss_state",
    "min_block_fee_loss",
    "decode_action",
]

_StrictFiniteFloat: _typing.TypeAlias = _typing.Annotated[
    float,
    _Field(strict=True, allow_inf_nan=False),
]
_StrictPositiveFloat: _typing.TypeAlias = _typing.Annotated[
    float,
    _Field(strict=True, gt=0.0, allow_inf_nan=False),
]
_StrictPositiveInt: _typing.TypeAlias = _typing.Annotated[int, _Field(strict=True, gt=0)]


class _State(_BaseModel):
    model_config = _ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        revalidate_instances="always",
    )


class TargetState(_State):
    mean: _StrictFiniteFloat
    standard_deviation: _StrictPositiveFloat


class ClassificationLossState(_State):
    class_support: _typing.Annotated[tuple[_StrictPositiveInt, ...], _Field(min_length=1)]


class MinBlockFeeOutput(_typing.NamedTuple):
    action_logits: _torch.Tensor
    minimum_fee_z: _torch.Tensor


@_dataclass(frozen=True, slots=True)
class MinBlockFeeLoss:
    mean_total: _torch.Tensor
    total_by_origin: _torch.Tensor
    classification_by_origin: _torch.Tensor
    regression_by_origin: _torch.Tensor


def _require_int64_vector(values: object, name: str) -> _NDArray[_np.int64]:
    if not isinstance(values, _np.ndarray):
        raise TypeError(f"{name} must be a numpy.ndarray")
    array = _typing.cast(_NDArray[_np.generic], values)
    if array.dtype != _np.dtype(_np.int64):
        raise TypeError(f"{name} must have dtype int64")
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if array.size == 0:
        raise ValueError(f"{name} must be nonempty")
    return _typing.cast(_NDArray[_np.int64], array)


def _require_positive(values: _NDArray[_np.int64], name: str) -> None:
    if _np.any(values <= 0):
        raise ValueError(f"{name} must contain only positive values")


def _natural_log(values: _NDArray[_np.int64]) -> _NDArray[_np.float64]:
    result = _np.log(values.astype(_np.float64, copy=False))
    if not _np.isfinite(result).all():
        raise ValueError("natural-log targets must be finite")
    return _typing.cast(_NDArray[_np.float64], result)


def fit_target_state(raw_minima: _NDArray[_np.int64]) -> TargetState:
    minima = _require_int64_vector(raw_minima, "raw_minima")
    _require_positive(minima, "raw_minima")
    natural_log = _natural_log(minima)
    mean = float(natural_log.mean(dtype=_np.float64))
    standard_deviation = float(natural_log.std(dtype=_np.float64, ddof=0))
    if not _np.isfinite(mean) or not _np.isfinite(standard_deviation):
        raise ValueError("target statistics must be finite")
    if standard_deviation == 0.0:
        raise ValueError("raw_minima must not be constant")
    return TargetState(mean=mean, standard_deviation=standard_deviation)


def standardize_target(
    raw_minima: _NDArray[_np.int64],
    state: TargetState,
) -> _NDArray[_np.float32]:
    minima = _require_int64_vector(raw_minima, "raw_minima")
    _require_positive(minima, "raw_minima")
    standardized = (_natural_log(minima) - state.mean) / state.standard_deviation
    result = _np.ascontiguousarray(standardized, dtype=_np.float32)
    if not _np.isfinite(result).all():
        raise ValueError("standardized targets must be finite")
    return result


def _require_floating_vector(values: object, name: str) -> _torch.Tensor:
    if not isinstance(values, _torch.Tensor):
        raise TypeError(f"{name} must be a torch.Tensor")
    if values.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if values.numel() == 0:
        raise ValueError(f"{name} must be nonempty")
    if not values.is_floating_point():
        raise TypeError(f"{name} must have a floating dtype")
    if not _torch.isfinite(values).all():
        raise ValueError(f"{name} must be finite")
    return values


def target_natural_log(target_z: _torch.Tensor, state: TargetState) -> _torch.Tensor:
    standardized = _require_floating_vector(target_z, "target_z").to(dtype=_torch.float64)
    result = state.mean + state.standard_deviation * standardized
    if not _torch.isfinite(result).all():
        raise ValueError("natural-log targets must be finite")
    return result


def fit_classification_loss_state(
    labels: _NDArray[_np.int64],
    *,
    horizon_blocks: int,
    classification_loss: _typing.Literal["unweighted", "corrected_inverse_frequency"],
) -> ClassificationLossState | None:
    label_values = _require_int64_vector(labels, "labels")
    if type(horizon_blocks) is not int:
        raise TypeError("horizon_blocks must be an int")
    if horizon_blocks <= 0:
        raise ValueError("horizon_blocks must be positive")
    if classification_loss not in {"unweighted", "corrected_inverse_frequency"}:
        raise ValueError(
            "classification_loss must be 'unweighted' or 'corrected_inverse_frequency'"
        )
    if _np.any(label_values < 0) or _np.any(label_values >= horizon_blocks):
        raise ValueError("labels must be in [0, horizon_blocks)")
    if classification_loss == "unweighted":
        return None

    support = _np.bincount(label_values, minlength=horizon_blocks)
    if _np.any(support == 0):
        raise ValueError(
            "corrected_inverse_frequency classification loss requires support for every class"
        )
    return ClassificationLossState(class_support=tuple(int(count) for count in support))


def _require_output(output: MinBlockFeeOutput) -> tuple[_torch.Tensor, _torch.Tensor, int, int]:
    logits = output.action_logits
    minimum_fee_z = output.minimum_fee_z
    if logits.ndim != 2:
        raise ValueError("action_logits must have shape [B, K]")
    batch_size, class_count = logits.shape
    if batch_size == 0 or class_count == 0:
        raise ValueError("action_logits must have nonempty batch and class dimensions")
    if not logits.is_floating_point():
        raise TypeError("action_logits must have a floating dtype")
    if not _torch.isfinite(logits).all():
        raise ValueError("action_logits must be finite")

    fee_values = _require_floating_vector(minimum_fee_z, "minimum_fee_z")
    if fee_values.shape[0] != batch_size:
        raise ValueError("output heads must have matching batch dimensions")
    return logits, fee_values, batch_size, class_count


def _require_labels(
    labels: object,
    *,
    batch_size: int,
    class_count: int,
) -> _torch.Tensor:
    if not isinstance(labels, _torch.Tensor):
        raise TypeError("labels must be a torch.Tensor")
    if labels.ndim != 1 or labels.shape[0] != batch_size:
        raise ValueError("labels must have shape [B]")
    if labels.dtype != _torch.int64:
        raise TypeError("labels must have dtype int64")
    if _torch.any(labels < 0) or _torch.any(labels >= class_count):
        raise ValueError("labels must be valid class indices")
    return labels


def min_block_fee_loss(
    output: MinBlockFeeOutput,
    *,
    label: _torch.Tensor,
    target: _torch.Tensor,
    classification_state: ClassificationLossState | None,
) -> MinBlockFeeLoss:
    logits, minimum_fee_z, batch_size, class_count = _require_output(output)
    label_values = _require_labels(
        label,
        batch_size=batch_size,
        class_count=class_count,
    )
    target_values = _require_floating_vector(target, "target")
    if target_values.shape[0] != batch_size:
        raise ValueError("target must have shape [B]")

    weights: _torch.Tensor | None = None
    if classification_state is not None:
        support = classification_state.class_support
        total_support = sum(support)
        width = len(support)
        weights = logits.new_tensor([total_support / (width * count) for count in support])

    classification = _functional.cross_entropy(
        logits,
        label_values,
        weight=weights,
        reduction="none",
    )
    regression = _functional.smooth_l1_loss(
        minimum_fee_z,
        target_values,
        reduction="none",
    )
    total = classification + regression
    return MinBlockFeeLoss(
        mean_total=total.sum() / batch_size,
        total_by_origin=total.detach(),
        classification_by_origin=classification.detach(),
        regression_by_origin=regression.detach(),
    )


def decode_action(output: MinBlockFeeOutput) -> _torch.Tensor:
    logits, _, _, _ = _require_output(output)
    return logits.argmax(dim=-1)
