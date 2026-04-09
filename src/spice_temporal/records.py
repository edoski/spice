"""Core record types shared across the project."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BlockRecord:
    block_number: int
    timestamp: int
    base_fee_per_gas: int
    gas_used: int
    gas_limit: int
    chain_id: int

    @property
    def gas_utilization(self) -> float:
        if self.gas_limit <= 0:
            raise ValueError("gas_limit must be positive to compute gas utilization")
        return self.gas_used / self.gas_limit
