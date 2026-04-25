# Concrete Evaluators

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

Current evaluators accept `DecodedOffsets`. They interpret offsets through temporal rows and, usually, the realization policy.

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

Ratios are computed on real fee values, not log values.

## Replay Evaluator

The replay engine realizes selected offsets for historical samples and compares realized fee to baseline and optimum.

```text
sample positions
  -> decoded offsets
  -> realization policy
  -> realized rows
  -> fee ratios
```

Run metrics include:

| Metric | Formula idea |
| --- | --- |
| `profit_over_baseline` | `(baseline - realized) / baseline` |
| `cost_over_optimum` | `(realized - optimum) / optimum` |
| `baseline_cost_over_optimum` | `(baseline - optimum) / optimum` |
| Fee sums | Realized, baseline, optimum totals. |

### Fullset Sampler

`fullset` evaluates every selected sample once. It is deterministic and direct.

### Poisson Arrivals Sampler

`poisson_arrivals` simulates randomly timed transaction opportunities. Each repetition picks a uniform replay window, samples exponential inter-arrival times, maps each arrival to the latest sample at or before that timestamp, and evaluates those selected samples.

Duplicate selected samples can occur when several arrivals map to the same sample. They count as repeated events.

## Replay Aggregations

`event_mean` computes ratios per event, then averages. This answers: "How much did a typical event improve?"

`total_ratio` sums fees first, then computes ratios. This answers: "How much did total paid fee improve?"

```text
event_mean:  mean((baseline_i - realized_i) / baseline_i)
total_ratio: (sum(baseline) - sum(realized)) / sum(baseline)
```

## Zero-Stop Rollout

`zero_stop_rollout` repeatedly applies decoded offsets as a stop policy. It requires current-row candidate windows where anchor rows equal baseline rows.

```text
start at anchor row
while inside candidate window:
    if decoded offset for current row == 0:
        stop at current row
    else:
        advance one row
```

If no zero appears before the effective terminal row, the rollout realizes the terminal row. Metrics include replay-like fee ratios plus `mean_steps_to_stop`, `zero_stop_rate`, and `terminal_without_zero_count`.

## Anchor-Basefee Evaluator

`anchor_basefee` realizes every decoded offset through the realization policy, then compares realized fee against the anchor-row base fee.

Primary metric:

```text
fee_delta_over_anchor = (anchor_total - realized_total) / anchor_total
```

Diagnostics include realized fee sum, anchor fee sum, overflow count, and zero-action rate.

## Objective Link

Evaluation objectives call evaluator scoring on validation samples during training and tuning. Standalone evaluate workflow compiles the selected evaluation config and stores its summary under the artifact state DB.

## Failure Modes

| Failure | Meaning |
| --- | --- |
| Missing `engine` | Registry cannot choose evaluator. |
| Decoded-result id mismatch | Evaluator cannot interpret prediction output. |
| Empty selected positions | No events to score. |
| Non-positive fee total | Economic ratio denominator invalid. |
| Poisson window too long | Not enough timestamp coverage. |
| Zero-stop non-current-row store | Rollout rule does not match problem geometry. |
| Multiple stored summaries without id | Artifact state has several evaluation runs. |

## Extension Pattern

A new evaluator should declare its accepted decoded-result id, metric descriptors, primary metric, and direction. It should treat sample indices as positions into the problem store samples, not block row numbers.

