"""Block-window Hamilton feature nodes."""

from __future__ import annotations

import numpy as np
import polars as pl
from hamilton.function_modifiers import tag
from numpy.typing import NDArray

FloatVector = NDArray[np.float64]


def _rolling_stat(values: FloatVector, *, window: int, stat: str) -> FloatVector:
    if values.size == 0:
        return np.empty(0, dtype=np.float64)
    series = pl.Series(values)
    if stat == "mean":
        result = series.rolling_mean(window_size=window, min_samples=window)
    elif stat == "std":
        result = series.rolling_std(window_size=window, min_samples=window, ddof=0)
    else:  # pragma: no cover
        raise ValueError(f"Unsupported rolling stat: {stat}")
    return result.to_numpy().astype(np.float64, copy=False)


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="9")
def rolling_mean_log_base_fee_10(log_base_fee: FloatVector) -> FloatVector:
    return _rolling_stat(log_base_fee, window=10, stat="mean")


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="9")
def rolling_std_log_base_fee_10(log_base_fee: FloatVector) -> FloatVector:
    return _rolling_stat(log_base_fee, window=10, stat="std")


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="9")
def rolling_mean_gas_utilization_10(gas_utilization: FloatVector) -> FloatVector:
    return _rolling_stat(gas_utilization, window=10, stat="mean")


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="9")
def rolling_std_gas_utilization_10(gas_utilization: FloatVector) -> FloatVector:
    return _rolling_stat(gas_utilization, window=10, stat="std")


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="49")
def rolling_mean_log_base_fee_50(log_base_fee: FloatVector) -> FloatVector:
    return _rolling_stat(log_base_fee, window=50, stat="mean")


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="49")
def rolling_std_log_base_fee_50(log_base_fee: FloatVector) -> FloatVector:
    return _rolling_stat(log_base_fee, window=50, stat="std")


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="49")
def rolling_mean_gas_utilization_50(gas_utilization: FloatVector) -> FloatVector:
    return _rolling_stat(gas_utilization, window=50, stat="mean")


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="49")
def rolling_std_gas_utilization_50(gas_utilization: FloatVector) -> FloatVector:
    return _rolling_stat(gas_utilization, window=50, stat="std")


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="199")
def rolling_mean_log_base_fee_200(log_base_fee: FloatVector) -> FloatVector:
    return _rolling_stat(log_base_fee, window=200, stat="mean")


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="199")
def rolling_std_log_base_fee_200(log_base_fee: FloatVector) -> FloatVector:
    return _rolling_stat(log_base_fee, window=200, stat="std")


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="199")
def rolling_mean_gas_utilization_200(gas_utilization: FloatVector) -> FloatVector:
    return _rolling_stat(gas_utilization, window=200, stat="mean")


@tag(spice_kind="feature", spice_history_seconds="0", spice_warmup_rows="199")
def rolling_std_gas_utilization_200(gas_utilization: FloatVector) -> FloatVector:
    return _rolling_stat(gas_utilization, window=200, stat="std")
