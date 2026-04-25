# Evaluation Architecture

## Purpose

`evaluation` scores decoded predictions against temporal problem stores. It owns evaluator configs, engine dispatch, metric descriptors, summary shapes, sampling, replay/window mechanics, and accepted decoded-result checks.

Training metrics answer “did the model optimize its objective?” Evaluation metrics answer “were the decoded decisions good under the temporal problem?” These are related but not identical.

## Config And Registry Pattern

Evaluator configs separate reusable config identity from implementation selection:

```yaml
id: poisson_replay_2h_mean
engine: replay
```

```text
mapping / EvaluatorConfig
        |
        v
coerce_evaluator_config()
  - require evaluation.engine
  - lookup local evaluator spec
  - validate concrete config type
        |
        v
compile_evaluator_contract()
  - lookup same engine spec
  - require concrete config object
  - call concrete compiler directly
```

Evaluator engines are explicit string selectors owned by the local evaluation registry. The registry dispatches from the `engine` field to the concrete config and compiler. Config coercion performs validation before compile-time dispatch.

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
        evaluator.run(store, realization_policy, decoded_result, sample_indices)
             |
             v
        EvaluationSummary
```

Evaluators never call models or prediction heads. The modeling scoring service performs inference and passes decoded results to evaluator contracts.

## Replay Offset Boundary

Replay evaluators accept the generic `DecodedPredictionResult` at the evaluator entrypoint because that is the evaluator ABI. Replay then narrows to `DecodedOffsets` once:

```text
run_fullset / run_poisson_arrivals
  generic decoded result -> require_decoded_offsets()
  DecodedOffsets -> replay_summary.summarize_selected_costs()
```

`replay_summary` is replay-specific and accepts `DecodedOffsets` directly. That keeps generic decoded-result handling at the evaluator boundary.

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
  registry.py        local engine dispatch
  metrics.py         metric descriptor definitions
  sampling.py        sample/window selection helpers
  windows.py         evaluator candidate-window helper
  aggregation.py     replay aggregation rules
  replay.py          replay evaluator entrypoints
  replay_summary.py  replay-private run accumulation
  zero_stop_rollout.py
  anchor_basefee.py
  summary.py         generic summary helpers
```

## Extension Points

Add a new evaluator engine when scoring mechanics change. Add a new named evaluation YAML when reusable settings change but the scoring engine is the same. Do not put evaluator-engine branches in workflows.
