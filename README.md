# SPICE

Lean temporal-module baseline for SPICE-style fee-timing experiments.

This repository is intentionally scoped to the temporal module only:

- pull raw EVM block data
- enrich missing block fields
- build fixed-horizon temporal datasets
- train baseline sequence models
- run evaluation-day temporal simulations

It does not implement the broader SPICE spatial/oracle/reputation system.

## Stack

- `Typer` + `Rich` for CLI and progress output
- `Pydantic v2` + `pydantic-settings` for config, settings, manifests, and reports
- `Polars` for Parquet IO, validation scans, canonicalization, and feature prep
- `HTTPX` for JSON-RPC transport
- `scikit-learn` for weighted feature scaling
- `NumPy` + `PyTorch` for dataset math, modeling, training, inference, and simulation

## Package Layout

The installable namespace is `spice`, so the source layout stays `src/spice/...`.
The package itself is now split into four shallow subpackages plus two top-level entrypoints:

- `src/spice/core`: config, settings, constants, and console/reporting primitives
- `src/spice/acquisition`: raw pulls, RPC, enrichment, validation, and provenance
- `src/spice/data`: Parquet IO, feature engineering, dataset geometry, and scaling
- `src/spice/modeling`: models, training, inference, simulation, artifacts, and reports
- `src/spice/api.py`: supported high-level Python API
- `src/spice/cli.py`: supported CLI surface

There are no dual paths for old/new formats. Runtime block datasets are Parquet-only.
Named snapshots live under `output_root/datasets/<chain>/<snapshot>/...`.
Under `enriched/`, datasets are canonical model inputs with exactly these six `Int64`
columns: `block_number`, `timestamp`, `base_fee_per_gas`, `gas_used`, `chain_id`,
and `gas_limit`.

## Configuration

Experiment configuration is loaded from YAML through `spice.core.config.ExperimentConfig`.
Environment-backed RPC settings are loaded through `spice.core.settings.RuntimeSettings`.

Supported environment variables:

- `RPC_PROVIDER`
- `ETHEREUM_RPC_URL`
- `POLYGON_RPC_URL`
- `AVALANCHE_RPC_URL`
- `ALCHEMY_API_KEY`

## CLI

The installed command is `spice`.

Examples:

- `spice acquire configs/pilots/ethereum-36s.yaml --provider publicnode --no-dry-run`
- `spice train configs/pilots/ethereum-36s.yaml lstm --device cpu`
- `spice train configs/pilots/ethereum-36s.yaml lstm --device cpu --evaluate`
- `spice simulate configs/pilots/ethereum-36s.yaml lstm --device cpu`
- `spice datasets list configs/pilots/ethereum-36s.yaml`

The CLI infers chain and delay values only when the config makes them unambiguous.
It uses Rich progress for acquisition and training, then prints concise stable summary lines.

## Python API

`spice.api` is the only supported Python API surface.

```python
from pathlib import Path

from spice.api import (
    acquire_snapshot,
    load_config,
    simulate_model,
    train_model,
)

config = load_config(Path("configs/pilots/ethereum-36s.yaml"))

acquire_result = acquire_snapshot(
    config,
    "ethereum",
    snapshot_name="working",
    rpc_provider="publicnode",
    dry_run=False,
)

train_result = train_model(
    config,
    "lstm",
    "ethereum",
    36,
    device="cpu",
)

simulation_result = simulate_model(config, "lstm", "ethereum", 36, device="cpu")
```

## Artifacts

Training writes:

- `artifact.json`
- `model.pt`
- `train_report.json`

Simulation writes:

- `simulation_report.json`

Dataset provenance is stored under `.spice/source.json` inside dataset directories.
Snapshot activation and summary metadata are stored under
`output_root/datasets/<chain>/.spice/snapshots.json`.

## Verification

Run all checks inside the project virtual environment:

- `.venv/bin/ruff check src/spice tests`
- `.venv/bin/pyright src/spice tests`
- `.venv/bin/pytest -q`
