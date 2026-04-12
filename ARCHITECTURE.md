# Architecture Guide

## Overview

Runtime commands:

1. `spice acquire`
2. `spice tune`
3. `spice train`
4. `spice simulate`

One CLI. One config system. One feature path.

## Config Flow

Config loading lives in [src/spice/core/config.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/core/config.py).

Flow:

1. Hydra composes the task root from [src/spice/conf](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/conf).
2. `experiment=<name>` selects a saved experiment spec from `conf/experiment/`.
3. `feature_set=<name>` selects ordered outputs from `conf/feature_set/`.
4. Chain-specific RPC profile overrides are applied.
5. Derived paths are rebuilt.
6. Final config is validated through Pydantic.

Public dataset definition:

- `evaluation.date` defines the fixed one-day UTC evaluation window.
- `dataset.sampling.sample_count` defines training and tuning sample count.
- `acquisition.history_sample_budget` optionally acquires more history than training uses.

## Feature Architecture

Feature execution lives in [src/spice/features](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/features).

Rules:

- each feature is a small Hamilton node
- feature selection is config-driven
- feature formulas stay in Python
- warmup is derived from the selected graph
- training persists `feature_set_id`, ordered `feature_names`, and `feature_graph_fingerprint`
- simulation rebuilds the exact same graph and fails on mismatch

## Package Roles

### `core`

- [config.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/core/config.py): typed config schema, Hydra composition, path derivation
- [console.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/core/console.py): workflow reporting
- [json.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/core/json.py): JSON artifact writes
- [files.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/core/files.py): atomic file and directory promotion helpers

### `acquisition`

- workflow/planning derives required history length before acquisition runs
- [rpc.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/acquisition/rpc.py): block planning, RPC pulling, adaptive batching
- [datasets.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/acquisition/datasets.py): history and evaluation dataset reuse
- [metadata.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/acquisition/metadata.py): typed dataset metadata

### `features`

- [engine.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/features/engine.py): Hamilton driver, feature selection, warmup, fingerprinting
- [base.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/features/base.py): base nodes
- [rolling.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/features/rolling.py): rolling statistics
- [trend.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/features/trend.py): trend features

### `data`

- [block_contract.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/data/block_contract.py): canonical block schema
- [io.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/data/io.py): parquet dataset discovery and loading
- [datasets.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/data/datasets.py): temporal geometry and array-backed stores
- [normalization.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/data/normalization.py): scaler fitting and application
- [validation.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/data/validation.py): dataset validation

### `modeling`

- [pipeline.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/modeling/pipeline.py): training and inference dataset preparation
- [training.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/modeling/training.py): trainer execution and metrics
- [execution.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/modeling/execution.py): persisted training flow
- [artifacts.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/modeling/artifacts.py): model + manifest persistence and feature validation
- [simulation.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/modeling/simulation.py): Poisson-arrival simulation over evaluation examples

### `workflows`

- [acquire.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/workflows/acquire.py): acquisition orchestration and workflow-side history sizing
- [tune.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/workflows/tune.py): Optuna orchestration
- [train.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/workflows/train.py): artifact-producing training orchestration
- [simulate.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/workflows/simulate.py): evaluation-day simulation orchestration
- [_shared.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/workflows/_shared.py): shared runtime helpers

## Storage Layout

Datasets:

- `artifacts/datasets/<chain>/<dataset_id>/history/...`
- `artifacts/datasets/<chain>/<dataset_id>/evaluation/...`
- `artifacts/datasets/<chain>/<dataset_id>/.spice/metadata.json`

Models:

- `artifacts/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/<variant>/<study_id>/artifact.json`
- `artifacts/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/<variant>/<study_id>/model.pt`
- `artifacts/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/<variant>/<study_id>/train_report.json`

Tuning:

- `artifacts/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/tuned/<study_id>/tuning/study.json`
- `artifacts/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/tuned/<study_id>/tuning/trials.json`
- `artifacts/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/tuned/<study_id>/tuning/best_params.json`
