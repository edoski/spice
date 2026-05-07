# Corpus Architecture

## Purpose

`corpus` owns canonical block data and coverage checks. It is the boundary between raw acquisition output and downstream ML feature construction.

## Corpus Identity

Corpus identity is durable data identity:

```text
chain + dataset name + evaluation date -> corpus id
```

It does not include model, prediction, objective, evaluator, or artifact settings. It also does not include the incidental acquisition window. Acquisition windows are provenance for a run; corpus identity is the named canonical dataset context.

## Acquisition To Corpus Flow

```text
provider/RPC blocks
  |
  v
canonical block rows
  |
  v
history and evaluation parquet datasets
  |
  v
dataset manifest + acquire run record
  |
  v
corpus root state
```

External uncertainty enters through acquisition: provider failures, missing blocks, latency, and chain-specific payload details. Corpus validation resolves those concerns before feature construction starts.

## Corpus Assembly

Corpus Assembly owns acquisition-to-corpus orchestration. It builds a Corpus Capability Planning context, asks it for initial history/evaluation windows, delegates committed fulfillment to Corpus Acquisition Stage, and returns the committed corpus result.

Corpus Capability Planning owns feature/problem contract compilation for acquisition coverage, generic Corpus Acquisition Source Requirements, initial history sizing, valid temporal capability sample counting, and the bounded history refill lifecycle including attempt limits, status wording, and termination. It consumes `required_source_columns` and `acquisition_enrichments` from the compiled feature contract. Source requirements describe required source columns, optional enrichments, temporal unit, ordering key, and partition key. They are corpus-level requirements, not RPC configuration. Concrete acquisition adapters receive them and either bind them to provider behavior or fail before acquisition starts.

Corpus Acquisition Stage owns acquire staging paths, materialization session lifecycle, planning-step-to-split-intent adaptation, evaluation fulfillment, state DB staging, partial commit wiring, successful cleanup, and preserve-on-failure behavior. Corpus Split Materialization fulfills Split Intents and owns staged/committed candidate loading, target assessment, pull execution, chunk writing, source reuse, and validation of history/evaluation parquet datasets. Validation includes the active source requirements, so a dataset with null required source columns cannot be reused or promoted. Its public session interface stays small; private modules keep candidate loading, chunk IO, source reuse, acquisition pulls, invariant checks, and materializer control flow local. Extension paths reuse whole clean parquet chunks and materialize only missing or edge block ranges.

The dataset manifest is split-first. `history` and `evaluation` each record requested timestamps/blocks, observed coverage, validation status/issues, and materialization outcome. Coverage owns observed rows and ranges; validation owns cleanliness and issues. Downstream coverage checks read the split manifests directly instead of reconstructing corpus windows from flat manifest fields.

The acquire workflow supplies a Workflow Config, resolved paths, and a block source constructed with corpus-derived source requirements. It does not know feature-source policy, requirement-to-provider mapping, capability planning, split materialization, refill, staging, or publication ordering.

## Coverage Checks

Training and evaluation workflows ask corpus coverage whether the stored block windows satisfy the temporal problem and feature prerequisites.

```text
dataset manifest
  + feature prerequisites
  + temporal problem coverage requirement
  -> pass/fail before model work starts
```

This prevents expensive training or evaluation from running on a corpus that cannot support the requested examples.

## Boundaries

Corpus code should not know about model families, evaluator adapters, objectives, or artifact variants. Corpus Capability Planning may compile feature/problem contracts only to prove raw corpus coverage during acquisition.
