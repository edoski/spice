from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from spice.features import FeatureSelection, build_feature_table, feature_warmup_blocks
from tests.support import base_overrides, compose_experiment, make_history_rows


def test_feature_table_preserves_requested_output_order() -> None:
    blocks = pl.DataFrame(make_history_rows(256))
    selection = FeatureSelection(
        feature_set_id="ordered",
        feature_names=("hour_cos", "hour_sin", "log_base_fee"),
    )

    table = build_feature_table(blocks, selection=selection)
    expected_hour_cos = np.cos(
        2.0 * np.pi * ((table.timestamps // 3600) % 24) / 24.0
    ).astype(np.float32)

    assert table.feature_names == selection.feature_names
    assert table.feature_matrix.shape[1] == 3
    assert np.array_equal(table.feature_matrix[:, 0], expected_hour_cos)


def test_feature_warmup_comes_from_selected_nodes() -> None:
    assert feature_warmup_blocks(("log_base_fee", "rolling_mean_log_base_fee_200")) == 199
    assert feature_warmup_blocks(("trend_slope_200",)) == 199
    assert feature_warmup_blocks(("hour_sin", "weekday_cos")) == 0


def test_config_rejects_unknown_feature_outputs(tmp_path) -> None:
    with pytest.raises(ValueError, match="Unknown feature outputs"):
        compose_experiment(
            "train",
            overrides=base_overrides(tmp_path)
            + ["feature_set.outputs=[log_base_fee,missing_feature]"],
        )


def test_config_rejects_duplicate_feature_outputs(tmp_path) -> None:
    with pytest.raises(ValueError, match="feature_set.outputs must not contain duplicates"):
        compose_experiment(
            "train",
            overrides=base_overrides(tmp_path)
            + ["feature_set.outputs=[log_base_fee,log_base_fee]"],
        )
