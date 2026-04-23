from __future__ import annotations

from typing import cast

import pytest

from spice.config import TrainConfig, WorkflowTask
from spice.core.errors import StateConflictError
from spice.corpus.coverage import training_coverage_requirement, validate_corpus_coverage
from spice.corpus.metadata import (
    BlockRangeMetadata,
    ChainMetadata,
    CompactValidationReport,
    DatasetCoverageMetadata,
    DatasetIdentity,
    DatasetManifest,
    DatasetRequestMetadata,
    DatasetValidationMetadata,
    DatasetWindowMetadata,
    TimestampRangeMetadata,
)
from spice.features import compile_feature_contract
from spice.temporal.contracts import compile_problem_contract


def _manifest(*, history_seconds: int, history_rows: int) -> DatasetManifest:
    history = DatasetWindowMetadata(start_timestamp=1000, end_timestamp=1000 + history_seconds)
    evaluation = DatasetWindowMetadata(start_timestamp=2000, end_timestamp=2100)
    clean_report = CompactValidationReport(
        status="clean",
        rows=history_rows,
        block_range=BlockRangeMetadata(first=1, last=history_rows),
        timestamp_range=TimestampRangeMetadata(
            first=history.start_timestamp,
            last=history.end_timestamp,
        ),
    )
    evaluation_report = CompactValidationReport(
        status="clean",
        rows=64,
        block_range=BlockRangeMetadata(first=10_000, last=10_063),
        timestamp_range=TimestampRangeMetadata(
            first=evaluation.start_timestamp,
            last=evaluation.end_timestamp,
        ),
    )
    return DatasetManifest(
        dataset=DatasetIdentity(id="cor_test", name="test"),
        chain=ChainMetadata(name="ethereum", chain_id=1),
        request=DatasetRequestMetadata(history=history, evaluation=evaluation),
        coverage=DatasetCoverageMetadata(history=history, evaluation=evaluation),
        validation=DatasetValidationMetadata(
            history=clean_report,
            evaluation=evaluation_report,
        ),
    )


def test_training_corpus_coverage_accepts_compiled_requirement(
    tmp_path,
    load_workflow_config,
    model_workflow_override,
) -> None:
    config = cast(
        TrainConfig,
        load_workflow_config(
            WorkflowTask.TRAIN,
            workspace=tmp_path,
            override=model_workflow_override(sample_count=4, lookback_seconds=24),
        ),
    )
    feature_contract = compile_feature_contract(feature_set=config.feature_set)
    contract = compile_problem_contract(
        problem=config.problem,
        feature_contract=feature_contract,
        chain_runtime=config.chain.runtime,
    )
    requirement = training_coverage_requirement(contract)

    validate_corpus_coverage(
        _manifest(
            history_seconds=requirement.history_seconds,
            history_rows=requirement.history_rows,
        ),
        contract=contract,
        feature_contract=feature_contract,
        requirement=requirement,
    )


def test_training_corpus_coverage_rejects_short_history(
    tmp_path,
    load_workflow_config,
    model_workflow_override,
) -> None:
    config = cast(
        TrainConfig,
        load_workflow_config(
            WorkflowTask.TRAIN,
            workspace=tmp_path,
            override=model_workflow_override(sample_count=4, lookback_seconds=24),
        ),
    )
    feature_contract = compile_feature_contract(feature_set=config.feature_set)
    contract = compile_problem_contract(
        problem=config.problem,
        feature_contract=feature_contract,
        chain_runtime=config.chain.runtime,
    )
    requirement = training_coverage_requirement(contract)

    with pytest.raises(StateConflictError, match="history coverage is insufficient"):
        validate_corpus_coverage(
            _manifest(
                history_seconds=requirement.history_seconds - 1,
                history_rows=requirement.history_rows,
            ),
            contract=contract,
            feature_contract=feature_contract,
            requirement=requirement,
        )
