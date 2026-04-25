# Concrete Feature Families

Feature families turn canonical block rows into numeric columns for temporal models. A feature is a value known at a specific point in time. The family decides which information is allowed and how it is transformed.

## Mental Model

Raw blockchain rows are uneven and high-scale. Base fees can vary by orders of magnitude, gas usage has daily patterns, and recent trends matter more than isolated values. Features encode these signals as stable numeric inputs.

```text
canonical block rows
  -> feature family functions
  -> ordered feature columns
  -> float32 feature matrix
  -> model input windows
```

Feature contracts validate source columns, output ids, dependencies, row counts, and feature-set fingerprints.

## Beginner Theory: Base Fee, Gas, And Predictive Signals

Ethereum-style base fee is a protocol-set fee per gas unit. Under EIP-1559, the protocol adjusts the base fee according to how full recent blocks are compared with a target. High gas usage signals congestion, and congestion pushes future base fees upward. Low usage can push them down.

SPICE tries to learn when waiting a few blocks is economically useful. The feature families therefore emphasize:

| Signal | Why it can matter |
| --- | --- |
| Current base fee | Starting point for the decision. |
| Gas used and gas ratio | Proxy for demand pressure. |
| Recent fee deltas | Short-term momentum or reversal. |
| Rolling statistics | Smoothed context over noisy blocks. |
| Calendar time | Repeating demand patterns by hour or day. |

Feature engineering is the step where domain knowledge becomes numeric model input. The model does not know what "congestion" means unless the inputs expose useful measurements.

## Shared Helpers

All families use shared helper mechanics:

| Helper concept | Purpose |
| --- | --- |
| `log(base_fee_per_gas)` | Compresses large fee scales. Fees are clipped to at least `1` before logging. |
| `log1p(x)` | Stabilizes non-negative gas quantities while preserving zero. |
| `shift(lag)` | Uses values from earlier rows. |
| `delta` | Measures row-to-row change. |
| Rolling windows | Summarize recent history by mean, std, min, or slope. |
| Calendar sin/cos | Encodes cyclic time without discontinuity at midnight or week boundary. |

Rolling block windows use fixed row counts. Timestamp windows use elapsed seconds and `searchsorted`.

### Why Log Transforms

Fees and gas quantities are positive and can be heavy-tailed. A raw fee jump from `10` to `20` has the same absolute size as `100` to `110`, but economically the first is a doubling and the second is a 10% increase. Logs make multiplicative changes more additive:

```text
log(20) - log(10)  = log(2)
log(110) - log(100) = log(1.1)
```

That gives the model a scale where relative changes are easier to learn.

### Why Cyclic Time Uses Sine And Cosine

Hour `23` and hour `0` are adjacent in real time, but numerically they look far apart if encoded as plain integers. Sine and cosine place cyclic values on a circle:

```text
hour -> sin(2*pi*hour/24), cos(2*pi*hour/24)
```

The pair keeps midnight close to 23:00 and 01:00.

### Why Rolling Windows

One block can be noisy. Rolling windows summarize recent history:

```text
last 10 rows  -> local short-term signal
last 50 rows  -> medium context
last 200 rows -> broader regime
```

Timestamp windows ask the same question in seconds instead of row counts, which matters when block intervals vary.

## `same_block_closed`

`same_block_closed` assumes the current block is closed and its full block data is known. It can use current-row gas usage, gas limit, base fee, timestamp, and derived statistics.

Main feature groups:

| Group | Examples | Why it exists |
| --- | --- | --- |
| Fee level | log base fee | The target fee scale itself. |
| Gas pressure | gas used, gas limit, gas ratio | Congestion affects future base fees. |
| Time | hour/day sin/cos, elapsed time | Demand can have daily or weekly cycles. |
| Local change | fee deltas, gas deltas | Recent movement helps predict near-future movement. |
| Rolling stats | 10/50/200 row means, std, min | Smooths noisy row-level values. |
| Lags | lag1..lag6 | Gives the model explicit recent memory. |

This family is information-rich. It is useful when the decision point is after observing the current closed block.

## `block_open_lagged`

`block_open_lagged` models a stricter timing surface. It keeps the current `log_base_fee_per_gas`, because that value is known at block opening, but lags gas, gas ratio, calendar, elapsed-time, and rolling features by one row.

```text
row t base fee       -> allowed
row t gas usage      -> not used directly
row t-1 gas usage    -> allowed
```

This controls leakage: a model should not see values that would only be known after the decision point.

The family has fewer outputs than `same_block_closed`. Rolling gas-ratio windows account for the extra lag row, so a 200-row rolling feature needs 200 rows of warmup plus the one-row timing offset.

## `timestamp_features`

`timestamp_features` uses elapsed time instead of fixed block counts. It is useful when block intervals vary and a "last 300 seconds" summary is more meaningful than "last 25 blocks".

Feature groups:

| Group | Examples |
| --- | --- |
| Local time gaps | seconds since previous block |
| Elapsed timeline | seconds since start |
| Calendar cycles | hour/day/week sin/cos |
| Time rolling windows | 60s, 300s, 600s mean/std |
| Trend | centered slope over 600s |

Time windows scan timestamp arrays to find each row's history window. That makes the feature depend on elapsed wall-clock time rather than row count.

## Warmup And Missing Values

Rolling windows, lags, and deltas need past rows. Early rows can have missing values until enough history exists. Feature contracts expose prerequisites so temporal problem compilers and corpus coverage checks can demand enough history before the first usable sample.

```text
raw rows:     0  1  2  3 ... 199 200
rolling 200:  -  -  -  - ...  ok  ok
usable rows start after warmup
```

## Current Feature-Set Presets

Presets select concrete output lists from the families:

| Suffix | Meaning |
| --- | --- |
| `full` | Broad feature set for the family. |
| `no_time` | Removes explicit time/calendar fields. |
| `no_time_since_start` | Keeps most fields but removes elapsed-time trend. |
| `calendar_only_time` | Keeps cyclic calendar features as the time signal. |
| `time_since_start_only` | Keeps elapsed-time style signal. |
| `standard` or `baseline` | Compact baseline set. |

## Invariants

| Rule | Enforced by |
| --- | --- |
| Feature ids are unique and known. | Feature contract compilation. |
| Required source columns exist. | Feature execution. |
| Dependencies have no cycles. | Topological resolver. |
| Feature vector length equals row count. | Feature execution. |
| Rolling/time windows use positive sizes. | Helper validation. |

## Extension Pattern

A new family should define feature specs, source columns, prerequisites, and output functions in its own module. Keep leakage policy explicit: state what is known at the decision point, then encode only those values.

## Theory References

- EIP-1559 base-fee mechanism: https://eips.ethereum.org/EIPS/eip-1559
- Ethereum gas and fees overview: https://ethereum.org/en/developers/docs/gas/
