# SPICE

SPICE is a temporal fee-timing pipeline for EVM chains. It acquires canonical block datasets, builds Hamilton-based feature tables, tunes models, trains artifacts, and runs evaluation-day simulations.

## Stack

- `Typer` for the root CLI
- `Pydantic` + `PyYAML` for explicit config loading
- `SQLAlchemy Core` for SPICE-owned structured state
- `sf-hamilton` for feature/dataflow execution
- `Lightning` + `PyTorch` for training
- `Optuna` for tuning and study persistence
- `web3.py` for RPC access
- `Polars` + `Pandera` for block-table validation and dataset IO

## Setup

```bash
brew install uv
uv sync --extra dev
source .venv/bin/activate
```

`uv` manages the repo-local `.venv/`. If you do not want to activate it, prefix commands with `uv run`.

Provider credentials:

- `direct`: export `ETHEREUM_RPC_URL`, `POLYGON_RPC_URL`, `AVALANCHE_RPC_URL`
- `alchemy`: export `ALCHEMY_API_KEY`

## CLI

Everything runs through one command with explicit flags:

```bash
spice acquire --preset icdcs_2026
spice acquire --preset icdcs_2026 --chain avalanche --provider publicnode
spice train --preset icdcs_2026 --model lstm --feature-set icdcs_2026
spice tune --preset icdcs_2026 --model lstm --feature-set icdcs_2026 --trial-count 20
spice simulate --preset icdcs_2026 --variant baseline
spice config list provider
spice config show dataset icdcs_2026
spice config create chain my_chain --set runtime.chain_id=123 --set runtime.block_time_seconds=2.0 --set runtime.uses_poa_extra_data=false
spice config update provider direct --set chains.my_chain.endpoint.env_var=MY_CHAIN_RPC_URL
spice config delete preset old_preset
spice show dataset
spice show artifact --chain avalanche --dataset icdcs_2026 --model lstm --task icdcs_2026 --variant baseline
spice show study --chain avalanche --dataset icdcs_2026 --model lstm --task icdcs_2026 --study default
spice show study --chain avalanche --dataset icdcs_2026 --model lstm --task icdcs_2026 --study default --detail config
spice delete artifact --chain avalanche --dataset icdcs_2026 --model lstm --task icdcs_2026 --variant baseline
```

Override files stay plain YAML:

```bash
spice train --preset icdcs_2026 --config local/train.yaml
```

## Config

Config loading lives in [src/spice/config](src/spice/config).

Named specs live under [src/spice/conf](src/spice/conf):

- `preset/`: convenience bundles of named selectors
- `dataset/`: dataset contracts
- `chain/`, `provider/`: chain and RPC specs
- `model/`, `feature_set/`: modeling choices
- `training/`, `split/`, `simulation/`, `acquisition/`, `tuning/`, `tuning_space/`: workflow profiles

Core spec authoring now goes through `spice config`:

- `spice config list <group>`
- `spice config show <group> <name>`
- `spice config create <group> <name> --set path=value ...`
- `spice config update <group> <name> --set path=value ... --unset path ...`
- `spice config delete <group> <name> [--force]`

Phase 2a authorable groups:

- `chain`
- `provider`
- `dataset`
- `task`
- `execution`
- `feature-set`
- `preset`

Rules:

- Presets are optional. They are not the canonical schema.
- `spice config` writes canonical YAML into `src/spice/conf/<group>/<name>.yaml`.
- `dataset.history_context_blocks` is the dataset contract boundary for feature warmup + lookback.
- `acquire` uses the dataset contract to fetch enough raw blocks.
- `train` and `simulate` validate that the selected feature graph fits inside that contract.

## Output Layout

- catalog: `outputs/.spice/catalog.sqlite`
- history blocks: `outputs/datasets/<chain>/<dataset_id>/history/...`
- evaluation blocks: `outputs/datasets/<chain>/<dataset_id>/evaluation/...`
- dataset state: `outputs/datasets/<chain>/<dataset_id>/.spice/state.sqlite`
- tuned study state: `outputs/studies/<chain>/<study_id>/.spice/state.sqlite`
- model artifacts: `outputs/models/<chain>/<artifact_id>/...`
- artifact state: `outputs/models/<chain>/<artifact_id>/.spice/state.sqlite`

`outputs/` is the default root. Override it only when you want isolation somewhere else.

Users query by selectors such as `--dataset`, `--study`, `--model`, `--task`, and `--variant`.
The filesystem ids are deterministic internal storage ids. The catalog maps selectors to roots.
Structured state is SQLite-only. SPICE no longer persists generated JSON metadata or report files.
Re-running `spice tune` with the same study resumes that study up to the requested total `--trial-count`.

## Verification

```bash
ruff check src/spice tests
pyright
pytest -q
```
