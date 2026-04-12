# SPICE

SPICE is a temporal fee-timing pipeline for EVM chains. It acquires canonical block datasets, builds Hamilton-based feature tables, tunes models, trains artifacts, and runs evaluation-day simulations.

## Stack

- `Hydra` for config composition
- `Typer` for the root CLI
- `sf-hamilton` for feature/dataflow execution
- `Lightning` + `PyTorch` for training
- `Optuna` for tuning
- `web3.py` for RPC access
- `Polars` + `Pandera` for block-table validation and dataset IO

## Setup

```bash
.venv/bin/pip install -e .
```

Provider credentials:

- `direct`: export `ETHEREUM_RPC_URL`, `POLYGON_RPC_URL`, `AVALANCHE_RPC_URL`
- `alchemy`: export `ALCHEMY_API_KEY`

## CLI

Everything runs through one command:

```bash
.venv/bin/spice acquire experiment=icdcs_2025_11_09
.venv/bin/spice train experiment=icdcs_2025_11_09 model=lstm feature_set=icdcs_2026
.venv/bin/spice tune experiment=icdcs_2025_11_09 model=lstm feature_set=icdcs_2026 tuning.trial_count=20
.venv/bin/spice simulate experiment=icdcs_2025_11_09 artifact.variant=baseline
```

Typer handles subcommands. Hydra owns all config overrides.

## Config

Saved experiment specs live in [src/spice/conf/experiment](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/conf/experiment).

Named feature sets live in [src/spice/conf/feature_set](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/conf/feature_set).

Rules:

- YAML selects experiments and feature sets.
- Python defines feature logic.
- `train` and `tune` choose `feature_set=<name>`.
- `simulate` rebuilds the feature graph from the trained artifact and fails on mismatch.

## Output Layout

- history blocks: `artifacts/datasets/<chain>/<dataset_id>/history/...`
- evaluation blocks: `artifacts/datasets/<chain>/<dataset_id>/evaluation/...`
- dataset metadata: `artifacts/datasets/<chain>/<dataset_id>/.spice/metadata.json`
- model artifacts: `artifacts/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/<variant>/<study_id>/...`
- tuning outputs: `artifacts/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/tuned/<study_id>/tuning/...`

## Verification

```bash
.venv/bin/ruff check src/spice tests
.venv/bin/pyright
.venv/bin/pytest -q
```
