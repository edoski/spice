# Concrete Evaluator

Evaluators score decoded model decisions against historical fee data. They are separate from prediction losses: a model can train with one loss and still be evaluated with replay-style economic metrics.

## Mental Model

Evaluation starts after inference:

```text
model outputs
  -> prediction decode
  -> DecodedOffsets
  -> evaluator contract
  -> EvaluationSummary
```

The current evaluator accepts `DecodedOffsets`. It interprets offsets through temporal rows and the execution policy.

## Evaluation Contract

`CompiledEvaluatorContract` contains:

| Field | Meaning |
| --- | --- |
| `evaluation_id` | Stable evaluator config id. |
| `metric_descriptors` | Metric names, roles, and directions. |
| `primary_metric_id` | Metric used for headline reporting. |
| `accepted_decoded_result_id` | Decoded ABI the evaluator accepts. |
| `run_fn` | Concrete evaluation function. |

The contract validates metric descriptor uniqueness and decoded-result id before running.

## Fee Math

Problem stores keep fees in log space. Evaluators exponentiate before economic ratios:

```text
fee = exp(log_base_fee)
```

Ratios are computed on real fee values, not log values. Fee accounting is private to the Poisson replay evaluator while it is the only economic evaluator.

## Poisson Replay

`poisson_replay_2h` simulates randomly timed transaction opportunities. Each repetition picks a uniform replay window, samples exponential inter-arrival times, maps each arrival to the latest sample at or before that timestamp, realizes decoded offsets, and compares realized fee to baseline and optimum.

```text
arrivals
  -> sample positions
  -> decoded offsets
  -> execution policy
  -> realized rows
  -> event-mean fee ratios
```

Duplicate selected samples can occur when several arrivals map to the same sample. They count as repeated events.

Run metrics include:

| Metric | Formula idea |
| --- | --- |
| `profit_over_baseline` | Mean `(baseline - realized) / baseline` per event. |
| `cost_over_optimum` | Mean `(realized - optimum) / optimum` per event. |
| `baseline_cost_over_optimum` | Mean `(baseline - optimum) / optimum` per event. |
| Fee sums | Realized, baseline, optimum totals. |

## Objective Link

Evaluation objectives call evaluator scoring on validation samples during training and tuning. Standalone evaluate workflow compiles the selected evaluation config and stores its summary under the artifact state DB.

## Failure Modes

| Failure | Meaning |
| --- | --- |
| Unknown evaluation id | Only `poisson_replay_2h` is supported. |
| Decoded-result id mismatch | Evaluator cannot interpret prediction output. |
| Empty selected positions | No events to score. |
| Non-positive fee total | Economic ratio denominator invalid. |
| Poisson window too long | Not enough timestamp coverage. |
| Multiple stored summaries without id | Artifact state has several evaluation runs. |

## Extension Pattern

A future second evaluator should declare its accepted decoded-result id, metric descriptors, primary metric, and direction. Add shared fee-accounting only when that second evaluator needs it.
