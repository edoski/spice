from __future__ import annotations

import pytest

from spice.acquisition.rpc.client import BlockRpcClient


def test_block_range_validation_rejects_misaligned_batch_response() -> None:
    with pytest.raises(ValueError, match="expected block 101 at index 1"):
        BlockRpcClient._validate_range_blocks(
            [{"number": 100}, {"number": 102}],
            start=100,
            end=102,
        )


def test_block_range_validation_accepts_hex_block_numbers() -> None:
    BlockRpcClient._validate_range_blocks(
        [{"number": "0x64"}, {"number": "0x65"}],
        start=100,
        end=102,
    )
