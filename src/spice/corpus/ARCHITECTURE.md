# Corpus Architecture

## Purpose

`corpus` owns canonical block data and coverage checks. It is the boundary between raw acquisition output and downstream ML feature construction.

## Corpus Identity

Corpus identity is durable data identity:

```text
chain + dataset name + evaluation date -> corpus id
```

It does not include model, prediction, objective, evaluator, or artifact settings. It also does not include the incidental acquisition request window. Acquisition windows are provenance for a run; corpus identity is the named canonical dataset context.

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

Corpus code should not know about model families, evaluator engines, objectives, or artifact variants. Workflows coordinate corpus coverage with feature and temporal contracts.
