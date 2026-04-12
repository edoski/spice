# Architecture Guide

## Overview

Runtime commands:

1. `spice acquire`
2. `spice tune`
3. `spice train`
4. `spice simulate`

One CLI. One config system. One feature path.

## Config Flow

Config loading lives in [src/spice/config](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/config).

Flow:

1. The loader reads named specs from [src/spice/conf](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/conf).
2. `--preset` optionally selects a bundle of named defaults.
3. `--config PATH` overlays plain YAML on top of that preset.
4. Explicit CLI flags override both preset and file values.
5. Pydantic validates the final request model.
6. `PathLayout` derives concrete dataset and model paths from `storage.root`.

Public dataset definition:

- `dataset.evaluation_date` defines the fixed one-day UTC evaluation window.
- `dataset.sampling.sample_count` defines training and tuning sample count.
- `dataset.history_context_blocks` defines the dataset contract boundary.
- `acquisition.history_sample_budget` optionally acquires more history than training uses.

## Feature Architecture

Feature execution lives in [src/spice/features](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/features).

Rules:

- each feature is a small Hamilton node
- feature selection is config-driven
- feature formulas stay in Python
- warmup is derived from the selected graph
- dataset contracts may over-provision history relative to one feature set
- training persists `feature_set_id`, ordered `feature_names`, and `feature_graph_fingerprint`
- simulation rebuilds the exact same graph and fails on mismatch

## Package Roles

### `config`

- [models.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/config/models.py): typed specs, workflow request models, path layout, provider resolution
- [loader.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/config/loader.py): named YAML loading, fixed-order merges, CLI/file override composition

### `core`

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
- [datasets.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/data/datasets.py): array-backed stores and split helpers
- [normalization.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/data/normalization.py): scaler fitting and application
- [validation.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/data/validation.py): dataset validation

### `planning`

- [geometry.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/planning/geometry.py): shared lookback, delay, action-count, and history-sizing math

### `modeling`

- [pipeline.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/modeling/pipeline.py): training and inference dataset preparation
- [training.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/modeling/training.py): trainer execution and metrics
- [execution.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/modeling/execution.py): persisted training flow
- [artifacts.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/modeling/artifacts.py): model + manifest persistence and feature validation
- [simulation.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/modeling/simulation.py): Poisson-arrival simulation over evaluation examples

### `workflows`

- [acquire.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/workflows/acquire.py): acquisition orchestration
- [tune.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/workflows/tune.py): Optuna orchestration
- [train.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/workflows/train.py): artifact-producing training orchestration
- [simulate.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/workflows/simulate.py): evaluation-day simulation orchestration
- [_shared.py](/Users/edo/Documents/Obsidian/the-vault/university/Thesis/spice/src/spice/workflows/_shared.py): shared runtime helpers

## Storage Layout

Datasets:

- `outputs/datasets/<chain>/<dataset_id>/history/...`
- `outputs/datasets/<chain>/<dataset_id>/evaluation/...`
- `outputs/datasets/<chain>/<dataset_id>/.spice/metadata.json`

Models:

- `outputs/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/<variant>/<study_id>/artifact.json`
- `outputs/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/<variant>/<study_id>/model.pt`
- `outputs/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/<variant>/<study_id>/train_report.json`

Tuning:

- `outputs/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/tuned/<study_id>/tuning/study.json`
- `outputs/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/tuned/<study_id>/tuning/trials.json`
- `outputs/models/<chain>/<dataset_id>/<feature_set>/<family>/<delay>s/tuned/<study_id>/tuning/best_params.json`
