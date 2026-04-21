from __future__ import annotations

from typing import cast

from spice.config import TuneConfig, WorkflowTask
from spice.modeling.dataset_builders import ProfessorTemporalDatasetBuilderConfig
from spice.modeling.tuned_config import coerce_tuned_parameter_set
from spice.modeling.tuning import apply_tuned_parameters


def test_apply_tuned_parameters_preserves_professor_dataset_builder(
    tmp_path,
    load_workflow_config,
) -> None:
    config = cast(
        TuneConfig,
        load_workflow_config(
            WorkflowTask.TUNE,
            workspace=tmp_path,
            preset="icdcs_2026_professor",
        ),
    )

    assert isinstance(config.dataset_builder, ProfessorTemporalDatasetBuilderConfig)

    tuned = apply_tuned_parameters(
        config,
        coerce_tuned_parameter_set(
            {
                "training": {"learning_rate": 0.001, "weight_decay": 0.001},
                "model": {"id": "lstm", "hidden_size": 256, "dropout": 0.1},
            },
            model_id=config.model.id,
        ),
    )

    assert isinstance(tuned, TuneConfig)
    assert isinstance(tuned.dataset_builder, ProfessorTemporalDatasetBuilderConfig)
    assert tuned.dataset_builder.min_sequence_length == 64
    assert tuned.dataset_builder.max_sequence_length == 4096
