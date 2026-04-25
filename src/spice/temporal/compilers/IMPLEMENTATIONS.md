# Concrete Temporal Problem Compilers

Temporal problem compilers turn feature rows into supervised decision examples. A problem defines which past rows the model may see, which future rows it may choose, and how many candidate actions exist.

## Mental Model

Each sample has three row regions:

```text
context rows              candidate rows
|------------------|      |-------------|
context_start      anchor candidate_start candidate window end
```

The context is model input. The candidate window is the action space. The anchor is the row that defines the decision time.

The compiled store uses arrays rather than per-sample objects:

```text
feature_matrix[row, feature]
log_base_fees[row]
timestamps[row]
anchor_rows[sample]
context_start_rows[sample]
candidate_start_rows[sample]
candidate window end row array[sample]   # exclusive
max_candidate_slots
```

## Candidate Offsets

Candidate offset `0` means the first selectable candidate row for that sample. The realization policy maps the selected offset to an actual row. Current action masks are all true for `max_candidate_slots`; overflow slots are meaningful under `strict_deadline_miss`.

```text
selected row = candidate_start_row + decoded_offset
if selected row is outside candidate window:
    use post-window row under strict deadline miss
```

## `timestamp_future_window`

This compiler defines future windows in elapsed seconds.

Config concepts:

| Field | Meaning |
| --- | --- |
| `lookback_seconds` | How much past time the model may see. |
| `max_delay_seconds` | Maximum allowed delay for action choices. |
| `sample_count` | Number of valid samples requested. |
| `action_interval_estimator` | Converts seconds to action slots. |

The compiler uses timestamps and `searchsorted` to build windows:

```text
context_start = first row with timestamp >= anchor_ts - lookback
candidate_end = first row with timestamp > anchor_ts + max_delay
```

It also sets the realization policy to require a post-window row, because overflow slots need a row just after the window.

## Action Interval Estimators

`nominal` uses the chain's configured nominal block time.

`recent_deltas` computes the median positive timestamp delta from recent rows. This adapts to observed block timing while rejecting zero or negative timestamp gaps.

The action count is:

```text
floor(max_delay_seconds / action_interval_seconds) + 1
```

The extra `+1` includes offset `0`.

## `estimated_block`

This compiler converts time horizons into row counts before building samples. It is useful when the experiment should act on estimated block steps instead of timestamp search windows.

Config concepts:

| Field | Meaning |
| --- | --- |
| `lookback_interval_source` | Interval used to convert lookback seconds to rows. |
| `candidate_interval_source` | Interval used to convert delay seconds to candidate count. |
| `calibrated_interval_statistic` | `median` or `mean` over positive timestamp deltas. |

Conversion:

```text
lookback_steps = round(lookback_seconds / lookback_interval)
candidate_count = floor(max_delay_seconds / candidate_interval) + 1
```

Candidate windows start at the anchor row. The delay store persists interval metadata so inference uses the same geometry as training.

## Shared Timestamp Window Builder

The shared builder filters samples with these rules:

| Rule | Why |
| --- | --- |
| Enough context history exists. | Inputs must satisfy lookback and feature warmup. |
| Candidate window is non-empty. | The model needs at least one fee choice. |
| Optional post-window row exists. | Overflow realization needs a concrete row. |
| Warmup rows are skipped. | Feature prerequisites must be satisfied. |

## Acquisition Sizing

Temporal contracts tell acquisition how much history is needed before the evaluation day. Acquisition uses that to download enough bootstrap history, then validates by actually compiling features and counting valid samples.

```text
problem required history
  + feature prerequisites
  + requested samples
  -> acquisition lookback plan
```

## Invariants

| Rule | Enforced by |
| --- | --- |
| Timestamps and arrays align by row. | Problem-store construction. |
| Candidate end is exclusive. | Compiler geometry. |
| `max_candidate_slots` matches prediction head width. | Artifact/prediction contracts. |
| Delay at evaluation is not greater than trained capability. | Workflow validation. |
| Runtime compiler metadata round-trips. | Dataset builder and artifact manifest. |

## Extension Pattern

A new compiler should produce the same `CompiledProblemStore` arrays and explicit runtime metadata. Keep row geometry inspectable; model code should not need compiler-specific branches.
