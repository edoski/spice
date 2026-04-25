# Concrete Objectives

Objectives define what training and tuning optimize. They are not model losses by themselves; they select a metric and a direction.

## Mental Model

Training always computes prediction metrics. An objective decides which metric controls best checkpoint and early stopping.

```text
validation batches
  -> prediction metrics
  -> optional evaluation scoring
  -> objective metric
  -> checkpoint decision
```

## Validation Objective

`id: validation` uses validation metrics directly. Current checked-in preset `validation_total_loss` minimizes `total_loss`.

This is the simplest objective: it optimizes the same metric produced by the prediction family during validation.

## Evaluation Objective

`id: evaluation` runs an evaluator on validation samples and optimizes an evaluator metric. Current checked-in presets maximize `profit_over_baseline` under Poisson replay benchmarks.

```text
validation samples
  -> predict offsets
  -> run evaluator
  -> select evaluator metric
```

This is slower than a validation-loss objective, but it aligns checkpoint selection with the economic metric used for research reporting.

## Direction

Each objective has a direction:

| Direction | Meaning |
| --- | --- |
| `minimize` | Smaller metric is better. |
| `maximize` | Larger metric is better. |

The direction controls early stopping, best checkpoint selection, and Optuna study optimization.

## Benchmark Binding

Evaluation objectives name a benchmark evaluator id. Train and tune configs must select the same evaluation benchmark. This keeps the optimized metric tied to the intended evaluator.

Evaluate workflow can run a selected diagnostic evaluator directly; artifact semantic validation still checks the trained configuration identity.

## Current Presets

| Preset | Mode | Metric | Direction |
| --- | --- | --- | --- |
| `validation_total_loss` | validation | `total_loss` | minimize |
| `profit_poisson_replay_2h_mean` | evaluation | `profit_over_baseline` | maximize |
| `profit_poisson_replay_2h_total` | evaluation | `profit_over_baseline` | maximize |

## Failure Modes

| Failure | Meaning |
| --- | --- |
| Metric id missing | Objective cannot find configured metric. |
| Evaluation objective without benchmark | Evaluator scoring target is undefined. |
| Benchmark mismatch | Training would optimize a different evaluator than requested. |
| Invalid direction | Best-metric comparison is undefined. |

## Extension Pattern

A new objective mode should still produce one metric id and direction. Keep objective selection separate from prediction family loss implementation.

