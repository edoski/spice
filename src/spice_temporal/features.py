"""Feature engineering for temporal SPICE baselines."""

from __future__ import annotations

import math

from spice_temporal.records import BlockRecord, FeatureRow

ROLLING_WINDOWS = (10, 50, 200)


def cyclical_encode(value: int, period: int) -> tuple[float, float]:
    angle = 2.0 * math.pi * (value % period) / period
    return math.sin(angle), math.cos(angle)


def safe_log(value: float) -> float:
    return math.log(max(value, 1.0))


def rolling_mean(values: list[float]) -> float:
    return sum(values) / len(values)


def rolling_std(values: list[float]) -> float:
    if len(values) == 1:
        return 0.0
    mean = rolling_mean(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def ols_slope(values: list[float]) -> float:
    n_values = len(values)
    if n_values < 2:
        return 0.0
    x_mean = (n_values - 1) / 2
    y_mean = rolling_mean(values)
    numerator = 0.0
    denominator = 0.0
    for index, value in enumerate(values):
        dx = index - x_mean
        numerator += dx * (value - y_mean)
        denominator += dx * dx
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def feature_names() -> list[str]:
    names = [
        "log_base_fee",
        "gas_utilization",
        "hour_sin",
        "hour_cos",
        "weekday_sin",
        "weekday_cos",
        "elapsed_blocks",
        "trend_slope_200",
    ]
    for window in ROLLING_WINDOWS:
        names.extend(
            [
                f"rolling_mean_log_base_fee_{window}",
                f"rolling_std_log_base_fee_{window}",
                f"rolling_mean_gas_utilization_{window}",
                f"rolling_std_gas_utilization_{window}",
            ]
        )
    return names


def build_feature_rows(blocks: list[BlockRecord]) -> list[FeatureRow]:
    if not blocks:
        return []

    blocks = sorted(blocks, key=lambda item: item.block_number)
    log_base_fees = [safe_log(block.base_fee_per_gas) for block in blocks]
    gas_utilizations = [block.gas_utilization for block in blocks]
    min_index = max(ROLLING_WINDOWS) - 1
    rows: list[FeatureRow] = []

    for index in range(min_index, len(blocks)):
        block = blocks[index]
        hour = (block.timestamp // 3600) % 24
        weekday = (block.timestamp // 86_400 + 4) % 7
        hour_sin, hour_cos = cyclical_encode(hour, 24)
        weekday_sin, weekday_cos = cyclical_encode(weekday, 7)

        feature_vector = [
            log_base_fees[index],
            gas_utilizations[index],
            hour_sin,
            hour_cos,
            weekday_sin,
            weekday_cos,
            float(index),
            ols_slope(log_base_fees[index - 199 : index + 1]),
        ]

        for window in ROLLING_WINDOWS:
            fee_window = log_base_fees[index - window + 1 : index + 1]
            gas_window = gas_utilizations[index - window + 1 : index + 1]
            feature_vector.extend(
                [
                    rolling_mean(fee_window),
                    rolling_std(fee_window),
                    rolling_mean(gas_window),
                    rolling_std(gas_window),
                ]
            )

        rows.append(
            FeatureRow(
                block_number=block.block_number,
                timestamp=block.timestamp,
                features=feature_vector,
                log_base_fee=log_base_fees[index],
            )
        )
    return rows
