# Architecture Guide

## Overview

Runtime commands:

1. `spice acquire`
2. `spice tune`
3. `spice train`
4. `spice simulate`

One CLI. One config system. One feature path.

## Config Flow

Config loading lives in [src/spice/config](src/spice/config).

Flow:

1. The loader reads named specs from [src/spice/conf](src/spice/conf).
2. `spice config` authors repo-local YAML specs directly under that tree.
3. `--preset` optionally selects a bundle of named defaults.
4. `--config PATH` overlays plain YAML on top of that preset.
5. Explicit CLI flags override both preset and file values.
6. Pydantic validates the final request model.
7. `PathLayout` derives deterministic storage ids and roots from `storage.root`.

Selector rules:

- `dataset.name` and `study.name` are human selectors.
- `dataset_id`, `study_id`, and `artifact_id` are deterministic storage ids.
- Runtime commands work from selectors. Users do not need paths.

Public dataset definition:

- `dataset.evaluation_date` defines the fixed one-day UTC evaluation window.
- `dataset.sampling.sample_count` defines training and tuning sample count.
- `dataset.history_context_blocks` defines the dataset contract boundary.
- `acquisition.history_sample_budget` optionally acquires more history than training uses.

## Feature Architecture

Feature execution lives in [src/spice/features](src/spice/features).

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

- [models.py](src/spice/config/models.py): typed specs, workflow request models, path layout, provider resolution
- [loader.py](src/spice/config/loader.py): named YAML loading, fixed-order merges, CLI/file override composition
- `registry.py`: config group registry, canonical YAML serialization, create/update/delete helpers

### `core`

- [console.py](src/spice/core/console.py): workflow reporting
- [files.py](src/spice/core/files.py): atomic file and directory promotion helpers

### `state`

- `engine.py`: SQLAlchemy engine creation, SQLite PRAGMAs, root-kind bootstrap
- `schema.py`: SPICE-owned Core table definitions
- `catalog.py`: global selector-to-root catalog
- `dataset.py`: dataset summary + acquire-run persistence
- `artifact.py`: manifest, training, and simulation persistence
- `study.py`: Optuna-backed study helpers and tuned-param loading
- `show.py`: selector-resolved inspection helpers

### `acquisition`

- workflow/planning derives required history length before acquisition runs
- [rpc.py](src/spice/acquisition/rpc.py): block planning, RPC pulling, adaptive batching
- [datasets.py](src/spice/acquisition/datasets.py): history and evaluation dataset reuse
- [metadata.py](src/spice/acquisition/metadata.py): typed dataset summary builders

### `features`

- [engine.py](src/spice/features/engine.py): Hamilton driver, feature selection, warmup, fingerprinting
- [base.py](src/spice/features/base.py): base nodes
- [rolling.py](src/spice/features/rolling.py): rolling statistics
- [trend.py](src/spice/features/trend.py): trend features

### `data`

- [block_contract.py](src/spice/data/block_contract.py): canonical block schema
- [io.py](src/spice/data/io.py): parquet dataset discovery and loading
- [datasets.py](src/spice/data/datasets.py): array-backed stores and split helpers
- [normalization.py](src/spice/data/normalization.py): scaler fitting and application
- [validation.py](src/spice/data/validation.py): dataset validation

### `planning`

- [geometry.py](src/spice/planning/geometry.py): shared lookback, delay, action-count, and history-sizing math

### `modeling`

- [pipeline.py](src/spice/modeling/pipeline.py): training and inference dataset preparation
- [training.py](src/spice/modeling/training.py): trainer execution and metrics
- [execution.py](src/spice/modeling/execution.py): persisted training flow
- [artifacts.py](src/spice/modeling/artifacts.py): model + manifest persistence and feature validation
- [reporting.py](src/spice/modeling/reporting.py): internal summary objects
- [simulation.py](src/spice/modeling/simulation.py): Poisson-arrival simulation over evaluation examples

### `workflows`

- [acquire.py](src/spice/workflows/acquire.py): acquisition orchestration
- [tune.py](src/spice/workflows/tune.py): Optuna orchestration with `RDBStorage`
- [train.py](src/spice/workflows/train.py): artifact-producing training orchestration
- [simulate.py](src/spice/workflows/simulate.py): evaluation-day simulation orchestration
- [_shared.py](src/spice/workflows/_shared.py): shared runtime helpers

## Storage Layout

Datasets:

- `outputs/datasets/<chain>/<dataset_id>/history/...`
- `outputs/datasets/<chain>/<dataset_id>/evaluation/...`
- `outputs/datasets/<chain>/<dataset_id>/.spice/state.sqlite`

Models:

- `outputs/models/<chain>/<artifact_id>/model.pt`
- `outputs/models/<chain>/<artifact_id>/.spice/state.sqlite`

Tuning:

- `outputs/studies/<chain>/<study_id>/.spice/state.sqlite`

Notes:

- `outputs/.spice/catalog.sqlite` is the global lookup index
- `src/spice/conf` is the saved spec registry
- SPICE-owned structured state lives only in `.spice/state.sqlite`
- studies and artifacts are separate roots
- `spice config ...` is the human-facing config authoring path
- `spice show dataset|study|artifact` is the human-facing inspection path
- `spice delete dataset|study|artifact` is the cleanup path
