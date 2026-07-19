# One FABLE (Fee Analysis through Blockchain Learning and Estimation) Decision, End to End

FABLE makes a decision immediately after a closed parent block `h`. Every number in this hand-computable Ethereum example is a fabricated teaching value.

## 1. Fix the geometry

Suppose:

```text
h = 25,400,000
C = 200 closed context blocks
K = 5 future outcome blocks
```

The model may see exactly blocks `h-C+1 … h`, or `25,399,801 … 25,400,000`. The complete outcome is `h+1 … h+K`. Actions are zero-based:

| Action `k` | Intended target block |
| ---: | ---: |
| 0 | 25,400,001 |
| 1 | 25,400,002 |
| 2 | 25,400,003 |
| 3 | 25,400,004 |
| 4 | 25,400,005 |

The arithmetic is always `target_block = h + 1 + k`.

## 2. Build only closed-parent inputs

For this calculation only, let the request's ordered feature tuple contain three supported features. Suppose closed parent `h` has:

```text
base_fee_per_gas = 24,000,000,000 wei/gas
gas_used         = 27,000,000 gas
gas_limit        = 36,000,000 gas
```

The raw closed-row features are:

```text
log_base_fee_per_gas = ln(24,000,000,000 / (1 wei/gas))
                     = 23.901320

gas_utilization = 27,000,000 / 36,000,000
                = 0.75
```

Ethereum's forming-child fee follows the exact parent recurrence. The parent target is `36,000,000 // 2 = 18,000,000 gas`. Usage exceeds target by `9,000,000`, so ordered integer arithmetic gives:

```text
increase = 24,000,000,000 * 9,000,000 // 18,000,000 // 8
         = 1,500,000,000 wei/gas

forming_child_base_fee = 25,500,000,000 wei/gas

log_exact_forming_base_fee_per_gas
  = ln(25,500,000,000 / (1 wei/gas))
  = 23.961944
```

All feature inputs come from block `h` or earlier. The exact child fee is an Ethereum parent-state result. The other 199 rows are prepared the same way from their own closed facts.

Training-only Float64 means and population standard deviations standardize the ordered raw matrix. The one-origin input is finite float32 `[C,F] = [200,3]`; a live batch is `[1,200,3]`.

## 3. Keep outcomes on the other side of the origin

Invent these complete future base fees:

```text
h+1 ... h+5 = [25.5, 23, 21, 20, 22] gwei/gas
```

They are stored and compared as positive Int64 wei/gas:

```text
[25_500_000_000, 23_000_000_000, 21_000_000_000,
 20_000_000_000, 22_000_000_000]
```

NumPy first-index `argmin` gives label `k*=3` and raw minimum
`O=20,000,000,000 wei/gas`. A tie would select the earliest equal minimum.

The dataset item is:

| Value | Shape and dtype |
| --- | --- |
| `inputs` | `[200,3]`, float32 |
| `label` | scalar, int64 |
| `target` | scalar, float32 |
| `base_fees` | `[5]`, int64 |
| `origin_block` | scalar, int64 |

The raw minimum first enters Float64 natural-log coordinates:

```text
ell = ln(20,000,000,000 / (1 wei/gas)) = 23.718998
```

For a purely illustrative fitted `TargetState(mean=23.5, standard_deviation=0.25)`:

```text
z = (23.718998 - 23.5) / 0.25 = 0.875992
```

Real state is fitted once from all retained training-origin minima with Float64 `ddof=0`. Validation, testing, and live inference use the persisted state.

## 4. Separate the roles

Every retained origin must have its complete `K`-block outcome inside its role. If validation begins at parent block `V`, a training origin is eligible only when `h+K < V`. Testing starts only after `validation_last_parent + K`.

Training fits feature state, target state, optional class support, and weights. Validation selects epochs and retained candidate objectives. Testing produces the final report.

## 5. Compute one two-head loss

For one origin, suppose the model returns:

```text
action_logits = [0.2, 1.1, -0.1, 1.7, 0.5]
minimum_fee_z = 0.7
```

For the arithmetic, let the request supply:

```text
classification_weighting = unweighted
classification_scale     = 1.0
regression_threshold     = 1.0
regression_scale         = 0.5
```

Another request may supply corrected inverse-frequency classification and other positive or nonnegative values.

With label `3`, cross-entropy is:

```text
CE = log(sum(exp(action_logits))) - action_logits[3]
   = log(exp(0.2)+exp(1.1)+exp(-0.1)+exp(1.7)+exp(0.5)) - 1.7
   ≈ 0.805777

c = 1.0 * CE ≈ 0.805777
```

The z error is `e = 0.7 - 0.875992 = -0.175992`. Because `|e| < beta=1`:

```text
SmoothL1(e) = 0.5 * e^2 / beta ≈ 0.015487
r           = 0.5 * SmoothL1(e) ≈ 0.007743
t           = c + r ≈ 0.813520
```

For this one-origin batch, `mean_total = sum(t_i)/B = t`. In a larger batch every origin contributes one scaled classification term plus one scaled regression term, with sample count `B` as the denominator.

## 6. Decode and account

Native first-index `argmax` selects `k=3`; equal maximum logits would choose the first. The intended target is block `25,400,004`.

For this outcome:

```text
B = immediate h+1 fee       = 25.5 gwei/gas
R = selected h+1+k fee      = 20.0 gwei/gas
O = hindsight minimum fee   = 20.0 gwei/gas

S = B - R = 5.5
G = B - O = 5.5
Q = R - O = 0.0
S + Q = G
```

This origin saves base fee per gas versus immediate action and captures all available hindsight opportunity. Across a declared evaluation window, FABLE first sums raw Int64 `S`, `G`, and `Q`, then forms Float64 ratio-of-sums.

The canonical observation also records `selected_action_wait_seconds = timestamp(h+3)-timestamp(h)` and `full_horizon_elapsed_seconds = timestamp(h+5)-timestamp(h)`. The selected wait is zero for `k=0`.

## 7. Carry the same contract into serving

The checkpoint fixes chain association, `C`, `K`, ordered features, feature state, target state, model definition, and weights. Live serving freezes the latest closed head, fetches exactly `C-1` predecessors, creates `[1,C,F]`, validates both output heads, and decodes the same way.

Continuing the teaching values, the API response shape is:

```json
{"head_block": 25400000, "selected_action_k": 3, "target_block": 25400004}
```

Next, read the [theory](theory.md) for the complete equations and claim boundaries, the [architecture](../ARCHITECTURE.md) for system ownership, and the [reference](reference.md) for exact schemas and commands.
