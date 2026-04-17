"""Paper-aligned time-native feature nodes."""

from __future__ import annotations

import math

import numpy as np
import polars as pl
from hamilton.function_modifiers import tag
from numpy.typing import NDArray

FloatVector = NDArray[np.float64]
IntVector = NDArray[np.int64]


def _paper_gas_ratio(sorted_blocks: pl.DataFrame) -> FloatVector:
    return (
        sorted_blocks["gas_used"].cast(pl.Float64) / sorted_blocks["gas_limit"].cast(pl.Float64)
    ).to_numpy().astype(np.float64, copy=False)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="0")
def log_base_fee_per_gas(sorted_blocks: pl.DataFrame) -> FloatVector:
    return np.log1p(
        sorted_blocks["base_fee_per_gas"].cast(pl.Float64).to_numpy().astype(np.float64, copy=False)
    )


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="0")
def log_gas_used(sorted_blocks: pl.DataFrame) -> FloatVector:
    return np.log1p(
        sorted_blocks["gas_used"].cast(pl.Float64).to_numpy().astype(np.float64, copy=False)
    )


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="0")
def log_gas_limit(sorted_blocks: pl.DataFrame) -> FloatVector:
    return np.log1p(
        sorted_blocks["gas_limit"].cast(pl.Float64).to_numpy().astype(np.float64, copy=False)
    )


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="0")
def gas_ratio(sorted_blocks: pl.DataFrame) -> FloatVector:
    return _paper_gas_ratio(sorted_blocks)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="0")
def dow_sin(timestamps: IntVector) -> FloatVector:
    weekdays = ((timestamps // 86_400) + 4) % 7
    return np.sin(2.0 * math.pi * weekdays.astype(np.float64, copy=False) / 7.0)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="0")
def dow_cos(timestamps: IntVector) -> FloatVector:
    weekdays = ((timestamps // 86_400) + 4) % 7
    return np.cos(2.0 * math.pi * weekdays.astype(np.float64, copy=False) / 7.0)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="0")
def time_since_start(timestamps: IntVector) -> FloatVector:
    if timestamps.size == 0:
        return np.empty(0, dtype=np.float64)
    return timestamps.astype(np.float64, copy=False) - float(timestamps[0])


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="0")
def dt_seconds(timestamps: IntVector) -> FloatVector:
    if timestamps.size == 0:
        return np.empty(0, dtype=np.float64)
    deltas = np.diff(timestamps.astype(np.float64, copy=False), prepend=timestamps[:1])
    if deltas.size > 1:
        deltas[0] = float(np.median(deltas[1:]))
    return deltas.astype(np.float64, copy=False)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="1")
def dlog_base_fee(log_base_fee_per_gas: FloatVector) -> FloatVector:
    if log_base_fee_per_gas.size == 0:
        return np.empty(0, dtype=np.float64)
    result = np.empty(log_base_fee_per_gas.shape[0], dtype=np.float64)
    result[0] = np.nan
    result[1:] = np.diff(log_base_fee_per_gas)
    return result


def _rolling_mean(values: FloatVector, *, window: int) -> FloatVector:
    result = np.full(values.shape[0], np.nan, dtype=np.float64)
    if window <= 0:
        raise ValueError("window must be positive")
    if values.size < window:
        return result
    cumsum = np.cumsum(values, dtype=np.float64)
    result[window - 1] = cumsum[window - 1] / window
    for index in range(window, values.shape[0]):
        result[index] = (cumsum[index] - cumsum[index - window]) / window
    return result


def _rolling_std(values: FloatVector, *, window: int) -> FloatVector:
    result = np.full(values.shape[0], np.nan, dtype=np.float64)
    if window <= 0:
        raise ValueError("window must be positive")
    if values.size < window:
        return result
    for index in range(window - 1, values.shape[0]):
        window_values = values[index - window + 1 : index + 1]
        result[index] = float(np.std(window_values, ddof=1))
    return result


def _rolling_min(values: FloatVector, *, window: int) -> FloatVector:
    result = np.full(values.shape[0], np.nan, dtype=np.float64)
    if window <= 0:
        raise ValueError("window must be positive")
    if values.size < window:
        return result
    for index in range(window - 1, values.shape[0]):
        result[index] = float(values[index - window + 1 : index + 1].min())
    return result


def _shift(values: FloatVector, *, lag: int) -> FloatVector:
    result = np.full(values.shape[0], np.nan, dtype=np.float64)
    if lag <= 0:
        raise ValueError("lag must be positive")
    if values.size <= lag:
        return result
    result[lag:] = values[:-lag]
    return result


@tag(spice_kind="feature", spice_history_seconds="600", spice_warmup_rows="0")
def base_fee_trend(
    log_base_fee_per_gas: FloatVector,
    timestamps: IntVector,
) -> FloatVector:
    result = np.full(log_base_fee_per_gas.shape[0], np.nan, dtype=np.float64)
    if timestamps.size == 0:
        return result
    starts = np.searchsorted(timestamps, timestamps - 600, side="left")
    valid = (timestamps - timestamps[0]) >= 600
    for index, start in enumerate(starts):
        if not valid[index]:
            continue
        window_values = log_base_fee_per_gas[start : index + 1]
        window_times = timestamps[start : index + 1].astype(np.float64, copy=False)
        centered_x = window_times - window_times.mean()
        denominator = np.square(centered_x).sum()
        if denominator <= 0.0:
            result[index] = 0.0
            continue
        centered_y = window_values - window_values.mean()
        result[index] = float((centered_x * centered_y).sum() / denominator)
    return result


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="9")
def roll10_mean_logfee(log_base_fee_per_gas: FloatVector) -> FloatVector:
    return _rolling_mean(log_base_fee_per_gas, window=10)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="9")
def roll10_std_logfee(log_base_fee_per_gas: FloatVector) -> FloatVector:
    return _rolling_std(log_base_fee_per_gas, window=10)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="9")
def roll10_min_logfee(log_base_fee_per_gas: FloatVector) -> FloatVector:
    return _rolling_min(log_base_fee_per_gas, window=10)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="9")
def roll10_mean_gr(gas_ratio: FloatVector) -> FloatVector:
    return _rolling_mean(gas_ratio, window=10)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="9")
def roll10_std_gr(gas_ratio: FloatVector) -> FloatVector:
    return _rolling_std(gas_ratio, window=10)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="49")
def roll50_mean_logfee(log_base_fee_per_gas: FloatVector) -> FloatVector:
    return _rolling_mean(log_base_fee_per_gas, window=50)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="49")
def roll50_std_logfee(log_base_fee_per_gas: FloatVector) -> FloatVector:
    return _rolling_std(log_base_fee_per_gas, window=50)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="49")
def roll50_min_logfee(log_base_fee_per_gas: FloatVector) -> FloatVector:
    return _rolling_min(log_base_fee_per_gas, window=50)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="49")
def roll50_mean_gr(gas_ratio: FloatVector) -> FloatVector:
    return _rolling_mean(gas_ratio, window=50)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="49")
def roll50_std_gr(gas_ratio: FloatVector) -> FloatVector:
    return _rolling_std(gas_ratio, window=50)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="199")
def roll200_mean_logfee(log_base_fee_per_gas: FloatVector) -> FloatVector:
    return _rolling_mean(log_base_fee_per_gas, window=200)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="199")
def roll200_std_logfee(log_base_fee_per_gas: FloatVector) -> FloatVector:
    return _rolling_std(log_base_fee_per_gas, window=200)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="199")
def roll200_min_logfee(log_base_fee_per_gas: FloatVector) -> FloatVector:
    return _rolling_min(log_base_fee_per_gas, window=200)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="199")
def roll200_mean_gr(gas_ratio: FloatVector) -> FloatVector:
    return _rolling_mean(gas_ratio, window=200)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="199")
def roll200_std_gr(gas_ratio: FloatVector) -> FloatVector:
    return _rolling_std(gas_ratio, window=200)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="1")
def gas_ratio_lag1(gas_ratio: FloatVector) -> FloatVector:
    return _shift(gas_ratio, lag=1)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="2")
def gas_ratio_lag2(gas_ratio: FloatVector) -> FloatVector:
    return _shift(gas_ratio, lag=2)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="3")
def gas_ratio_lag3(gas_ratio: FloatVector) -> FloatVector:
    return _shift(gas_ratio, lag=3)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="4")
def gas_ratio_lag4(gas_ratio: FloatVector) -> FloatVector:
    return _shift(gas_ratio, lag=4)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="5")
def gas_ratio_lag5(gas_ratio: FloatVector) -> FloatVector:
    return _shift(gas_ratio, lag=5)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="6")
def gas_ratio_lag6(gas_ratio: FloatVector) -> FloatVector:
    return _shift(gas_ratio, lag=6)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="1")
def dlogfee_lag1(dlog_base_fee: FloatVector) -> FloatVector:
    return _shift(dlog_base_fee, lag=1)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="2")
def dlogfee_lag2(dlog_base_fee: FloatVector) -> FloatVector:
    return _shift(dlog_base_fee, lag=2)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="3")
def dlogfee_lag3(dlog_base_fee: FloatVector) -> FloatVector:
    return _shift(dlog_base_fee, lag=3)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="4")
def dlogfee_lag4(dlog_base_fee: FloatVector) -> FloatVector:
    return _shift(dlog_base_fee, lag=4)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="5")
def dlogfee_lag5(dlog_base_fee: FloatVector) -> FloatVector:
    return _shift(dlog_base_fee, lag=5)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="6")
def dlogfee_lag6(dlog_base_fee: FloatVector) -> FloatVector:
    return _shift(dlog_base_fee, lag=6)
