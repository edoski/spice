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

Everything else exists to resolve config, derive storage identity and layout, and drive workflows around those seams.

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

Config resolution lives in [src/spice/config](src/spice/config):

- `registry.py`: named spec discovery, validation, and canonical YAML helpers
- `presets.py`: preset overlay validation, `extends` resolution, request overlays
- `resolution.py`: workflow request handling and payload-to-config resolution
- `models.py`: resolved runtime config models

Flow:

1. load named YAML specs from [src/spice/conf](src/spice/conf)
2. resolve one preset, including its single optional `extends` parent chain
3. apply the small workflow override surface
4. validate one typed workflow config and resolve one chain-specific RPC endpoint for `acquire`
5. derive deterministic storage identities and paths through storage helpers

Presets are the workflow-owned experiment unit. Internally they are overlay configs
resolved through one `extends` chain, which keeps user-facing YAML readable without
making every internal seam a workflow flag.

Public `spice config` groups:

- `preset`
- `dataset`
- `chain`
- `provider`
- `problem`

Internal registry-loaded groups:

- `model`
- `dataset_builder`
- `feature_set`
- `prediction`
- `evaluation`
- `objective`
- `tuning_space`
- `execution`

Workflow selectors:

- `preset`
- `chain`

`provider` remains a named config seam and public config group, but it is preset-owned
runtime configuration rather than a workflow selector. `acquire` resolves that provider
spec into one chain-specific RPC endpoint before runtime code starts.

Important runtime overrides:

- `delay_seconds`
- `trial_count`
- `dry_run`
- `study`
- `variant`

Public temporal contract stays seconds-native:

- `problem.lookback_seconds`
- `problem.max_delay_seconds`
- `delay_seconds`

## Feature Architecture

Feature execution lives in [src/spice/features](src/spice/features).

Current feature families:

- `block_native`
- `block_open_native`
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
Feature fingerprints use package-relative source ids plus implementation bytes,
so equivalent checkouts under different absolute paths produce the same graph id.

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
Compiler runtime metadata is serialized through compiler registry entries, not a
central temporal union. Dataset builders persist typed builder metadata and route
compiler-owned payloads back through the registry.

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

Evaluation stays separate in [src/spice/evaluation](src/spice/evaluation). Evaluators consume declared decoded-result semantics plus a compiled problem store.
`DecodedOffsets` is one prediction-owned decoded-result implementation. Evaluator
contracts declare the decoded-result id they accept, and workflows validate the
prediction/evaluator pairing before inference.

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
The same applies to `push` and `pull`: their selector flags identify existing
storage records, not workflow composition seams.

## Storage Layout

Storage code lives in [src/spice/storage](src/spice/storage). Identity assembly
and path layout are split deliberately:

- `identity.py` owns canonical provenance payloads for study and artifact ids
- `layout.py` owns deterministic root formatting from those ids

Roots:

- corpora: `outputs/corpora/<chain>/<corpus_id>/...`
- studies: `outputs/studies/<chain>/<study_id>/...`
- artifacts: `outputs/artifacts/<chain>/<artifact_id>/...`

State:

- one SQLite file per root under `.spice/state.sqlite`
- one global catalog at `outputs/.spice/catalog.sqlite`

Important invariants:

- root-kind enforcement stays strict
- corpus ids cover raw chain/dataset storage only
- study and artifact ids are deterministic
- study ids hash durable search semantics but exclude run limits such as
  `trial_count` and `timeout_seconds`
- artifact ids hash full resolved provenance, excluding pure output locations
  such as `storage.root`
- workflows validate raw corpus coverage against compiled feature prerequisites,
  lookback, warmup rows, candidate horizon, and evaluation delay
- catalog rebuild and delete cascades are storage-owned
- on-disk payload meanings stay explicit and typed

## Execution and Acquisition

Acquisition logic lives in [src/spice/acquisition](src/spice/acquisition) and [src/spice/workflows/acquire.py](src/spice/workflows/acquire.py).

Execution and sync backends are concrete:

- SSH
- `rsync`
- SLURM
- checked-in sync helper actions in [src/spice/storage/sync_actions.py](src/spice/storage/sync_actions.py)

Submission lives in [src/spice/execution](src/spice/execution). `--target`
selects a named execution spec, and submission sends a resolved config snapshot
instead of re-resolving request JSON remotely. Storage sync lives in
[src/spice/storage/sync.py](src/spice/storage/sync.py).

Reference reconstruction lives under [src/spice/reconstruction](src/spice/reconstruction)
and is quarantined as explicit analysis tooling. It requires a user-provided
reference root and is not on the acquire/train/evaluate/tune runtime path.

## Package Roles

- `config`: registry-backed YAML access, preset overlays, workflow request resolution, typed runtime config models
- `features`: explicit feature-family contracts and execution
- `temporal`: compiler contracts and compiled problem-store lowering
- `prediction`: family-owned prediction semantics
- `evaluation`: evaluator contracts and execution
- `modeling`: dataset builders, representations, models, training, artifacts, results
- `corpus`: block IO, metadata, builders, validation
- `execution`: execution target models and workflow submission backends
- `storage`: identity payloads, deterministic layout, catalog, manifest persistence, inspection, sync
- `workflows`: acquire, tune, train, evaluate orchestration
