# Issue 48 accounting fixture

Status: throwaway research prototype. It changes no production module, corpus,
artifact, database, configuration, ADR, or normative guide.

Question: does exhaustive fixed-`K` accounting stay explicit and coherent across
earliest-argmin labels, weighting choices, duplicate timestamps, structural exclusions, serving
availability, finite ratios, and zero denominators? The prototype assumes the
owner-approved issue-46 clock and target mapping. It does not choose `K`, windows,
or issue-47 preprocessing eligibility.

Run the complete non-interactive fixture:

```sh
uv run python docs/research/issue-48-temporal-evaluation/explore_fixture.py
```

Add `--interactive` to switch between equal block-opportunity and wall-clock
weights in a one-screen terminal loop. Query the two frozen historical diagnostic
windows separately:

```sh
uv run python docs/research/issue-48-temporal-evaluation/representative_frozen_window.py
```

## Pure interface and fixed contract

[`fixture_semantics.py`](fixture_semantics.py) exposes one scoring interface:

```text
evaluate(origins, action_count=K, weighting=..., window_end_timestamp_s=...)
```

This is a small deep module: callers declare origins and the estimand; the module
owns target arithmetic, raw-value minima, exact decompositions, weights, units, and
undefined denominators. It uses `fractions.Fraction`, so every hand-fixture result
is exact.

For a decision after latest closed canonical parent `h`, tuple position `k` is the
intended target `h+1+k`. `k=0` is the immediate attempt. For `k>0`, the broadcast
trigger is observation of target parent `h+k`; the transaction remains unchanged.
The historical target fee is a counterfactual base-fee opportunity. It is not
transaction inclusion or actual execution cost.

An origin is scoreable only when issue 47 has already declared it structurally
eligible, its complete causal span and all `K` target outcomes exist in one regime,
and it yields exactly one action. Missing inference at an eligible offline origin
invalidates evaluation; it is never silently dropped or replaced by `k=0`.
`structural_exclusion_reason` is an input to this prototype. The prototype does not
derive it and therefore does not settle issue 47.

Serving availability uses the separate
`summarize_serving_availability(attempts)` interface. It counts snapshot, inference,
action-opportunity, broadcast-submission, and receipt-observation stages with
conditional denominators. These counts never enter the offline model-score
denominator. There is no deadline, overflow, or fallback model metric.

## Exact per-origin semantics

For every structurally eligible origin `i`, let:

```text
f[i,k]  raw integer historical base fee per gas at target h[i]+1+k
p[i]    selected k
B[i]    f[i,0]                              immediate_k0_reference
R[i]    f[i,p[i]]                           selected target opportunity
O[i]    min_k f[i,k]                        hindsight_best_within_K fee
o[i]    min {k : f[i,k] = O[i]}             earliest hindsight label
S[i]    B[i] - R[i]                         base-fee savings per gas
G[i]    B[i] - O[i]                         hindsight opportunity gap per gas
Q[i]    R[i] - O[i]                         hindsight regret per gas
```

The identity `S[i] + Q[i] = G[i]` is exact. `Q[i] >= 0`; `S[i]` may be negative.
Raw fee integers define the minimum and deterministic earliest argmin label.

`harmful_action[i] = 1[R[i] > B[i]]`. Equality is not harmful. Equal minima are
possible: the one-off audit found 29 among 13,435,494 post-Granite Avalanche `K=5`
origins and none in the audited modern Ethereum and Polygon corpora. Selecting a later
equal minimum misses the earliest label while the economic accounting gives zero regret.
No tie-specific metric, counter, mode, or test matrix is retained.

Block-triggered wait is:

```text
wait_blocks[i]  = p[i]
wait_seconds[i] = 0                                      if p[i] = 0
                  timestamp(h[i] + p[i]) - timestamp(h[i]) otherwise
```

The second line uses candidate timestamp position `p[i]-1`, because candidate
position zero is block `h+1`. It is the trace displacement until the approved
broadcast trigger, not target-block displacement, local inference latency, or
receipt time.

## Aggregation, denominators, and units

Let `w[i]` be the declared estimand weight and `g[i]` a predeclared request gas
quantity in gas units. Its source and schedule must be fixed before outcome
inspection. Every model formula below ranges over all structurally eligible origins;
none ranges over only successful inferences.

```text
mean base-fee savings per gas       = sum w[i] S[i] / sum w[i]
mean hindsight opportunity gap      = sum w[i] G[i] / sum w[i]
mean hindsight regret               = sum w[i] Q[i] / sum w[i]

gas-weighted savings ratio of sums  = sum w[i] g[i] S[i]
                                      --------------------
                                      sum w[i] g[i] B[i]

gas-weighted opportunity ratio      = sum w[i] g[i] G[i] / sum w[i] g[i] B[i]
gas-weighted regret ratio           = sum w[i] g[i] Q[i] / sum w[i] g[i] B[i]

harmful-action rate                 = sum w[i] 1[R[i] > B[i]] / sum w[i]
mean wait in block opportunities    = sum w[i] p[i] / sum w[i]
mean broadcast wait seconds         = sum w[i] wait_seconds[i] / sum w[i]
earliest-hindsight-label accuracy   = sum w[i] 1[p[i] = o[i]] / sum w[i]
```

Fees `B`, `R`, `O`, `S`, `G`, and `Q` have base-fee-units-per-gas units.
Multiplying by `g` gives counterfactual base-fee amount units, not actual execution
cost. The three ratios are dimensionless and share one baseline denominator, so
savings plus regret equals opportunity after aggregation too. A fee-per-gas sum
without a declared gas quantity is not called gas-weighted spending.

The diagnostic mean of finite per-origin ratios is different:

```text
mean origin savings fraction = sum_{B[i]>0} w[i] S[i]/B[i]
                               -----------------------------
                               sum_{B[i]>0} w[i]
```

The two-state fixture has `(savings, baseline) = (1,1)` and `(0,9)`. Its
equal-origin one-request expected ratio is `1/2`; its finite-fixture ratio of sums
is `1/10`. The ratio of sums is first an exact property of that declared finite
fixture or window. It becomes a ratio-of-expectations or long-run target only under
an explicitly declared independent exposure process. It is not the expected ratio
of an arbitrary finite random workload. If any requested denominator is zero, the
result is explicitly undefined with its numerator and denominator retained; the
prototype never emits zero, infinity, or NaN as a substitute.

## Block opportunity versus wall clock

`block_opportunity` sets `w[i]=1`, evaluating every eligible closed-parent origin
once. It matches the fixed same-`K` block-opportunity question and does not require
an arrival rate, replay repetition, or seed.

`wall_clock_latest_parent` sets:

```text
w[i] = parent_timestamp[i+1] - parent_timestamp[i]
w[last] = declared_window_end - parent_timestamp[last]
```

This is the exposure of a latest-parent state in half-open time intervals. With
duplicate integer timestamps, earlier tied parents receive zero exposure and the
last tied parent receives the interval until the next timestamp. In the fixture,
origins B and C both have timestamp 10; B has wall-clock weight zero while both
retain block-opportunity weight one. A positive block wait can likewise appear as
zero seconds at coarse timestamp resolution.

That behavior is coherent for the stated lookup rule but is a measurement artifact,
not evidence that the earlier block had no real-time opportunity. Splitting tied
time equally would invent another rule. A wall-clock estimand therefore needs a
proved decision-time clock and sufficient timestamp resolution. The hand fixture's
harmful-action rate changes from `1/4` under block weights to `1/3` under wall-clock
weights; its savings ratio changes from `4/117` to `1/11`. Weighting is substantive,
not presentation.

## Frozen 300/1,200-window diagnostic

[`representative_frozen_window.py`](representative_frozen_window.py) opens
`benchmarks/results.sqlite` with `mode=ro&immutable=1`, verifies SHA-256
`ba70a8f65e9210edc2cfee63243d69e46f55235f5b78f39d7dd5cdd83bf724b0`, and reads
one archived Polygon 300-block row and one 1,200-block row. They were selected
after outcome inspection to expose reducer sensitivity, so they cannot become
protocol windows.

| Old window | Samples / sampled events | Archived mean event savings | Reconstructed fee-per-gas ratio of sums |
| --- | ---: | ---: | ---: |
| Polygon 300, start 82,363,890 | 300 / 17,858 | -0.22366770% | +0.00934817% |
| Polygon 1,200, start 80,322,090 | 1,200 / 17,876 | -0.38301240% | +0.03832282% |

Both signs change under the reducer. This proves that the denominator choice is
material. It does not approve the ratio of sums, the historical windows, or the old
models. The frozen index contains Poisson-reweighted old-current-row aggregates,
not one row per clean-contract eligible origin. It lacks transaction gas vectors,
raw tie sets, issue-47 eligibility, and clean-contract predictions. It therefore
cannot calculate or validate the proposed primary metrics; a clean rerun is needed.

## Prototype answer and owner status

The prototype found exhaustive once-per-eligible-origin accounting to be the leanest
coherent primary route for the fixed same-`K` block-opportunity claim. Edo approved
that route on 2026-07-12: the sealed testing role uses the full eligible range, equal
block-opportunity weights, and no Poisson, random-start, replay-repetition, or
wall-clock primary estimator. The exact approved wording is in
[`decision-contract.md`](decision-contract.md).

The amended owner-approved K contract uses 10 independently trained LSTM horizons on
three chains and exactly one predeclared ML training seed. `K=5` is the
primary/default/headline condition; serving/mobile supports separately trained
`K=2,3,4,5` artifacts through a discrete block-horizon choice. See
[`decision-contract.md`](decision-contract.md).
Issue-47 eligibility inputs remain upstream. The fixture does not decide them.

The owner-approved metric contract keeps the additive finite ratio-of-sums as the
canonical economic surface, adds the three required secondary paper-alignment
mean-origin reducers and frozen-artifact predictive diagnostics, and retains the
auxiliary fee-regression head with target-explicit Smooth-L1 loss plus log-view MAE and
MSE. No native-unit regression MAE or inverse-reporting path is required for scoring.
Exact head target/scaling/checkpoint/architecture semantics remain with their linked
owning issues in [`decision-contract.md`](decision-contract.md).

The testing-process contract uses one predeclared chronological range per chain, accepts
existing or newly acquired data, permits retained-data reruns, and adds no reuse registry
or mandatory replacement suffix. Testing does not select development choices; unavoidable
iteration on the same range is disclosed once as a plain methodological limitation.

The approved secondary condition view uses every testing origin at `K=5`, with only raw
closed-parent fee and signed one-block log fee change as x descriptors. Four tie-
preserving within-chain value quartiles must recombine exactly to the full raw totals.
All selected-window, rolling-descriptor, Poisson/random replay, 300/1,200, correlation,
and replay-interval machinery is retired from the final protocol while frozen outputs
remain archival.

Each chain's official test is its maximal contiguous post-validation range inside one
approved regime, after the required purge and through the frozen corpus endpoint. Every
eligible origin complete through `K_max=200` is scored. Counts, exclusions, endpoints,
and elapsed spans remain chain-specific; no common size or duration is imposed. After
any separately approved one-time suffix acquisition, freeze one endpoint per chain;
later data never auto-appends.

Before official scores open, exact work counts and—only when needed—one small
metrics-blind throughput preflight may establish whether the complete artifact matrix is
affordable. It exposes no predictions or metrics and adds no profiling framework. If
the maximal matrix is unaffordable, stop and return to Edo before any official outcome;
never inspect partial results and truncate. No numeric testing cap is approved.

The approved leanness rule is narrow and validation-only. At `K=5`, a later owning
ticket may predeclare a materially leaner candidate and complex reference. The lean
candidate must remain within five absolute percentage points of captured hindsight
opportunity on every chain and approved seed, on identical origins, without increasing
the harmful-action rate. The rule has no effect without that predeclared comparison and
does not reopen any fixed contract choice.

Edo approved the complete contract on 2026-07-12. The
[single resolution comment](https://github.com/edoski/spice/issues/48#issuecomment-4950650999)
is canonical; issue 48 is closed as completed.
