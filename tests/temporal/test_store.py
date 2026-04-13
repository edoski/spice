from __future__ import annotations

import numpy as np
import polars as pl

from spice.config import coerce_problem_spec
from spice.features import FeatureSelection, build_feature_table
from spice.temporal.contracts import resolve_feature_contract


def test_temporal_store_uses_real_timestamps_for_context_and_candidates() -> None:
    selection = FeatureSelection(
        feature_set_id="test_timestamp_native",
        feature_family_id="time_native",
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
    contract = resolve_feature_contract(
        problem=coerce_problem_spec(
            {
                "id": "test_timestamp_native",
                "lookback_seconds": 10,
                "sample_count": 4,
                "max_supported_delay_seconds": 12,
                "compiler": {"id": "timestamp_native"},
            }
        ),
        selection=selection,
    )
    store, _ = contract.build_capability_store(feature_table)

    np.testing.assert_array_equal(store.anchor_rows, np.array([0, 1, 2, 3, 4, 5], dtype=np.int64))
    np.testing.assert_array_equal(
        store.context_start_rows,
        np.array([0, 0, 1, 2, 3, 4], dtype=np.int64),
    )
    np.testing.assert_array_equal(
        store.candidate_end_rows - store.candidate_start_rows,
        np.array([2, 1, 1, 2, 1, 1], dtype=np.int64),
    )
    assert store.max_candidate_slots == 2


def test_estimated_block_store_uses_corpus_calibration_for_row_geometry() -> None:
    selection = FeatureSelection(
        feature_set_id="test_estimated_block",
        feature_family_id="time_native",
        feature_names=("seconds_since_previous_block", "elapsed_seconds"),
    )
    blocks = pl.DataFrame(
        {
            "block_number": np.arange(200, 208, dtype=np.int64),
            "timestamp": np.array([0, 7, 15, 26, 34, 45, 53, 65], dtype=np.int64),
            "base_fee_per_gas": np.full(8, 1_000_000_000, dtype=np.int64),
            "gas_used": np.full(8, 18_000_000, dtype=np.int64),
            "gas_limit": np.full(8, 30_000_000, dtype=np.int64),
            "chain_id": np.ones(8, dtype=np.int64),
        }
    )
    feature_table = build_feature_table(blocks, selection=selection)
    contract = resolve_feature_contract(
        problem=coerce_problem_spec(
            {
                "id": "test_estimated_block",
                "lookback_seconds": 20,
                "sample_count": 3,
                "max_supported_delay_seconds": 18,
                "compiler": {"id": "estimated_block"},
            }
        ),
        selection=selection,
    )

    store, runtime_metadata = contract.build_capability_store(feature_table)

    assert runtime_metadata["effective_block_interval_seconds"] == 8.0
    np.testing.assert_array_equal(store.anchor_rows, np.array([1, 2, 3, 4], dtype=np.int64))
    np.testing.assert_array_equal(store.context_start_rows, np.array([0, 1, 2, 3], dtype=np.int64))
    np.testing.assert_array_equal(store.candidate_end_rows, np.array([5, 6, 7, 8], dtype=np.int64))
    np.testing.assert_array_equal(store.candidate_counts, np.array([3, 3, 3, 3], dtype=np.int64))
    assert store.max_candidate_slots == 3
