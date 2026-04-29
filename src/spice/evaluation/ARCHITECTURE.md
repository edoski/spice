# Evaluation Architecture

## Purpose

`evaluation` scores decoded predictions against temporal problem stores. It owns evaluator config validation, evaluator contracts, metric descriptors, Poisson replay sampling, private replay fee accounting, and decoded-result checks.

Training metrics answer “did the model optimize its objective?” Evaluation metrics answer “were the decoded decisions good under the temporal problem?” These are related but not identical.

## Config And Registry Pattern

There is one concrete evaluator spec:

```yaml
id: poisson_replay_2h
window_seconds: 7200
repetitions: 50
arrival_rate_per_second: 0.05
seed: 2026
```

```text
mapping / EvaluatorConfig
        |
        v
coerce_evaluator_config()
  - validate PoissonReplayEvaluatorConfig
        |
        v
compile_evaluator_contract()
  - require PoissonReplayEvaluatorConfig
  - compile Poisson replay contract
```

There is no evaluator engine registry while `poisson_replay_2h` is the only trusted economic evaluator.

## Scoring Flow

```text
model outputs
    |
    v
prediction contract decodes result
    |
    v
decoded result id
    |
    +--> evaluator contract checks accepted decoded-result id
             |
             v
        evaluator.run(store, execution_policy, decoded_result, sample_indices)
             |
             v
        EvaluationSummary
```

Evaluators never call models or prediction heads. The modeling scoring service performs inference and passes decoded results to evaluator contracts.

## Replay Offset Boundary

The evaluator accepts the generic `DecodedPredictionResult` from `prediction.decoding` at the evaluator entrypoint because that is the evaluator ABI. Replay then narrows to `DecodedOffsets` from `prediction.decoded_offsets` once:

```text
run_poisson_replay
  generic decoded result -> require_decoded_offsets()
  DecodedOffsets -> replay_summary.summarize_selected_costs()
```

`replay_summary` is replay-private and accepts `DecodedOffsets` directly. That keeps generic decoded-result handling at the evaluator boundary.

## Metric Descriptor Rule

```text
metric id -> label -> role(primary | secondary | diagnostic)
```

Each evaluator contract must declare exactly one primary metric. Descriptor ids must be unique and path-safe. The primary metric drives objective alignment and reporting; secondary and diagnostic metrics explain behavior.

## Module Map

```text
evaluation/
  config.py          evaluator config models
  contracts.py       compiled evaluator contract and summary models
  registry.py        public config coercion and contract compile helpers
  metrics.py         metric descriptor definitions
  sampling.py        Poisson arrival and chronological sample helpers
  replay.py          Poisson replay evaluator entrypoint
  replay_summary.py  replay-private fee accounting and run accumulation
  summary.py         generic summary helpers
```

## Extension Points

Add a public fee-accounting or evaluator-engine seam only when a second trusted evaluator exists. Workflows should keep calling `compile_evaluator_contract()`.
