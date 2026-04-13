from __future__ import annotations

import numpy as np
import polars as pl

from spice.features import FeatureSelection, build_feature_table
from spice.temporal.store import build_temporal_store
from spice.temporal.window import DelayWindow


def test_temporal_store_uses_real_timestamps_for_context_and_candidates() -> None:
    selection = FeatureSelection(
        feature_set_id="test_timestamp_native",
        feature_names=("seconds_since_previous_block", "elapsed_seconds"),
    )
    blocks = pl.DataFrame(
        {
            "block_number": np.arange(100, 107, dtype=np.int64),
            "timestamp": np.array([0, 5, 11, 18, 27, 29, 40], dtype=np.int64),
            "base_fee_per_gas": np.full(7, 1_000_000_000, dtype=np.int64),
            "gas_used": np.full(7, 18_000_000, dtype=np.int64),
            "gas_limit": np.full(7, 30_000_000, dtype=np.int64),
            "chain_id": np.ones(7, dtype=np.int64),
        }
    )
    feature_table = build_feature_table(blocks, selection=selection)
    store = build_temporal_store(
        feature_table,
        window=DelayWindow(
            lookback_seconds=10,
            delay_seconds=12,
            feature_history_seconds=feature_table.feature_history_seconds,
        ),
    )

    np.testing.assert_array_equal(store.anchor_rows, np.array([2, 3, 4, 5], dtype=np.int64))
    np.testing.assert_array_equal(store.context_start_rows, np.array([1, 2, 3, 4], dtype=np.int64))
    np.testing.assert_array_equal(
        store.candidate_end_rows - store.candidate_start_rows,
        np.array([1, 2, 1, 1], dtype=np.int64),
    )
    assert store.max_candidate_slots == 2
