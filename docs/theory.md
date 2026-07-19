# FABLE (Fee Analysis through Blockchain Learning and Estimation) Theory

FABLE is a closed-parent, fixed-block-horizon temporal learning system. This document owns the causal information set, `C/K/k` geometry, fitted-state rules, feature and target equations, evaluation estimands, claim boundaries, sources, and limitations.

## Lineage and ownership

The manuscript *SPICE: A Predictive Framework for Cost-Optimization in Multichain Environments* describes a broader spatial, temporal, and distributed-reputation system. Its temporal experiment motivates a future minimum-block decision, an associated scalar fee prediction, the LSTM/Transformer/Transformer-LSTM comparison, chronological roles, and a weighted cross-entropy plus Smooth-L1 lineage.

FABLE specifies the current closed-parent origins, fixed block-count geometry, causal features, raw-integer target ties, training-fitted state, request-authored loss, exhaustive equal-origin evaluation, durable objects, and serving semantics.

## Closed-parent causality

A decision origin occurs immediately after block `h` closes. Facts in blocks through `h` may be inputs. Facts from `h+1` onward are outcomes and cannot influence features or fitted state available at that origin.

For context length `C` and horizon `K`:

```text
context rows:  h-C+1, ..., h
outcome rows:  h+1,   ..., h+K
actions:       k in {0, ..., K-1}
target block:  b = h+1+k
```

Block number owns geometry. Timestamp spacing may vary while the number of context and outcome rows stays fixed.

An origin is eligible only with all `C` context rows and all `K` outcome rows. At a boundary where the next role begins at parent `B`, an earlier origin must satisfy `h+K < B`. Therefore no training outcome reaches validation, and no validation outcome reaches testing.

## Role ownership and fitted populations

Training alone may fit:

- feature population means and standard deviations;
- target natural-log mean and standard deviation;
- class support for corrected inverse-frequency loss;
- neural weights.

Validation selects the earliest best epoch and supplies candidate objectives. Testing reports only. Changing a method, feature route, loss choice, horizon, context, or other scientific decision after inspecting testing would turn that evidence into selection evidence.

### Feature state

Let raw training-support feature row `x_r ∈ R^F`. For each ordered feature `j`:

```text
mu_j    = (1/N) sum_r x_rj
sigma_j = sqrt((1/N) sum_r (x_rj - mu_j)^2)
z_rj    = (x_rj - mu_j) / sigma_j
```

Fitting uses Float64 and `ddof=0`; every `sigma_j` must be positive. Transformation returns finite float32. Training support contains each closed block row once, so overlapping model windows do not reweight feature-state fitting.

## Causal features

The request supplies a nonempty unique ordered tuple drawn from the supported names, making feature choice request-authored.

| Feature | Raw equation and unit | Domain and availability |
| --- | --- | --- |
| `log_base_fee_per_gas` | `ln(base_fee_per_gas / (1 wei/gas))` | Fee positive; closed-row header fact. |
| `gas_utilization` | `gas_used / gas_limit` | `gas_limit>0`, `0≤gas_used≤gas_limit`; known after row close. |
| `log_exact_forming_base_fee_per_gas` | `ln(exact_child_base_fee / (1 wei/gas))` | Positive; Ethereum-only parent-state recurrence. |
| `log_gas_limit` | `ln(gas_limit / (1 gas))` | Gas limit positive; closed-row header fact. |
| `log1p_tx_count` | `ln(1 + tx_count / (1 transaction))` | Transaction count nonnegative; known after row close. |
| `hour_sin` | `sin(2π hour_UTC/24)` | `hour_UTC = (timestamp//3600) mod 24`; closed timestamp. |
| `hour_cos` | `cos(2π hour_UTC/24)` | Same angle and availability. |

The exact forming-fee column implements the Ethereum parent-known recurrence. Polygon and Avalanche requests use the other supported features.

### Ethereum forming-child recurrence

For positive parent fee `f`, parent gas used `u`, and positive gas limit `L`, use Python integers throughout:

```text
t = L // 2

if u == t:
    f_child = f
elif u > t:
    f_child = f + max(f * (u - t) // t // 8, 1)
else:
    f_child = f - f * (t - u) // t // 8
```

`t` and the final child fee must be positive. Python integers carry the recurrence through the two ordered divisions; the one-wei floor applies only upward. The completed positive integer is then logged in Float64. This follows the integer ordering in [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559#specification).

## Historical tensors and targets

One lazy historical item has:

| Value | Shape | Dtype | Meaning |
| --- | --- | --- | --- |
| `inputs` | `[C,F]` | float32 | Standardized closed rows `h-C+1 … h`. |
| `label` | scalar | int64 | Earliest horizon minimum action. |
| `target` | scalar | float32 | Standardized log horizon minimum. |
| `base_fees` | `[K]` | int64 | Positive fees at `h+1 … h+K`. |
| `origin_block` | scalar | int64 | Closed parent `h`. |

Collation produces `[B,C,F]`, `[B]`, `[B]`, `[B,K]`, and `[B]`.

Let the positive Int64 outcomes be `y_i0 … y_i,K-1`. Then:

```text
k_i* = first argmin_k y_ik
o_i  = y_i,k_i*
ell_i = ln(o_i / (1 wei/gas))
```

Raw integer comparison precedes floating conversion. Equal minima choose the first index, consistent with [NumPy `argmin`](https://numpy.org/doc/stable/reference/generated/numpy.argmin.html).

Target state is fitted over retained training origins only:

```text
mu_o    = mean_Float64(ell_i)
sigma_o = std_Float64(ell_i, ddof=0)
z_i     = Float32((ell_i - mu_o) / sigma_o)
```

`sigma_o` must be positive, and standardization follows the equation above exactly.

## Targets, loss, and decode

All concrete model definitions return:

```text
action_logits: [B,K]
minimum_fee_z: [B]
```

The first head scores actions. The second predicts the standardized natural log of the same horizon minimum.

### Classification

The request chooses `cross_entropy` and either unweighted or corrected inverse-frequency classification. For corrected weighting, training support for every class must be positive. With `N_train` labels, `K` actions, and support `n_k`:

```text
w_k = N_train / (K n_k)
```

For origin `i`, letting `a_i` be its logits and `k_i*` its label:

```text
c_i = classification_scale * CE(a_i, k_i*; optional w)
```

The corrected form weights that origin's negative log probability by `w_k`. Classification scale is finite and nonnegative.

### Regression

The request chooses Smooth L1, a positive threshold `beta`, and a finite nonnegative regression scale. For `e_i = predicted_z_i - target_z_i`:

```text
smooth_l1_beta(e) = 0.5 e^2 / beta       if |e| < beta
                    |e| - 0.5 beta       otherwise

r_i = regression_scale * smooth_l1_beta(e_i)
```

### Total

```text
t_i = c_i + r_i
mean_total = (sum_i t_i) / B
```

The denominator is the number of origins in the batch. Evaluation reconstructs Smooth L1 from persisted float32 z values in Float32, with the artifact's threshold and regression scale; the persisted classification contribution already includes classification weighting and scale. The operative functions match PyTorch's [`cross_entropy`](https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.cross_entropy.html) and [`smooth_l1_loss`](https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.smooth_l1_loss.html).

Decode is native `argmax(action_logits, dim=-1)`. Equal maximum logits select the first index, and decode depends on the logits alone.

## Model concepts

FABLE uses a closed discriminated union of three concrete sequence models:

- LSTM recurrently summarizes the fixed context and uses its final state.
- Transformer projects each row, adds sinusoidal positions, applies self-attention, and uses the final encoded position.
- Transformer-LSTM applies the Transformer encoder, then recurrently summarizes the encoded sequence.

All three attach the same two MLP heads. Architecture capacity belongs to `ModelDefinition` or Method; target and loss meaning stays in `fable.min_block_fee`.

## Evaluation estimands

For each eligible origin, define raw Int64 fee-per-gas values:

```text
B_i = fee at immediate action k=0
R_i = fee at selected action k_i
O_i = minimum fee over the K-block horizon

S_i = B_i - R_i             savings
G_i = B_i - O_i             hindsight opportunity
Q_i = R_i - O_i             hindsight regret
```

`O_i≤B_i` and `O_i≤R_i`, so `G_i,Q_i≥0`; `S_i` is signed. Exact identity:

```text
S_i + Q_i = G_i
```

Differences are computed before Float64 casting. Over `N` equally weighted origins:

```text
savings ratio       = sum(S) / sum(B)
opportunity ratio   = sum(G) / sum(B)
regret ratio        = sum(Q) / sum(B)
captured opportunity = sum(S) / sum(G), only when exact sum(G) != 0
```

Captured opportunity is null iff exact raw-Int64 `sum(G)==0`. Every other S14 field is nonnull. Positive `B_i` and `O_i` make the per-origin views defined:

```text
mean_i(S_i / B_i)
mean_i(Q_i / O_i)
mean_i(G_i / O_i)
```

Their zero-denominator exclusion counts are therefore zero. A harmful action has `R_i>B_i`. Selected action counts have length `K` and sum to `N`.

Accuracy is the fraction `k_i=k_i*`. Macro-F1 averages over the union-active classes whose true support plus prediction count is positive; absent-from-both classes do not enter its denominator.

The canonical time descriptions are:

```text
selected_action_wait_seconds = timestamp(h+k) - timestamp(h)
full_horizon_elapsed_seconds = timestamp(h+K) - timestamp(h)
```

The first is zero at `k=0`.

## Derived evidence semantics

### Sealed testing report

For a testing request, let `T` be its first parent, `E` its last eligible parent, and `L` the Corpus endpoint. The candidate count is `L-T+1`; incomplete maximum-horizon exclusions are `L-E`; elapsed testing time is `timestamp(E)-timestamp(T)`. The sealed TSV is a derived view, not canonical state.

### Context-history sensitivity

A `C`-block context covers `C-1` timestamp intervals: `timestamp(h)-timestamp(h-C+1)`. Context-cell deltas are signed differences from the same-chain C200 cell. If either captured-opportunity value is null, its delta is null. The C200 rows alone carry the aligned final-K horizon and artifact-ID arrays; other rows encode empty arrays.

### K=5 fee conditions

The two descriptors are origin-known:

- closed-parent base fee per gas;
- signed one-block change `ln(fee_h / fee_h-1)`.

For sorted `N` descriptor values, inverse-CDF cutpoint indices are:

```text
ceil(N/4)-1, ceil(N/2)-1, ceil(3N/4)-1
```

Cells use `≤q25`, `(q25,q50]`, `(q50,q75]`, and `>q75`. Ties never split. Duplicate cutpoints and resulting empty cells remain. Empty cells encode zero counts and sums, but null medians, ratios, and accuracy.

Each cell computes raw Int64 `B/R/O` and then `S/G/Q` before Float64 casting. Counts and correct classifications must recombine exactly. Independently regrouped floating totals use:

```text
u = 2^-53
gamma = ((N+3)u) / (1-(N+3)u)
abs(C_X - S14_X) <= 3 gamma A_X
```

where `A_X` is the full sum of absolute raw contributions. If `A_X=0`, both compared totals must be exactly zero.

## HPO interpretation

A `TuneRequest` freezes the experiment and one finite typed MethodSpace. An operator submits complete Methods from that set. Each successful fit contributes validation total loss, earliest best epoch, and completed epochs in retention order. Selected training names an exact result index.

## Claim boundary and limitations

Evaluation describes target block base fee per gas over every eligible origin in one declared historical window. Its claims are bounded as follows:

- Base fee per gas omits priority fee and transaction gas use.
- Target-block intent does not guarantee inclusion at that block.
- The auxiliary head is not calibrated uncertainty or a quote.
- One seed or one time range does not establish seed, regime, or future robustness.
- Different `K` values are different classification problems; testing cannot choose a best `K`.
- Native assets, fee levels, protocol rules, and ranges differ by chain; totals are never pooled across chains.
- Exhaustive origins remove sampling within the declared range, not temporal dependence or selection bias outside it.

## Sources

- [EIP-1559 specification](https://eips.ethereum.org/EIPS/eip-1559)
- [Reference temporal-model repository at the frozen commit](https://github.com/UniBO-PRISMLab/ICDCS-Model-Training/tree/bcf80b92877941e3b05a7dc5138560ffe41df27e)
- [Hochreiter and Schmidhuber, “Long Short-Term Memory”](https://direct.mit.edu/neco/article/9/8/1735/6109/Long-Short-Term-Memory)
- [Vaswani et al., “Attention Is All You Need”](https://arxiv.org/abs/1706.03762)
- [Caruana, “Multitask Learning”](https://doi.org/10.1023/A:1007379606734)
- [NumPy `argmin`](https://numpy.org/doc/stable/reference/generated/numpy.argmin.html)
- [PyTorch cross entropy](https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.cross_entropy.html)
- [PyTorch Smooth L1](https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.smooth_l1_loss.html)
