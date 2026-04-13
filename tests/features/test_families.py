from __future__ import annotations

import numpy as np
import polars as pl

from spice.features import (
    FeaturePrerequisites,
    FeatureSelection,
    build_feature_table,
    resolve_feature_prerequisites,
)


def test_block_native_family_resolves_prerequisites_and_features() -> None:
    selection = FeatureSelection(
        feature_set_id="test_block_native",
        feature_family_id="block_native",
        feature_names=(
            "elapsed_blocks",
            "rolling_mean_log_base_fee_10",
            "trend_slope_200",
        ),
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

    prerequisites = resolve_feature_prerequisites(
        selection.feature_family_id,
        selection.feature_names,
    )
    feature_table = build_feature_table(blocks, selection=selection)

    assert prerequisites == FeaturePrerequisites(history_seconds=0, warmup_rows=199)
    assert feature_table.feature_family_id == "block_native"
    assert feature_table.feature_prerequisites == prerequisites
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
