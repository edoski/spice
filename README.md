# SPICE

SPICE is a temporal fee-timing pipeline for EVM chains. It acquires canonical block datasets, builds Hamilton-based feature tables, tunes models, trains artifacts, and runs evaluation-day simulations.

## Stack

- `Typer` for the root CLI
- `Pydantic` + `PyYAML` for explicit config loading
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

Everything runs through one command with explicit flags:

```bash
.venv/bin/spice acquire --preset icdcs_2026
.venv/bin/spice acquire --preset icdcs_2026 --chain avalanche --provider publicnode
.venv/bin/spice train --preset icdcs_2026 --model lstm --feature-set icdcs_2026
.venv/bin/spice tune --preset icdcs_2026 --model lstm --feature-set icdcs_2026 --trial-count 20
.venv/bin/spice simulate --preset icdcs_2026 --variant baseline
```

Override files stay plain YAML:

```bash
.venv/bin/spice train --preset icdcs_2026 --config local/train.yaml
```

## Config

Config loading lives in [src/spice/config](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/config).

Named specs live under [src/spice/conf](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/conf):

- `preset/`: convenience bundles of named selectors
- `dataset/`: dataset contracts
- `chain/`, `provider/`: chain and RPC specs
- `model/`, `feature_set/`: modeling choices
- `training/`, `split/`, `simulation/`, `acquisition/`, `tuning/`, `tuning_space/`: workflow profiles

Rules:

- Presets are optional. They are not the canonical schema.
- `dataset.history_context_blocks` is the dataset contract boundary for feature warmup + lookback.
- `acquire` uses the dataset contract to fetch enough raw blocks.
- `train` and `simulate` validate that the selected feature graph fits inside that contract.

## Output Layout

- history blocks: `outputs/datasets/<chain>/<dataset_id>/history/...`
- evaluation blocks: `outputs/datasets/<chain>/<dataset_id>/evaluation/...`
- dataset metadata: `outputs/datasets/<chain>/<dataset_id>/.spice/metadata.json`
- model artifacts: `outputs/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/<variant>/<study_id>/...`
- tuning outputs: `outputs/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/tuned/<study_id>/tuning/...`

`outputs/` is the default root. Override it only when you want isolation somewhere else.

## Verification

```bash
.venv/bin/ruff check src/spice tests
.venv/bin/pyright
.venv/bin/pytest -q
```
