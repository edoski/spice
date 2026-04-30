from __future__ import annotations

from typing import cast

import numpy as np
import polars as pl

from spice.config import TrainConfig, WorkflowTask
from spice.modeling.dataset_builders import FixedSequenceTemporalBuilderRuntimeMetadata
from spice.modeling.pipeline import build_training_spec, prepare_training_dataset
from spice.storage.workflow_paths import WorkflowIdentity, build_workflow_paths
from tests.dataset_helpers import (
    make_block_rows,
    required_dataset_blocks,
    synthetic_block_interval_seconds,
)


def _make_history_rows_with_margin(config: TrainConfig, *, extra_rows: int = 32):
    block_interval_seconds = synthetic_block_interval_seconds(config.chain.name)
    count = required_dataset_blocks(config) + extra_rows
    return make_block_rows(
        count,
        start_block=1,
        start_timestamp=config.evaluation_window_start_timestamp - count * block_interval_seconds,
        chain_id=config.chain.runtime.chain_id,
        block_interval_seconds=block_interval_seconds,
    )


def _make_rows_with_tail_cadence_shift(
    count: int,
    *,
    fast_start_offset: int,
    chain_id: int,
) -> list[dict[str, int]]:
    rows = make_block_rows(
        count,
        start_block=1,
        start_timestamp=0,
        chain_id=chain_id,
        block_interval_seconds=12,
    )
    timestamp = 0
    for offset, row in enumerate(rows):
        row["timestamp"] = timestamp
        timestamp += 1 if offset >= fast_start_offset else 12
    return rows


def _paths(config: TrainConfig):
    assert config.dataset_id is not None
    return build_workflow_paths(
        output_root=config.storage.root,
        chain_name=config.chain.name,
        identity=WorkflowIdentity(corpus_id=config.dataset_id, artifact_id="art_test"),
    )


def test_fixed_context_dataset_builder_prepares_seq_len_without_builder_owned_class_state(
    tmp_path,
    load_workflow_config,
) -> None:
    config = cast(
        TrainConfig,
        load_workflow_config(
            WorkflowTask.TRAIN,
            workspace=tmp_path,
            surface="current_row_fee_dynamics",
            override={
                "problem": {
                    "id": "test_fixed_context_problem",
                    "lookback_seconds": 600,
                    "sample_count": 4096,
                    "max_delay_seconds": 36,
                    "compiler": {
                        "id": "observed_time_window",
                        "slot_spacing": {"id": "nominal"},
                    },
                    "execution_policy": {
                        "id": "strict_deadline_miss",
                    },
                }
            },
        ),
    )
    prepared = prepare_training_dataset(
        pl.DataFrame(_make_history_rows_with_margin(config)),
        spec=build_training_spec(config, paths=_paths(config)),
    )

    assert config.dataset_builder.id == "fixed_sequence_temporal"
    assert isinstance(
        prepared.builder_runtime_metadata,
        FixedSequenceTemporalBuilderRuntimeMetadata,
    )
    assert prepared.builder_runtime_metadata.sequence_length >= 64
    assert prepared.builder_runtime_metadata.median_dt_seconds > 0.0
    assert prepared.max_candidate_slots == prepared.store.max_candidate_slots
    assert prepared.sample_count == config.problem.sample_count
    assert prepared.store.n_samples > prepared.sample_count
    assert prepared.split_indices.train.size > 0
    assert prepared.split_indices.validation.size > 0
    assert prepared.split_indices.test.size > 0


def test_fixed_context_dataset_builder_keeps_candidate_window_arrays_aligned_after_seq_trim(
    tmp_path,
    load_workflow_config,
) -> None:
    config = cast(
        TrainConfig,
        load_workflow_config(
            WorkflowTask.TRAIN,
            workspace=tmp_path,
            surface="current_row_fee_dynamics",
            override={
                "problem": {
                    "id": "test_fixed_context_problem",
                    "lookback_seconds": 600,
                    "sample_count": 4096,
                    "max_delay_seconds": 36,
                    "compiler": {
                        "id": "observed_time_window",
                        "slot_spacing": {"id": "nominal"},
                    },
                    "execution_policy": {
                        "id": "strict_deadline_miss",
                    },
                }
            },
        ),
    )

    prepared = prepare_training_dataset(
        pl.DataFrame(_make_history_rows_with_margin(config)),
        spec=build_training_spec(config, paths=_paths(config)),
    )

    assert prepared.store.anchor_rows.shape == prepared.store.candidate_start_rows.shape
    assert prepared.store.anchor_rows.shape == prepared.store.candidate_end_rows.shape
    np.testing.assert_array_equal(prepared.store.anchor_rows, prepared.store.candidate_start_rows)
    np.testing.assert_array_less(
        prepared.store.candidate_start_rows,
        prepared.store.candidate_end_rows,
    )


def test_fixed_sequence_length_calibration_uses_train_sample_rows_only(
    tmp_path,
    load_workflow_config,
) -> None:
    config = cast(
        TrainConfig,
        load_workflow_config(
            WorkflowTask.TRAIN,
            workspace=tmp_path,
            surface="current_row_fee_dynamics",
            override={
                "dataset_builder": {
                    "id": "fixed_sequence_temporal",
                    "min_sequence_length": 1,
                    "max_sequence_length": 200,
                },
                "problem": {
                    "id": "test_fixed_context_problem",
                    "lookback_seconds": 120,
                    "sample_count": 120,
                    "max_delay_seconds": 600,
                    "compiler": {
                        "id": "observed_time_window",
                        "slot_spacing": {"id": "nominal"},
                    },
                    "execution_policy": {
                        "id": "strict_deadline_miss",
                    },
                },
            },
        ),
    )
    rows = _make_rows_with_tail_cadence_shift(
        420,
        fast_start_offset=320,
        chain_id=config.chain.runtime.chain_id,
    )

    prepared = prepare_training_dataset(
        pl.DataFrame(rows),
        spec=build_training_spec(config, paths=_paths(config)),
    )

    assert prepared.builder_runtime_metadata.median_dt_seconds == 12.0
    assert prepared.builder_runtime_metadata.sequence_length == 10
