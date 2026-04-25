# Concrete Workflows

Workflows orchestrate complete user operations. They do not own model architectures, feature math, storage schema, or evaluator algorithms. They compile configs, validate prerequisites, call owner packages, and commit results.

## Workflow Map

```text
acquire  -> corpus root
train    -> artifact root
tune     -> study root
evaluate -> artifact evaluation state
```

Acquire runs locally. Train, tune, and evaluate can run locally or through remote execution.

## Acquire

Acquire downloads block data and writes a corpus root.

```text
resolve config
  -> compile feature/problem contracts
  -> estimate needed history
  -> download history
  -> count valid temporal samples
  -> optional one refill
  -> download evaluation day
  -> write dataset state
  -> partial commit corpus paths
```

The workflow adds a 10% cushion to initial history sizing. If compiled valid sample count is still short, it estimates observed seconds per block and refills once.

Dry run reports the plan without materializing data.

## Train

Train creates an artifact root.

```text
resolve config and identity
  -> apply best study params if tuned artifact
  -> validate corpus coverage
  -> stage artifact root
  -> train model
  -> write manifest/model/state
  -> promote artifact root
  -> reindex catalog
```

The artifact manifest stores exact configs and semantic fingerprints. Tuned train validates study identity before applying best params.

## Tune

Tune creates or resumes a study root.

```text
resolve study identity
  -> validate corpus coverage for tuned search space
  -> open Optuna study
  -> for each trial:
       sample params
       apply params
       train in trial dir
       report objective
  -> store best trial in study DB
```

Trial artifacts are not persisted as final artifacts. The study stores sampled params and best epoch metadata.

## Evaluate

Evaluate runs diagnostic scoring for an existing artifact.

```text
resolve artifact
  -> apply best study params if tuned
  -> load artifact manifest/model
  -> validate config semantics
  -> validate delay capability and corpus coverage
  -> prepare inference dataset
  -> score evaluator
  -> upsert evaluation state
```

Evaluate writes into the existing artifact state DB. It does not stage or replace the artifact root.

## Remote Submission Boundary

Workflow functions require resolved configs. CLI submission chooses the target and execution backend. Downstream workflow code receives explicit storage roots and does not choose remote targets.

## Failure Modes

| Workflow | Common failures |
| --- | --- |
| acquire | RPC retry exhaustion, insufficient valid samples after refill, invalid corpus validation. |
| train | Missing corpus coverage, CUDA unavailable, artifact destination conflict. |
| tune | Study identity mismatch, requested trial count below existing trial count, missing coverage for max tuned lookback. |
| evaluate | Artifact semantic mismatch, evaluation delay too large, missing corpus coverage. |

## Extension Pattern

A new workflow should orchestrate existing package contracts and commit one clear storage effect. Put reusable algorithms in owner packages, not workflow files.

