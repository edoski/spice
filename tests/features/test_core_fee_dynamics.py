from __future__ import annotations

from collections.abc import Callable

import numpy as np
import polars as pl
import pytest
from pydantic import ValidationError

from spice.temporal.features import (
    FeatureState,
    fit_feature_state,
    transform_feature_rows,
)

ETHEREUM_FEATURES = (
    "log_base_fee_per_gas",
    "gas_utilization",
    "log_exact_forming_base_fee_per_gas",
    "log_gas_limit",
    "log1p_tx_count",
    "hour_sin",
    "hour_cos",
)
POLYGON_FEATURES = (
    "log_base_fee_per_gas",
    "gas_utilization",
    "log_gas_limit",
    "log1p_tx_count",
)
AVALANCHE_FEATURES = (
    "log_base_fee_per_gas",
    "gas_utilization",
    "hour_sin",
    "hour_cos",
)


def _blocks(
    *,
    base_fees: list[float | int],
    gas_used: list[int],
    gas_limits: list[int],
    tx_counts: list[int],
    timestamps: list[int],
) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "base_fee_per_gas": base_fees,
            "gas_used": gas_used,
            "gas_limit": gas_limits,
            "tx_count": tx_counts,
            "timestamp": timestamps,
        }
    )


def test_exact_three_chain_feature_formulas_fit_and_held_out_transform() -> None:
    ethereum = _blocks(
        base_fees=[1_000, 2_000, 3_000, 8_000_000_000_000_000_000],
        gas_used=[500, 1_200, 1_200, 4],
        gas_limits=[1_000, 2_000, 3_000, 4],
        tx_counts=[0, 1, 2, 3],
        timestamps=[0, 6 * 3_600, 12 * 3_600, 18 * 3_600],
    )
    polygon = _blocks(
        base_fees=[10, 20, 80],
        gas_used=[1, 3, 8],
        gas_limits=[2, 6, 10],
        tx_counts=[0, 3, 8],
        timestamps=[0, 1, 2],
    )
    avalanche = _blocks(
        base_fees=[10, 30, 90, 270],
        gas_used=[1, 4, 9, 16],
        gas_limits=[2, 8, 10, 20],
        tx_counts=[0, 0, 0, 0],
        timestamps=[0, 6 * 3_600, 12 * 3_600, 18 * 3_600],
    )
    expected_raw = {
        1: np.column_stack(
            (
                np.log([1_000, 2_000, 3_000, 8_000_000_000_000_000_000]),
                [0.5, 0.6, 0.4, 1.0],
                np.log([1_000, 2_050, 2_925, 9_000_000_000_000_000_000]),
                np.log([1_000, 2_000, 3_000, 4]),
                np.log1p([0, 1, 2, 3]),
                np.sin([0.0, np.pi / 2, np.pi, 3 * np.pi / 2]),
                np.cos([0.0, np.pi / 2, np.pi, 3 * np.pi / 2]),
            )
        ),
        137: np.column_stack(
            (
                np.log([10, 20, 80]),
                [0.5, 0.5, 0.8],
                np.log([2, 6, 10]),
                np.log1p([0, 3, 8]),
            )
        ),
        43_114: np.column_stack(
            (
                np.log([10, 30, 90, 270]),
                [0.5, 0.5, 0.9, 0.8],
                np.sin([0.0, np.pi / 2, np.pi, 3 * np.pi / 2]),
                np.cos([0.0, np.pi / 2, np.pi, 3 * np.pi / 2]),
            )
        ),
    }

    cases = (
        (1, ETHEREUM_FEATURES, ethereum),
        (137, POLYGON_FEATURES, polygon),
        (43_114, AVALANCHE_FEATURES, avalanche),
    )
    states: dict[int, FeatureState] = {}
    for chain_id, ordered_features, support in cases:
        raw = expected_raw[chain_id].astype(np.float64)
        state = fit_feature_state(
            support,
            chain_id=chain_id,
            ordered_features=ordered_features,
        )
        states[chain_id] = state
        np.testing.assert_allclose(state.means, raw.mean(axis=0))
        np.testing.assert_allclose(state.standard_deviations, raw.std(axis=0, ddof=0))

        transformed = transform_feature_rows(
            support,
            chain_id=chain_id,
            ordered_features=ordered_features,
            state=state,
        )
        expected = ((raw - raw.mean(axis=0)) / raw.std(axis=0, ddof=0)).astype(np.float32)
        np.testing.assert_allclose(transformed, expected, rtol=1e-6, atol=1e-6)
        assert transformed.shape == (support.height, len(ordered_features))
        assert transformed.dtype == np.float32
        assert transformed.flags.c_contiguous
        assert np.isfinite(transformed).all()

    ethereum_state = states[1]
    held_out = _blocks(
        base_fees=[1],
        gas_used=[101],
        gas_limits=[200],
        tx_counts=[4],
        timestamps=[3_600],
    )
    held_out_raw = np.array(
        [
            [
                0.0,
                101 / 200,
                np.log(2),
                np.log(200),
                np.log(5),
                np.sin(np.pi / 12),
                np.cos(np.pi / 12),
            ]
        ],
        dtype=np.float64,
    )

    held_out_result = transform_feature_rows(
        held_out,
        chain_id=1,
        ordered_features=ETHEREUM_FEATURES,
        state=ethereum_state,
    )

    np.testing.assert_allclose(
        held_out_result,
        (
            (held_out_raw - np.asarray(ethereum_state.means))
            / np.asarray(ethereum_state.standard_deviations)
        ).astype(np.float32),
        rtol=1e-6,
        atol=1e-6,
    )


def _valid_blocks() -> pl.DataFrame:
    return _blocks(
        base_fees=[10, 20],
        gas_used=[1, 3],
        gas_limits=[2, 4],
        tx_counts=[0, 1],
        timestamps=[0, 3_600],
    )


def _fit(
    blocks: pl.DataFrame,
    *,
    chain_id: int = 137,
    ordered_features: tuple[str, ...] = ("log_base_fee_per_gas", "gas_utilization"),
) -> FeatureState:
    return fit_feature_state(
        blocks,
        chain_id=chain_id,
        ordered_features=ordered_features,
    )


@pytest.mark.parametrize(
    ("operation", "match"),
    [
        pytest.param(lambda: _fit(_valid_blocks(), chain_id=2), "Unsupported chain", id="chain"),
        pytest.param(
            lambda: _fit(
                _valid_blocks(),
                ordered_features=("log_base_fee_per_gas", "gas_utilization", "unknown"),
            ),
            "ordered_features",
            id="unknown-name",
        ),
        pytest.param(
            lambda: _fit(
                _valid_blocks(),
                ordered_features=("gas_utilization", "log_base_fee_per_gas"),
            ),
            "ordered_features",
            id="order",
        ),
        pytest.param(
            lambda: _fit(
                _valid_blocks(),
                chain_id=1,
                ordered_features=("log_base_fee_per_gas", "gas_utilization"),
            ),
            "ordered_features",
            id="missing-ethereum-forming-fee",
        ),
        pytest.param(
            lambda: _fit(
                _valid_blocks(),
                ordered_features=(
                    "log_base_fee_per_gas",
                    "gas_utilization",
                    "log_exact_forming_base_fee_per_gas",
                ),
            ),
            "ordered_features",
            id="forbidden-polygon-forming-fee",
        ),
        pytest.param(
            lambda: _fit(
                _valid_blocks(),
                ordered_features=(
                    "log_base_fee_per_gas",
                    "gas_utilization",
                    "log_gas_limit",
                ),
            ),
            "ordered_features",
            id="partial-activity-pair",
        ),
        pytest.param(
            lambda: _fit(
                _valid_blocks(),
                ordered_features=(
                    "log_base_fee_per_gas",
                    "gas_utilization",
                    "hour_sin",
                ),
            ),
            "ordered_features",
            id="partial-hour-pair",
        ),
        pytest.param(
            lambda: _fit(
                _blocks(
                    base_fees=[10, 20],
                    gas_used=[0, 1],
                    gas_limits=[1, 1],
                    tx_counts=[0, 1],
                    timestamps=[0, 1],
                ),
                chain_id=1,
                ordered_features=(
                    "log_base_fee_per_gas",
                    "gas_utilization",
                    "log_exact_forming_base_fee_per_gas",
                ),
            ),
            "gas_target must be positive",
            id="gas-target",
        ),
        pytest.param(lambda: _fit(_valid_blocks().clear()), "non-empty", id="empty-fit"),
        pytest.param(
            lambda: _fit(
                _blocks(
                    base_fees=[0.0, 1.0],
                    gas_used=[1, 3],
                    gas_limits=[2, 4],
                    tx_counts=[0, 1],
                    timestamps=[0, 1],
                )
            ),
            "finite raw",
            id="nonfinite-fit",
        ),
        pytest.param(
            lambda: _fit(
                _blocks(
                    base_fees=[10, 10],
                    gas_used=[1, 1],
                    gas_limits=[2, 2],
                    tx_counts=[0, 0],
                    timestamps=[0, 0],
                )
            ),
            "constant",
            id="constant-fit",
        ),
        pytest.param(
            lambda: FeatureState.model_validate(
                {"means": (), "standard_deviations": ()}, strict=True
            ),
            "at least 1 item",
            id="empty-state",
        ),
        pytest.param(
            lambda: FeatureState(means=(0.0,), standard_deviations=(1.0, 2.0)),
            "equal widths",
            id="state-widths",
        ),
        pytest.param(
            lambda: FeatureState(means=(float("nan"),), standard_deviations=(1.0,)),
            "finite number",
            id="nonfinite-state",
        ),
        pytest.param(
            lambda: FeatureState(means=(0.0,), standard_deviations=(0.0,)),
            "greater than 0",
            id="nonpositive-state",
        ),
        pytest.param(
            lambda: transform_feature_rows(
                _valid_blocks(),
                chain_id=137,
                ordered_features=("log_base_fee_per_gas", "gas_utilization"),
                state=FeatureState(means=(0.0,), standard_deviations=(1.0,)),
            ),
            "state width",
            id="transform-state-width",
        ),
        pytest.param(
            lambda: transform_feature_rows(
                _valid_blocks(),
                chain_id=137,
                ordered_features=("log_base_fee_per_gas", "gas_utilization"),
                state=FeatureState(
                    means=(0.0, 0.0),
                    standard_deviations=(1e-300, 1e-300),
                ),
            ),
            "finite float32",
            id="float32-overflow",
        ),
    ],
)
def test_feature_contract_rejections(
    operation: Callable[[], object],
    match: str,
) -> None:
    with pytest.raises((ValueError, ValidationError), match=match):
        operation()
