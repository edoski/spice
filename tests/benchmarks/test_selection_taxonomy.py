from __future__ import annotations

from spice.benchmarks.selection_taxonomy import (
    benchmark_dimension_fields,
    benchmark_selection_coordinate_fields,
    benchmark_selection_root_fields,
    benchmark_workflows,
)
from spice.config import WorkflowTask


def test_benchmark_selection_taxonomy_separates_roots_from_coordinates() -> None:
    assert benchmark_workflows() == {
        WorkflowTask.TRAIN,
        WorkflowTask.TUNE,
        WorkflowTask.EVALUATE,
    }
    coordinates = benchmark_selection_coordinate_fields()
    roots = benchmark_selection_root_fields()

    assert {"problem", "variant", "delay_seconds"} <= coordinates
    assert roots == {"dataset_id", "study_id", "artifact_id"}
    assert not roots & coordinates
    runtime_fields = benchmark_dimension_fields("runtime")
    assert runtime_fields is not None
    assert runtime_fields >= {"trial_count", "batch_size"}
