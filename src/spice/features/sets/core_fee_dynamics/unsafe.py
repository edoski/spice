"""Unsafe same-block gas/tx comparator catalog."""

from __future__ import annotations

from pathlib import Path

from ._family_builder import base_outputs, build_catalog, fingerprint_sources

CORE_FEE_DYNAMICS_UNSAFE_OUTPUTS = base_outputs(block_fact_mode="current")
CORE_FEE_DYNAMICS_UNSAFE_FINGERPRINT_SOURCES = fingerprint_sources(
    Path(__file__).resolve()
)

CORE_FEE_DYNAMICS_UNSAFE = build_catalog(
    variant_module_path=Path(__file__).resolve(),
    block_fact_mode="current",
    gas_utilization_source="current_gas_utilization",
    gas_utilization_base_warmup_rows=0,
    allowed_outputs=CORE_FEE_DYNAMICS_UNSAFE_OUTPUTS,
)
