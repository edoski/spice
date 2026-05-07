from __future__ import annotations

import pytest
from pydantic import ValidationError

from spice.corpus.metadata import (
    AcquisitionConfigSnapshot,
    ChainMetadata,
    CompactValidationReport,
    CorpusAcquisitionSourceRequirements,
    SplitMaterializationMetadata,
)


def test_source_requirements_decode_json_arrays_as_frozensets() -> None:
    requirements = CorpusAcquisitionSourceRequirements.model_validate(
        {
            "required_columns": ["timestamp", "block_number"],
            "optional_enrichments": ["priority_fee_percentiles"],
            "temporal_unit": "block",
            "ordering_key": "block_number",
            "partition_key": "chain_id",
        },
        strict=True,
    )

    assert requirements.required_columns == frozenset({"block_number", "timestamp"})
    assert requirements.model_dump(mode="json")["required_columns"] == [
        "block_number",
        "timestamp",
    ]


def test_chain_metadata_rejects_loose_runtime_scalars() -> None:
    with pytest.raises(ValidationError):
        ChainMetadata.model_validate(
            {
                "name": "ethereum",
                "runtime": {
                    "chain_id": "1",
                    "uses_poa_extra_data": False,
                    "nominal_block_time_seconds": 12.0,
                },
            },
            strict=True,
        )


def test_acquisition_settings_decode_json_rungs_as_immutable_tuple() -> None:
    settings = AcquisitionConfigSnapshot.model_validate(
        {
            "chunk_size": 5000,
            "rpc_batch_size": 100,
            "rpc_concurrency": 8,
            "rpc_min_batch_size": 10,
            "rpc_concurrency_rungs": [8, 4, 2],
        },
        strict=True,
    )

    assert settings.rpc_concurrency_rungs == (8, 4, 2)
    assert settings.model_dump(mode="json")["rpc_concurrency_rungs"] == [8, 4, 2]


def test_split_metadata_rejects_unknown_durable_values() -> None:
    with pytest.raises(ValidationError):
        CompactValidationReport(status="ok")

    with pytest.raises(ValidationError):
        SplitMaterializationMetadata(outcome="updated", file_count=1)
