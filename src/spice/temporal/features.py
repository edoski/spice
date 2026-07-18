"""Exact causal feature construction and scaling."""

from __future__ import annotations

import math
from typing import Annotated, Self

import numpy as np
import polars as pl
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, model_validator

_FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]
_PositiveFiniteFloat = Annotated[float, Field(gt=0.0, allow_inf_nan=False)]

_COMMON_PREFIX = ("log_base_fee_per_gas", "gas_utilization")
_ETHEREUM_PREFIX = (*_COMMON_PREFIX, "log_exact_forming_base_fee_per_gas")
_ACTIVITY_PAIR = ("log_gas_limit", "log1p_tx_count")
_HOUR_PAIR = ("hour_sin", "hour_cos")


class FeatureState(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        revalidate_instances="always",
    )

    means: Annotated[tuple[_FiniteFloat, ...], Field(min_length=1)]
    standard_deviations: Annotated[
        tuple[_PositiveFiniteFloat, ...],
        Field(min_length=1),
    ]

    @model_validator(mode="after")
    def validate_widths(self) -> Self:
        if len(self.means) != len(self.standard_deviations):
            raise ValueError("means and standard_deviations must have equal widths")
        return self


def fit_feature_state(
    training_support: pl.DataFrame,
    *,
    chain_id: int,
    ordered_features: tuple[str, ...],
) -> FeatureState:
    raw = _raw_feature_rows(
        training_support,
        chain_id=chain_id,
        ordered_features=ordered_features,
    )
    if raw.shape[0] == 0:
        raise ValueError("training_support must be non-empty")
    if not np.isfinite(raw).all():
        raise ValueError("training_support must produce finite raw features")

    means = raw.mean(axis=0, dtype=np.float64)
    standard_deviations = raw.std(axis=0, ddof=0, dtype=np.float64)
    if not np.isfinite(means).all() or not np.isfinite(standard_deviations).all():
        raise ValueError("fitted feature statistics must be finite")
    if np.any(standard_deviations == 0.0):
        raise ValueError("training_support contains a constant feature")

    return FeatureState(
        means=tuple(float(value) for value in means),
        standard_deviations=tuple(float(value) for value in standard_deviations),
    )


def transform_feature_rows(
    blocks: pl.DataFrame,
    *,
    chain_id: int,
    ordered_features: tuple[str, ...],
    state: FeatureState,
) -> NDArray[np.float32]:
    if len(state.means) != len(ordered_features):
        raise ValueError("state width must equal ordered_features width")

    raw = _raw_feature_rows(
        blocks,
        chain_id=chain_id,
        ordered_features=ordered_features,
    )
    means = np.asarray(state.means, dtype=np.float64)
    standard_deviations = np.asarray(state.standard_deviations, dtype=np.float64)
    with np.errstate(over="ignore", invalid="ignore"):
        transformed = np.ascontiguousarray(
            (raw - means) / standard_deviations,
            dtype=np.float32,
        )
    if not np.isfinite(transformed).all():
        raise ValueError("transformed features must be finite float32 values")
    if not transformed.flags.c_contiguous:
        raise ValueError("transformed features must be C-contiguous")
    return transformed


def _raw_feature_rows(
    blocks: pl.DataFrame,
    *,
    chain_id: int,
    ordered_features: tuple[str, ...],
) -> NDArray[np.float64]:
    prefix = _feature_prefix(chain_id)
    _validate_feature_order(prefix, ordered_features)

    base_fees = _float_column(blocks, "base_fee_per_gas")
    gas_used = _float_column(blocks, "gas_used")
    gas_limits = _float_column(blocks, "gas_limit")
    with np.errstate(divide="ignore", invalid="ignore"):
        columns = [np.log(base_fees), gas_used / gas_limits]

    if chain_id == 1:
        columns.append(_ethereum_forming_fee_logs(blocks))
    if _ACTIVITY_PAIR[0] in ordered_features:
        tx_counts = _float_column(blocks, "tx_count")
        with np.errstate(divide="ignore", invalid="ignore"):
            columns.extend((np.log(gas_limits), np.log1p(tx_counts)))
    if _HOUR_PAIR[0] in ordered_features:
        timestamps = blocks["timestamp"].to_numpy().astype(np.int64, copy=False)
        hours = (timestamps // 3_600) % 24
        angles = 2.0 * math.pi * hours.astype(np.float64, copy=False) / 24.0
        columns.extend((np.sin(angles), np.cos(angles)))

    return np.ascontiguousarray(np.column_stack(columns), dtype=np.float64)


def _feature_prefix(chain_id: int) -> tuple[str, ...]:
    if chain_id == 1:
        return _ETHEREUM_PREFIX
    if chain_id in (137, 43_114):
        return _COMMON_PREFIX
    raise ValueError(f"Unsupported chain: {chain_id}")


def _validate_feature_order(
    prefix: tuple[str, ...],
    ordered_features: tuple[str, ...],
) -> None:
    allowed = (
        prefix,
        (*prefix, *_ACTIVITY_PAIR),
        (*prefix, *_HOUR_PAIR),
        (*prefix, *_ACTIVITY_PAIR, *_HOUR_PAIR),
    )
    if ordered_features not in allowed:
        raise ValueError("ordered_features is not an approved feature tuple")


def _ethereum_forming_fee_logs(blocks: pl.DataFrame) -> NDArray[np.float64]:
    base_fees = blocks["base_fee_per_gas"].to_list()
    gas_used_values = blocks["gas_used"].to_list()
    gas_limits = blocks["gas_limit"].to_list()
    return np.fromiter(
        (
            math.log(_ethereum_child_base_fee(base_fee, gas_used, gas_limit))
            for base_fee, gas_used, gas_limit in zip(
                base_fees,
                gas_used_values,
                gas_limits,
                strict=True,
            )
        ),
        dtype=np.float64,
        count=blocks.height,
    )


def _ethereum_child_base_fee(
    base_fee_per_gas: int,
    gas_used: int,
    gas_limit: int,
) -> int:
    gas_target = gas_limit // 2
    if gas_target <= 0:
        raise ValueError("gas_target must be positive")
    if gas_used == gas_target:
        return base_fee_per_gas
    if gas_used > gas_target:
        return base_fee_per_gas + max(
            base_fee_per_gas * (gas_used - gas_target) // gas_target // 8,
            1,
        )
    return base_fee_per_gas - (
        base_fee_per_gas * (gas_target - gas_used) // gas_target // 8
    )


def _float_column(blocks: pl.DataFrame, name: str) -> NDArray[np.float64]:
    return blocks[name].to_numpy().astype(np.float64, copy=False)


__all__ = ["FeatureState", "fit_feature_state", "transform_feature_rows"]
