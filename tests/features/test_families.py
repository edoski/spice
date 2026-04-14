from __future__ import annotations

import numpy as np
import polars as pl

from spice.config import coerce_feature_set_config
from spice.features import (
    FeaturePrerequisites,
    compile_feature_contract,
)


def test_block_native_feature_contract_builds_table_with_family_owned_compile() -> None:
    feature_contract = compile_feature_contract(
        feature_set=coerce_feature_set_config(
            {
                "id": "test_block_native",
                "family": {"id": "block_native"},
                "outputs": [
                    "elapsed_blocks",
                    "rolling_mean_log_base_fee_10",
                    "trend_slope_200",
                ],
            }
        )
    )
    blocks = pl.DataFrame(
        {
            "block_number": np.arange(10_000, 10_210, dtype=np.int64),
            "timestamp": np.arange(210, dtype=np.int64) * 12,
            "base_fee_per_gas": np.arange(1_000, 1_210, dtype=np.int64),
            "gas_used": np.full(210, 18_000_000, dtype=np.int64),
            "gas_limit": np.full(210, 30_000_000, dtype=np.int64),
            "chain_id": np.ones(210, dtype=np.int64),
        }
    )

    feature_table = feature_contract.build_table(blocks)

    assert feature_contract.feature_prerequisites == FeaturePrerequisites(
        history_seconds=0,
        warmup_rows=199,
    )
    assert feature_table.feature_family_id == "block_native"
    assert feature_table.feature_prerequisites == feature_contract.feature_prerequisites
    np.testing.assert_array_equal(
        feature_table.feature_matrix[:5, 0],
        np.array([0.0, 1.0, 2.0, 3.0, 4.0], dtype=np.float32),
    )
    assert np.isnan(feature_table.feature_matrix[8, 1])
    np.testing.assert_allclose(
        feature_table.feature_matrix[9, 1],
        np.log(np.arange(1_000, 1_010, dtype=np.float64)).mean(),
    )
    assert np.isnan(feature_table.feature_matrix[198, 2])
    assert feature_table.feature_matrix[199, 2] > 0.0
