# Methodological estimands for temporal evaluation

Status: independent research input for [issue 48](https://github.com/edoski/spice/issues/48). This report defines consequences of candidate designs. It chooses no owner policy, metric tolerance, window, or numeric `K`.

## Fixed scope and notation

The approved [issue-46 contract](https://github.com/edoski/spice/issues/46#issuecomment-4948024446) fixes the decision origin at closed canonical parent `h`, fixes targets to `h+1...h+K`, defines `k=0` as immediate broadcast toward `h+1`, and makes equal `K` a block-opportunity contract. Target opportunity is neither transaction inclusion nor actual execution. Deadline miss is not a primary model outcome. The [issue-53 resolution](../fixed-block-comparability-and-exhaustive-replay.md) recommends exhaustive replay as the primary candidate and preserves Poisson replay only for an explicit request-arrival estimand; issue 48 still owns approval. The [issue-54 evidence](../modern-regime-coverage-and-evidence-periods.md) requires regime-contained eligibility and records whole-second duplicate Avalanche timestamps.

For one chain and one predeclared, regime-contained window `W`, let

```text
O_W = eligible origins h whose causal history through h and all targets h+1...h+K exist
n_W = |O_W|
Y_p,s(h) = a declared per-origin outcome for policy p and fitted training seed s
```

Every score needs a declared measure over `O_W`. “Average performance” alone does not identify an estimand.

## What each replay estimates

### Exhaustive eligible-origin replay

For a fixed fitted artifact, exhaustive replay gives the finite-window block-origin census

```text
mu_block(p, s, W) = (1 / n_W) * sum[h in O_W] Y_p,s(h).
```

Each eligible origin has weight `1/n_W` and appears once. The result is exact for this artifact, trace, eligibility rule, and window. It has no replay Monte Carlo error and no finite-population sampling error because no origin in `O_W` was sampled. It does not, by itself, estimate a random request, a random second, another regime, or a future deployment. Probability-sampling inference and purposive finite-population description are distinct designs in the foundational sampling treatment by [Neyman (1934)](https://doi.org/10.1111/j.2397-2335.1934.tb04184.x).

If several named windows are reported, two reducers answer different questions:

```text
pooled-origin mean = sum[j] sum[h in O_j] Y(h) / sum[j] n_j
equal-window mean  = (1 / J) * sum[j] ((1 / n_j) * sum[h in O_j] Y(h)).
```

The first weights windows by eligible-origin count. The second weights windows equally. They coincide only when counts match. Overlapping named windows either intentionally count an origin more than once or require deduplication; that rule must be declared.

### Homogeneous block-Poisson replay

For a fixed block window, model independent event counts as `C_h ~ Poisson(lambda)` per eligible origin. Conditional on total count `C_+=r>0`, `(C_h)` is multinomial with probabilities `1/n_W`. Therefore

```text
event mean = sum[h] C_h Y(h) / C_+
E[event mean | C_+=r] = mu_block.
```

For a linear per-request mean, block-Poisson replay is a noisy Monte Carlo estimator of the exhaustive block-origin mean. Duplicate selections represent multiple requests at one origin only if the thesis asserts such a workload. Otherwise they add simulation variance. `lambda` affects total requests, empty-run probability `exp(-lambda*n_W)`, workload totals, and the distribution of nonlinear finite ratios; it does not affect the conditional expected linear event mean.

### Homogeneous wall-clock Poisson replay

Let `I_h` be the wall-clock interval during which `h` is the latest available closed parent, and let `D_h` be its duration inside the evaluation window. Independent Poisson requests at rate `lambda` give `C_h ~ Poisson(lambda*D_h)`. Conditional on a positive total request count,

```text
E[event mean | C_+=r] = sum[h] D_h Y(h) / sum[h] D_h.
```

This is a wall-clock exposure estimand, not a block-origin estimand. Conditional arrival locations in a fixed interval are uniform order statistics, which gives the result directly ([MIT 6.262, Theorem 2.5.1](https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/resources/mit6_262s11_chap02/)). The broader PASTA result equates Poisson-arrival and time averages when the observed process cannot anticipate future Poisson arrivals ([Wolff 1982](https://doi.org/10.1287/opre.30.2.223)). A frozen-trace replay therefore supports only an exogenous, non-interacting request process. It cannot model requests changing fees, inclusion, queues, or congestion.

The rate again cancels from the conditional expected linear per-request mean. It remains material for counts, empty windows, workload totals, queues, and finite nonlinear ratios. A nonhomogeneous arrival claim instead weights `h` by `integral[I_h] lambda(t) dt`; homogeneous-Poisson results do not justify that claim.

This request-time design also needs actual parent-availability intervals. Block header timestamps are not observation times. Mapping a request to “latest available closed parent” must preserve its request timestamp and the canonical parent identity. Mapping it straight to a target row would violate issue 46.

## Named windows and the uniform-start inclusion kernel

A uniformly random window does not weight the enclosing corpus uniformly.

For `N` ordered eligible origins, a fixed window length `L`, and start `S` uniform on `1...M` where `M=N-L+1`, origin `i` is included in

```text
c_i = max(0, min(i, M) - max(1, i-L+1) + 1)
```

possible starts. The expectation of the within-window mean is

```text
E_S[(1/L) * sum[i=S..S+L-1] Y_i]
  = sum[i=1..N] (c_i / (M*L)) * Y_i.
```

For `N=5, L=3`, the inclusion counts are `(1, 2, 3, 2, 1)`, not `(1, 1, 1, 1, 1)`. Corpus edges are downweighted. Exhaustive whole-corpus block weighting is therefore not the exact expectation of uniform random starts. This formula assumes every start has exactly `L` eligible origins and the reducer divides by `L`; start-dependent exclusions or denominators require recomputing the weights.

The continuous-time form has the same boundary kernel. For corpus duration `T`, window duration `H<T`, and start uniform on `[0,T-H]`, define

```text
ell_H(t) = max(0, min(t, T-H) - max(0, t-H)).
```

Then

```text
E_S[(1/H) * integral[S..S+H] Y(t) dt]
  = integral[0..T] Y(t) * ell_H(t) / (H*(T-H)) dt.
```

For a piecewise-constant parent state, origin `h` receives weight proportional to `integral[I_h] ell_H(t) dt`, not merely `D_h/T`. Random-window Poisson replay combines this start kernel with block or time exposure. Pooling all simulated events, averaging per-run means, and averaging per-run ratios can then target different quantities, especially with empty runs. If starts are sampled from rows or integer timestamps instead of continuous time, use the actual discrete start support rather than this continuous kernel.

Predeclared named windows remove start randomness and its kernel. They change the estimand to the stated finite windows; they do not mathematically reproduce the old random-start estimator. Selection before outcome inspection is essential because outcome-guided windows define a selected-case estimand, not an external evaluation.

For SPICE, “broad” testing cannot mean only the old 300/1,200-block windows. On modern Avalanche those widths span minutes. The role vocabulary is training, validation, and testing only. Testing is one sealed, strictly later corpus role; it may contain multiple predeclared, non-overlapping, regime-contained reporting windows distributed across its calendar tail, with every eligible origin inside the primary test range scored exhaustively. Those windows are views inside one role, not extra dataset roles. Existing inspected tails can support validation, but a genuinely sealed clean-contract test likely requires a newly acquired contiguous suffix after issue 47, issue 48, numeric `K`, and all test views are frozen. Periods, counts, and calendar spans remain chain-specific; equalizing them would change the estimand.

The old 06/07 route selected 27 non-overlapping windows per fee/volatility quartile, producing 216 views per chain and 648 overall. That outcome-conditioned representative design cannot define the primary headline estimate. Exhaustive coverage of the predeclared test range remains primary. A predeclared fee/volatility stratification or old 300/1,200-block aggregation may survive only as a separately named secondary descriptive view if it answers a thesis question.

## Block weighting, wall-clock weighting, and duplicate timestamps

Block weighting answers: outcome for a uniformly selected eligible block decision origin. Wall-clock weighting answers: outcome for an exogenous request at a uniformly selected eligible instant, assuming valid availability intervals. Equal `K` normalizes only the former action geometry.

The issue-54 audit found whole-second timestamps and 70,493 adjacent same-second Avalanche blocks. Under the approved issue-47 corpus identity, the stable offline origin/pairing key is `(content_bound_corpus_id, chain_id, block_number)`, never timestamp alone. Live decisions separately retain `(h, hash(h))`; an offline physical-header parity case may retain a hash only when its selected evidence contract explicitly requires it. If a time sensitivity defines `I_h=[t_h,t_{h+1})` from header timestamps, tied timestamps give some origins zero exposure and assign the tied second according to an arbitrary right-continuous ordering rule. That is a declared quantization convention, not measured serving availability. Higher-resolution observation timestamps are required for an exact request-time claim.

Waiting also needs a named baseline:

```text
target_distance_blocks(h) = k_h + 1
extra_wait_blocks_vs_immediate(h) = k_h
target_timestamp_displacement(h) = t_(h+1+k_h) - t_h
extra_timestamp_wait_vs_immediate(h) = t_(h+1+k_h) - t_(h+1).
```

The two block quantities differ by one. The timestamp quantities can be zero under duplicate timestamps and are trace timestamp displacements, not observed service latency or inclusion delay.

## Ratios and their denominators

Let `B_h>0` be declared reference exposure at origin `h`, such as gas weight times the immediate target base fee, and let `C_h` be the same exposure construction under a candidate target. A gas-weighted savings ratio of sums is

```text
S_W = sum[h] (B_h - C_h) / sum[h] B_h
    = 1 - sum[h] C_h / sum[h] B_h.
```

It is dimensionless; multiply by 100 for percentage points. If `s_h=(B_h-C_h)/B_h`, then

```text
S_W = sum[h] B_h s_h / sum[h] B_h.
```

Thus it is a reference-exposure-weighted mean of per-origin relative savings. It is not the equal-origin mean base-fee difference, not the mean of per-origin percentages, not transaction inclusion, and not profit.

Three ratio meanings must stay separate:

```text
finite-window ratio:       R_W = sum[h in W] A_h / sum[h in W] B_h
ratio of expectations:     theta = E[A] / E[B]
expectation of a ratio:    rho = E[A / B].
```

`R_W` is an exact descriptive property of the observed finite window. Under the empirical uniform distribution on that same window, `E_W[A]/E_W[B]=R_W`; that identity is tautological and adds no future-process claim. For a future stochastic process, `theta` is a different parameter. In general `theta != rho`, and the expected value of a finite sample ratio need not equal `theta`.

A Poisson-sampled ratio of event totals converges toward the ratio under its block or time exposure measure when request count grows and regularity conditions hold. At finite request counts its expectation depends on count, denominator variability, and empty-run handling, so arrival rate need not cancel. Always publish numerator, denominator, origin/event count, and reducer beside the ratio.

Ratio inference becomes unstable when the denominator is noisy near zero; [Fieller's original treatment](https://doi.org/10.1111/j.2517-6161.1954.tb00159.x) shows why a bounded symmetric interval is not automatic. Here a positive, well-sized reference total can make that concern remote, but it must be demonstrated rather than inferred from a large origin count. For a ratio-of-expectations claim, one dependence-aware route uses paired vectors `(A_h,B_h)` and the influence quantity

```text
psi_h(theta) = (A_h - theta*B_h) / E[B].
```

Estimate its long-run variance with a time-series method, or block-bootstrap `(A_h,B_h)` jointly and recompute the ratio. An IID bootstrap of individual origins breaks temporal dependence.

When competing policies share the same reference denominator and common origin set, their savings-ratio difference reduces to one paired numerator difference over that common denominator. Changing eligible sets or denominators confounds policy performance with coverage.

## Dependence, pairing, and valid uncertainty labels

Adjacent origins are mechanically dependent. Origin `h` uses outcomes `h+1...h+K`; origin `h+1` uses `h+2...h+K+1`, so full-horizon metrics share `K-1` target rows. Fee dynamics can extend dependence beyond `K-1`.

Compare policies on a common eligible set with the paired differential

```text
d_h = L_A(h) - L_B(h).
```

The pairing key is the same content-bound corpus, chain, parent block number, window, targets, and fitted-seed estimand. Baselines and feasible oracles remain paired to the same origin. The relevant variance for a process-mean claim is the long-run variance

```text
Omega = gamma_0 + 2 * sum[l>=1] gamma_l,
SE(mean(d)) = sqrt(Omega / n).
```

[Diebold and Mariano (1995)](https://doi.org/10.1080/07350015.1995.10524599) formulate forecast comparison through a loss differential and allow serial and contemporaneous correlation. A positive-semidefinite HAC estimator is available under general conditions from [Newey and West (1987)](https://doi.org/10.2307/1913610). SPICE should not hard-code lag `K-1` as sufficient: horizon overlap guarantees short-lag dependence but fee autocorrelation can last longer. Any HAC bandwidth rule belongs in the predeclared analysis. Diebold later stressed that the DM test compares forecasts, not universal model truth; pseudo-out-of-sample evidence supports comparative historical performance ([Diebold 2012](https://doi.org/10.3386/w18391)).

A block bootstrap is an alternative only under a defensible weak-dependence/stationarity claim. The stationary bootstrap was designed for confidence regions from weakly dependent stationary observations ([Politis and Romano 1994](https://doi.org/10.1080/01621459.1994.10476870)). Resample contiguous vectors containing both policies and all ratio components; predeclare the block-length rule. A visible trend or regime transition defeats the stationary-process interpretation. Named-period dispersion then remains descriptive evidence, not an automatic confidence interval.

Use uncertainty labels that name their source:

| Label | Supports | Does not support |
|---|---|---|
| `finite-window census; no interval` | Exact result for the fixed artifact and every eligible origin in `W` | Future periods, regimes, or training runs |
| `evaluation Monte Carlo interval` | Random arrivals/window starts conditional on fixed trace and artifact | Temporal generalization or model uncertainty |
| `dependence-aware temporal interval` | A stated stationary/weakly dependent process mean within the declared regime | Upgrade/regime uncertainty or training-seed uncertainty |
| `training-seed range/distribution` | Optimization/training procedure sensitivity on the same data split | New temporal histories; seeds are not extra origins |
| `named-period variation` | Robustness across the displayed periods | IID replication unless periods came from a valid sampling design |

Millions of overlapping origins do not create millions of independent observations. Random replay repetitions are conditional simulation replicates, not deployment histories. A confidence interval without the source label is ambiguous.

## Seed protocol consequences

Exhaustive named-window evaluation needs no evaluation seed. Stochastic training still needs a predeclared seed set and all seed results; best-seed selection changes the estimand and biases comparison.

Two training targets are possible and must be named:

```text
fixed-artifact performance: one declared fitted seed, conditional result
training-procedure performance: aggregate over a predeclared seed distribution/set
```

Do not treat `(origin, seed)` cells as IID. The same trace is reused across seeds, and each seed's model induces outcomes across all origins. Report seed sensitivity separately from temporal dependence.

The same numeric training seed across different model implementations is not automatically a paired stochastic draw: implementations can consume randomness differently. Treat training seeds as paired only when the experimental randomization is explicitly coupled. Origin-level outcomes remain paired conditional on the declared fitted artifacts.

If a Poisson or random-window sensitivity survives, use a separate declared evaluation RNG stream and reuse the same request/window draws for every compared policy. Common random numbers are a standard paired simulation design ([Heikes, Montgomery, and Rardin 1976](https://doi.org/10.1177/003754977602700301)). This reduces comparison noise but does not change the arrival estimand. Training seeds and evaluation seeds must not be conflated.

## Practical equivalence for preferring leanness

“No statistically significant difference” is not evidence of practical equivalence. Define the paired effect in one direction and predeclare a smallest material difference `delta` in the primary outcome's units before inspecting validation or testing outcomes. Apply model-selection tolerance on validation only; testing remains sealed evidence rather than another selection surface.

For a lower-is-better loss, let `Delta=E[L_lean-L_complex]`:

```text
non-inferiority of lean model: upper one-sided confidence bound for Delta < delta
symmetric equivalence:        confidence interval for Delta lies inside (-delta, +delta)
```

The two one-sided-tests construction treats non-equivalence as the null and corresponds to containment of a `100*(1-2*alpha)%` confidence interval under its assumptions ([Schuirmann 1987](https://doi.org/10.1007/BF01068419)). One-sided non-inferiority matches a rule that tolerates at most `delta` degradation in exchange for leanness; two-sided equivalence answers the stronger question that neither model differs materially. Issue 48 must choose which claim it wants.

For the finite-window census alone, `Delta_W<delta` is a deterministic non-inferiority rule and `|Delta_W|<delta` is a deterministic symmetric-equivalence rule, not an inferential test. For a process/generalization claim, use a paired dependence-aware interval. Define `delta` as absolute base-fee units, percentage points, blocks, or another declared unit; never mix absolute and relative tolerance. A ratio tolerance must say whether it applies to the finite-window ratio or ratio-of-expectations. Safety/structural availability constraints should remain explicit gates rather than being traded through an expanding metric average.

## Decision consequences without a policy choice

The methods leave four mutually distinct claims:

1. Exhaustive named-window replay supports a finite, equally weighted eligible block-origin claim with no evaluation RNG.
2. Wall-clock weighting or time-Poisson replay supports an exogenous request-time claim only with valid parent-availability intervals; whole-second header timestamps cannot establish exact exposure for tied blocks.
3. Uniform random starts preserve a paper-style random-window target only through the explicit start-inclusion kernel. Whole-corpus replay changes that target.
4. Any claim beyond the observed windows needs separately labelled temporal-process, regime, and training-seed evidence. None can be manufactured from IID origin errors or replay repetitions.

These are estimand choices, not interchangeable implementations. Arrival rate or stochastic replay earns distinct information only for request counts, workload totals, queues/interactions, empty-window risk, finite-workload nonlinear ratios, or fidelity to an explicitly retained request-arrival claim.
