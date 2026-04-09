"""Block loading and validation."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from spice_temporal.records import BlockRecord

REQUIRED_BLOCK_COLUMNS = {
    "block_number",
    "timestamp",
    "base_fee_per_gas",
    "gas_used",
    "gas_limit",
    "chain_id",
}


def _coerce_block_row(row: dict[str, Any]) -> BlockRecord:
    missing = REQUIRED_BLOCK_COLUMNS - row.keys()
    if missing:
        raise ValueError(f"Missing required block columns: {sorted(missing)}")
    return BlockRecord(
        block_number=int(row["block_number"]),
        timestamp=int(row["timestamp"]),
        base_fee_per_gas=int(row["base_fee_per_gas"]),
        gas_used=int(row["gas_used"]),
        gas_limit=int(row["gas_limit"]),
        chain_id=int(row["chain_id"]),
    )


def load_block_records(path: Path) -> list[BlockRecord]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list):
            raise TypeError("JSON block files must contain a list of rows")
        return [_coerce_block_row(item) for item in data]
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            return [_coerce_block_row(row) for row in reader]
    if suffix == ".parquet":
        try:
            import pyarrow.parquet as pq
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Reading parquet files requires pyarrow. Install project dependencies first."
            ) from exc

        table = pq.read_table(path)
        return [_coerce_block_row(row) for row in table.to_pylist()]
    raise ValueError(f"Unsupported block file format: {path.suffix}")
