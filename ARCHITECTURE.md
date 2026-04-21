# Architecture Guide

## Overview

Runtime commands:

1. `spice acquire`
2. `spice tune`
3. `spice train`
4. `spice evaluate`

SPICE keeps six strong seams:

1. feature family
2. temporal compiler
3. prediction family
4. evaluator
5. model family
6. representation

Everything else exists to load config, materialize storage, and drive workflows around those seams.

## Core Model

Canonical domain truth is:

- raw block corpus
- resolved feature table
- compiled problem store

Model-input compilation is separate from prediction semantics:

- the current shipped representation is `sequence_inputs`
- prediction families attach their own targets after representation preparation
- model families consume compiled representations and family-owned targets

This keeps corpus storage, temporal lowering, and prediction behavior independent.

## Config Flow

Config loading lives in [src/spice/config](src/spice/config).

Flow:

1. load named YAML specs from [src/spice/conf](src/spice/conf)
2. optionally apply one preset
3. apply explicit selector and runtime overrides
4. validate one typed workflow config
5. derive deterministic storage paths through storage helpers

Presets stay flat and workflow-owned. Execution target selection is separate and happens at submission time.

Important selectors:

- `dataset`
- `chain`
- `provider`
- `problem`
- `feature_set`
- `prediction`
- `model`
- `study`
- `variant`

Important runtime overrides:

- `delay_seconds`
- `trial_count`
- `dry_run`

Public temporal contract stays seconds-native:

- `problem.lookback_seconds`
- `problem.max_delay_seconds`
- `delay_seconds`

## Feature Architecture

Feature execution lives in [src/spice/features](src/spice/features).

Current feature families:

- `block_native`
- `time_native`

Execution model:

- one explicit family spec per family
- one explicit feature map per family
- one canonical block series build
- one explicit dependency closure and topological execution order
- one family implementation fingerprint derived from requested outputs plus `fingerprint_sources`

Artifacts persist:

- `feature_set_id`
- `feature_family_id`
- ordered `feature_names`
- `feature_graph_fingerprint`
- feature prerequisites

Changing family implementation bytes changes the fingerprint and invalidates old artifact compatibility by design.

## Temporal Semantics

Temporal lowering lives in [src/spice/temporal](src/spice/temporal).

Current compilers:

- `timestamp_native`
- `estimated_block`

Both lower into the same `CompiledProblemStore` shape:

- `anchor_rows`
- `context_start_rows`
- `candidate_end_rows`
- `max_candidate_slots`

Workflows and prediction families consume compiled contracts and stores only. They do not branch on compiler-specific runtime shapes.

## Prediction and Evaluation

Prediction execution lives in [src/spice/prediction](src/spice/prediction).

Current shipped families:

- `candidate_offset_selection`
- `min_block_fee_multitask`

Family-owned responsibilities:

- target preparation
- output head definition
- training loss
- epoch metrics
- best-epoch selection
- decode

Evaluation stays separate in [src/spice/evaluation](src/spice/evaluation). Evaluators consume decoded offsets plus a compiled problem store.

## Modeling Boundary

Model families live in [src/spice/modeling/families](src/spice/modeling/families).

The current shipped representation is `sequence_inputs`. That boundary stays real even though only one public representation id ships today, because models still consume prepared inputs through an explicit representation seam rather than family-specific input wiring.

Dataset preparation is a separate seam in [src/spice/modeling/dataset_builders](src/spice/modeling/dataset_builders). The current shipped builders are `standard_temporal` and `professor_temporal`.

## CLI Shape

The CLI has three categories:

1. workflow commands
2. config commands
3. storage / transfer commands

Workflow commands:

- `acquire`
- `tune`
- `train`
- `evaluate`
- `train|tune|evaluate --submit`

Human workflow output goes through one concrete reporter in [src/spice/core/reporting.py](src/spice/core/reporting.py). The contract is intentionally small:

- one header line
- milestone lines for meaningful state changes
- one compact result line

`train` keeps one epoch-end line per completed epoch. `tune` keeps one completed-trial line per trial and does not print per-epoch trial output.

State commands:

- `show dataset|study|artifact`
- `delete dataset|study|artifact`
- `push dataset|study`
- `pull artifact|study`
- `refresh catalog`

`show` and `delete` are selector-driven over already-materialized state. They do not use workflow config resolution.

## Storage Layout

Storage code lives in [src/spice/storage](src/spice/storage).

Roots:

- corpora: `outputs/corpora/<chain>/<corpus_id>/...`
- studies: `outputs/studies/<chain>/<study_id>/...`
- artifacts: `outputs/artifacts/<chain>/<artifact_id>/...`

State:

- one SQLite file per root under `.spice/state.sqlite`
- one global catalog at `outputs/.spice/catalog.sqlite`

Important invariants:

- root-kind enforcement stays strict
- dataset, study, and artifact ids are deterministic
- catalog rebuild and delete cascades are storage-owned
- on-disk payload meanings stay explicit and typed

## Execution and Acquisition

Acquisition logic lives in [src/spice/acquisition](src/spice/acquisition) and [src/spice/workflows/acquire.py](src/spice/workflows/acquire.py).

Execution and sync backends are concrete:

- SSH
- `rsync`
- SLURM
- checked-in sync helper actions in [src/spice/storage/sync_actions.py](src/spice/storage/sync_actions.py)

Submission lives in [src/spice/execution](src/spice/execution) and always uses the checked-in L40 target spec. Storage sync lives in [src/spice/storage/sync.py](src/spice/storage/sync.py).

## Package Roles

- `config`: typed config models, loaders, registry-backed YAML access
- `features`: explicit feature-family contracts and execution
- `temporal`: compiler contracts and compiled problem-store lowering
- `prediction`: family-owned prediction semantics
- `evaluation`: evaluator contracts and execution
- `modeling`: dataset builders, representations, models, training, artifacts, results
- `corpus`: block IO, metadata, builders, validation
- `execution`: workflow submission backends
- `storage`: catalog, manifest persistence, inspection, root operations
- `workflows`: acquire, tune, train, evaluate orchestration
