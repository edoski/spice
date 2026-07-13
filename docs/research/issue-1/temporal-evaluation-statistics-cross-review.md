# Temporal evaluation and statistics cross-review

Date: 2026-07-10

Status: independent research and red-team evidence. This report approves no action
clock, evaluator, metric, split, HPO policy, thesis claim, ADR, or migration. The paper,
current code, companion audits, and this report remain challengeable inputs.

Scope: Poisson selection, deterministic evaluation, economic estimands, temporal
uncertainty, split ownership, tie-aware metrics, and validation-based model selection.
Production code, ADRs, architecture notes, and GitHub issues were not changed.

## Corrections first

Two companion-audit conclusions need qualification.

1. **Random replay windows are independent Monte Carlo draws conditional on the fixed
   trace.** `PoissonReplayAdapter` samples each window start and its arrivals afresh.
   Two sampled windows may overlap in historical time, but each run is still a function
   of an independent random draw and a fixed trace. Overlap does not by itself invalidate
   a Monte Carlo standard error for the simulator's conditional expectation. That error
   still says nothing about new days, new fee regimes, new model seeds, or new chains.
2. **Whole-corpus duration weighting is not an exact replacement for the current random-
   window evaluator.** It is exact for a fixed interval. The current evaluator also draws
   the interval start uniformly. An exact deterministic replacement must integrate that
   random-window inclusion kernel, or deliberately replace random windows with named
   fixed windows. The latter may be the clearer thesis design, but it changes the
   estimand.

Other audited claims survive:

- the event mean and ratio of fee sums are different estimands;
- the historical Polygon sign can change with that choice;
- forward label horizons cross the current adjacent role boundaries;
- past-context overlap is not the same defect;
- exact row identity is not fee-optimal accuracy when minima tie;
- current replay cannot establish the intended block-open action semantics because it
  discards the request timestamp after selecting a row;
- validation economic selection is legitimate, but a large search can overfit that
  finite validation criterion just as it can overfit validation loss.

## 1. The intentional current/forming-block target is not the statistical defect

The owner clarified that offset zero was intentionally extended beyond the paper to mean
the current/forming block. This review accepts that as design intent. It does not relabel
offset zero as an accidental off-by-one bug.

The remaining question is whether requests are assigned to decision states that can act
on that block.

Current time replay computes

```text
state(arrival a) = last sample i whose timestamp t_i <= a
```

with `searchsorted(..., side="right") - 1` in
`src/spice/evaluation/poisson_replay.py:46-61`. It then retains only the sample position;
the actual arrival time is absent from outcome realization.

That mapping has different meanings under two contracts:

| Contract | Meaning of row `i` | Is latest-prior mapping coherent? |
| --- | --- | --- |
| Post-observation immediate action | block `i` has been observed; requests arriving until the next observation use its state; first eligible inclusion is later | Yes as a state lookup. Offset zero must then realize the first eligible future block, not observed block `i`. |
| Intentional block-open action | row `i` is a virtual state available while forming block `i` is still actionable | Only if the project defines the interval during which every feature is available and a broadcast can still reach `i`. The current interval `[t_i,t_{i+1})` is not that proof. |

For the block-open route, the correct object is an eligibility interval `I_i`:

```text
I_i = request times for which virtual row i is available
      and block i remains a valid inclusion target
```

Its end may be a proposer/broadcast cutoff before the recorded block timestamp. It need
not equal the next inter-block interval. A deterministic evaluator should weight row `i`
by `|I_i|`; a stochastic evaluator should preserve the arrival timestamp and map it to
the next still-eligible action.

Two additional code facts matter:

- Integer-second duplicate timestamps give all positive exposure to the last sample in
  the tied group. Earlier same-timestamp samples can never be selected by continuous
  arrivals. This is a clock-resolution artifact, not evidence that those block decisions
  have zero real exposure.
- `BlockPoissonReplayAdapter` assigns Poisson multiplicities per abstract block offset.
  Conditional on a fixed block window, it weights blocks equally in expectation. It is
  not a homogeneous wall-clock arrival process; it assumes workload scales with block
  production rather than elapsed time.

The paper's simulation assumes a request is included in the immediately next block. The
current-forming-block route is an intentional extension. Paper fidelity should therefore
be reported as a difference, not used to choose the route automatically.

## 2. Exact deterministic reduction, with the missing caveats

### Fixed interval: exact event-mean result

Fix a replay interval `W=[s,s+T)`. Let `N` be the number of homogeneous Poisson arrivals
with rate `lambda`. Conditional on `N=n`, the unordered arrival times are independent
uniform draws on `W`; this is the standard conditional-arrival theorem for a Poisson
process ([MIT 6.262, Sec. 2.5](https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/resources/mit6_262s11_chap02/)).

Let state `i` own exposure length `e_i` inside `W`, and let its deterministic per-request
metric be `m_i`. For every `n>0`,

```text
E[event mean | N=n, W] = sum_i e_i m_i / T
```

Therefore the same formula holds conditional on a nonempty run. `lambda` cancels. For a
fixed block-index window, each block has unit exposure and the exact expected event mean
is the ordinary mean across blocks.

This reduction needs these conditions:

- requests do not alter fee dynamics, queues, capacity, model state, or later requests;
- the action/outcome for a state is deterministic once model and trace are fixed;
- the exposure intervals match the approved decision clock;
- the target is a normalized event mean, not finite-workload totals or tail probabilities.

Rate remains necessary for request counts, total cost, empty-window probability,
congestion, coupled requests, and finite-workload distributions.

### Random interval start: integrate the window kernel

Current time replay also samples

```text
S ~ Uniform(first_timestamp, last_timestamp - T).
```

Let corpus support be `[a,b]`. A time point `u` is included by all starts in

```text
[max(a, u-T), min(u, b-T)].
```

Its unnormalized inclusion weight is therefore

```text
q(u) = max(0, min(u, b-T) - max(a, u-T)).
```

An exact replacement for the current random-start expectation integrates each state
metric against `q(u)`, then normalizes by `(b-a-T)T`. The edges receive less weight than
the corpus interior. The block-index evaluator has the discrete analogue: a block's
weight is the number of possible `K`-block windows containing it.

A tiny locked-environment probe demonstrates why plain whole-corpus weighting is not
equivalent. The ten unit intervals had metric one only in the first and last two:

```text
whole-corpus duration mean       0.400000
exact random 4-unit-window mean  0.166667
200,000-draw simulation          0.166190
```

The exact random-window answer is `4/24`: the inclusion kernel downweights the edges.

Three valid but distinct targets now exist:

1. reproduce the paper/current random-window distribution by deterministic kernel
   integration;
2. evaluate a fixed full trace with duration or block exposure weights;
3. predeclare several named evaluation windows and report each directly.

Candidate 3 is easiest to teach and exposes regime variation. It is a deliberate protocol
change, not a mathematically exact refactor of candidate 1.

### Ratio of sums: exact long-run target, not every finite ratio

For event savings `X_i=B_i-R_i` and positive baseline cost `Y_i=B_i`, exposure weighting
gives

```text
long-run spend savings ratio = sum_i e_i X_i / sum_i e_i Y_i.
```

This is the ratio of expected aggregate savings to expected aggregate baseline spend and
the long-run ratio under the independent-request model. It is generally not

```text
E[finite random sum(X) / finite random sum(Y)].
```

The distinction is large in a two-state probe. Equal-probability states
`(savings, baseline)=(1,1)` and `(0,9)` give mean request savings `50%`, ratio of
expected sums `10%`, and expected one-request spend ratio `50%`. The finite random ratio
approaches `10%` only as workload grows.

The evaluator and documentation must name which of these is intended. “Deterministic
Poisson evaluation” is not enough.

## 3. Economic estimands and the historical sign flip

Current offline replay reports

```text
mean_request_base_fee_savings = mean_i((B_i-R_i)/B_i)
```

under the name `profit_over_baseline`. Serving reports

```text
total_spend_savings = sum_i(B_i-R_i) / sum_i B_i,
```

where serving multiplies each candidate base fee by that transaction's gas used. Both
are valid questions:

- mean request savings gives each request equal weight;
- total spend savings gives expensive or high-gas requests more weight.

Neither is “profit.” The code does not model revenue, all transaction fees, or latency
utility. Offline values are base fee per gas reconstructed from model floats; serving
values are base-fee amounts using observed gas. Names should state base-fee scope.

A read-only query against `benchmarks/results.sqlite` reproduced the companion audit's
sign-flip claim. It joined each observation's event mean with its baseline and realized
fee sums. The database contains two 648-observation benchmark collections using the same
three trained artifacts; these are archival diagnostics, not 1,296 independent trials.

| Chain | Observations | Mean event percentage | Mean per-observation spend ratio | Pooled ratio across all observations | Event/spend sign disagreements |
| --- | ---: | ---: | ---: | ---: | ---: |
| Avalanche | 432 | +0.384616% | +0.535235% | +1.821384% | 28 |
| Ethereum | 432 | +1.181614% | +1.314268% | +1.217594% | 2 |
| Polygon | 432 | -0.060895% | +0.046088% | +0.034292% | 50 |

The 80 sign disagreements prove that aggregation choice is material. They do not prove
that the spend ratio is the right target, or that the historical model is beneficial.
The pooled column weights repeated observations by their fee totals and must not be
pooled across chains as one thesis headline; chain currencies, fee scales, workloads,
and duplicated evaluation designs differ.

A clean metric decomposition can share one baseline denominator:

```text
request savings = (B-R)/B
oracle opportunity = (B-O)/B
model regret = (R-O)/B

request savings + model regret = oracle opportunity
```

Use gas-weighted sums for an operational spend ratio when gas is part of the approved
estimand. Keep mean request savings for distributional visibility and paper comparison.

## 4. What each uncertainty source can support

The word “repetition” currently hides different units.

| Source varied | Statistical unit | What variation means | What it cannot establish |
| --- | --- | --- | --- |
| Poisson/window RNG on one fixed trace and model | replay run | Monte Carlo integration error under the chosen window/arrival distribution | new-day, new-regime, or training uncertainty |
| Training seed | fitted model | initialization, minibatch order, dropout, and other algorithmic randomness | data/period uncertainty |
| Held-out date or non-overlapping regime window | temporal deployment period | sensitivity to market/fee conditions | population-of-days inference unless periods were sampled from a defined population |
| Neighboring blocks or sliding origins | subsamples within a period | detailed paired behavior | independent replication; serial and horizon overlap remain |
| Chain | distinct prediction task/domain | per-chain robustness | an IID replicate unless a target population of chains and sampling rule are defined |
| HPO trial | selected candidate | search evidence | an independent performance replicate |

### Current replay bars are narrow by construction

`temporal_replay_window_metrics` takes the population standard deviation of run-level
means. Rendering scripts use `1.96 * std / sqrt(repetitions)`. Conditional on a fixed
trace/model and ideal independent RNG, that is an approximate Monte Carlo error bar for
the **unweighted mean of run means**. The aggregate metric stored in
`TemporalReplayResult.metrics` is instead event-count weighted. Both target the same
expectation here because every window has equal duration/rate and event count is
independent of window state, but they are different finite estimators.

If this Monte Carlo bar remains, estimate run variance with the sample standard deviation
(`ddof=1`) and label the `1.96` interval as an asymptotic Monte Carlo interval. Current
`ddof=0` treats the finite run set as the full population and is slightly too small; this
is minor beside the estimand and interpretation problems.

The bar is not a confidence interval for deployment performance. Increasing repetitions
can drive it near zero while the model, trace, and day never change.

### Overlap needs two separate statements

- Independently sampled replay windows may overlap and still be independent Monte Carlo
  draws conditional on the fixed trace.
- Historical windows treated as empirical deployment replicates are not made independent
  by a fresh RNG seed. Sliding/overlapping windows share outcomes; even disjoint windows
  can remain serially dependent.

The checked-in recommended-window files illustrate both designs. A read-only interval
probe found zero overlaps among the 216 selected block-count windows per chain. The 216
wall-clock recommendations had 112 adjacent overlaps on Ethereum, 129 on Polygon, and
130 on Avalanche after sorting by start. The block windows are still deliberately
quartile-selected rather than random population samples, so `1.96*SD/sqrt(n)` across
them has no automatically defined population interpretation.

If formal time-series intervals are required, a moving-block bootstrap is the relevant
family because it resamples contiguous dependent observations
([Künsch, 1989](https://doi.org/10.1214/aos/1176347265)). It assumes a sufficiently
stationary regime and needs a defensible block length. Forks and major fee-regime changes
should be stratified first. For this undergraduate thesis, paired raw results across
named periods and seeds are clearer than an elaborate interval with weak assumptions.

Forecast evaluation should preserve temporal ordering and use multiple forecast origins
or test periods when the claim spans time ([Tashman, 2000](https://doi.org/10.1016/S0169-2070(00)00065-0)). Repeated measurements from one temporal unit should not be
presented as independent treatment replications; this is the classic temporal
pseudoreplication problem ([Hurlbert, 1984](https://doi.org/10.2307/1942661)).

## 5. Label-horizon leakage is real; input overlap is normal

`fixed_sequence_temporal.py` constructs future candidate windows, then slices sample
origins into adjacent train/validation/test fractions. It does not remove earlier-role
samples whose outcomes reach the next role.

This is leakage relative to a fixed-origin deployment experiment: to fit the model using
the last training label, the evaluator must wait for an outcome that occurs at or after
the first nominal validation decision. That validation decision could not then have been
forecast in real time by the fitted model.

The correction is outcome-based:

```text
train sample is valid iff every fact used by its target is before validation start
validation sample is valid iff every fact used by its target is before test start
```

Use exact outcome-end timestamps/rows rather than a guessed generic gap. Context rows may
look backward across the boundary. Adjacent validation examples may share most of their
past context. Both are ordinary causal forecasting behavior, not leakage. They do imply
dependent errors, so anchor count is not an independent sample size.

The paper says its temporal intervals do not overlap. Current origin slicing does not
satisfy that claim at the label boundary. The right fix is not random splitting and not
purging the full lookback context; it is purging forward outcome dependencies.

## 6. Exact and tie-aware decision metrics

Current target construction uses `np.argmin`, which chooses the earliest row among equal
fees. Current `exact_optimum_hit_rate` compares row identity. Those two facts define a
lexicographic target:

```text
first minimize fee; among equal fees, minimize delay.
```

That is coherent if intended. It should not be named plain fee-optimal accuracy. A later
equal-fee action is economically optimal but fails the row-identity metric.

Define the feasible optimal action set from raw integer economic values:

```text
A*_i = {a in feasible actions: cost(i,a) = min_feasible_cost_i}
tie_aware_hit_i = 1[predicted action in A*_i]
```

Then report a separate `earliest_minimum_hit` only if delay is the approved tie-break.
Raw integer base fees should remain beside transformed model inputs; exact equality and
accounting should not depend on exponentiating float32 logs.

Minimum useful evaluation surface:

- one approved aggregate base-fee savings estimand;
- baseline-normalized feasible-oracle regret;
- harmful-action rate `P(R>B)`;
- deadline-miss/fallback rate;
- wait or delayed-request distribution;
- tie-aware minimum-fee hit as a diagnostic;
- ordinary offset accuracy only for paper comparison.

Macro F1 does not add economic or temporal information. If retained for comparison, use
the conventional union-active definition. Its implementation correctness does not make
it a headline metric.

Deadline behavior must settle first. Current overflow can use a cheaper post-window row,
making feasible-oracle regret negative. Do not clamp that value: clamping hides the
contract failure. Either mask unavailable actions, realize an explicit fallback, or apply
an approved miss penalty, then compute economics under that same policy.

## 7. Economic validation selection is valid, not immune to overfit

Choosing a model with deterministic validation economics is conceptually sound when the
deployment goal is economic. Cross-entropy is not automatically a better model-selection
criterion merely because it is a training loss.

The risk comes from repeated search over a finite validation trace. The more epochs,
features, model families, seeds, HPO trials, and metric variants are tried and selected on
the same validation evidence, the more the chosen validation score can exploit noise or
period-specific quirks. Cawley and Talbot show that model-selection criteria themselves
can be overfit, creating optimistic subsequent evaluation
([JMLR 2010](https://www.jmlr.org/papers/v11/cawley10a.html)). HPO is an intentional and
valuable extension here; this finding calls for a bounded sealed protocol, not deletion.

The simplest defensible division is:

1. use corrected validation training loss for epoch early stopping and pruning;
2. at each trial's selected checkpoint, compute one predeclared deterministic validation
   economic score on identical origins;
3. let bounded HPO rank configurations by that score, with named safety constraints;
4. rerun the frozen finalist configuration over predeclared seeds;
5. do not choose the best seed; report every seed;
6. evaluate the frozen candidates on the final test periods and do not revise the design
   afterward.

This uses one validation set for both early stopping and bounded model selection. A
separate validation-within-validation split or nested time-series search would reduce
reuse but adds data loss and machinery. It is not needed for a careful bachelor's thesis
if the search space/budget, metric, origins, and test seal are declared before results.

Search budget is part of the method. Reporting all HPO trials and finalist seeds matters
because initialization, data, and hyperparameter variation can materially change ML
benchmark conclusions ([Bouthillier et al., MLSys 2021](https://proceedings.mlsys.org/paper/2021/hash/0184b0cd3cfb185989f858a1d9f5c1eb-Abstract.html)).

## 8. Minimum defensible thesis protocol

This is a candidate low-machinery protocol. Owner approval remains required.

1. **Freeze one action record per chain/regime.** Record request time, information set,
   virtual/forming row, offset zero, broadcast eligibility, inclusion, deadline, fallback,
   baseline, and feasible oracle. Preserve the intentional current-block route where its
   eligibility interval is proved.
2. **Build roles from raw-time cutoffs.** Purge every earlier-role origin whose complete
   target horizon crosses the next cutoff. Allow causal past-context overlap. Fit all
   preprocessing on training facts only.
3. **Predeclare evaluation periods.** Use several named post-cutoff dates or non-overlapping
   regime windows per chain. Pair every method on the same periods. Do not choose periods
   after seeing model outcomes.
4. **Keep HPO bounded and validation-only.** One exploration seed is acceptable for the
   search. Use identical validation origins, corrected loss, real epoch pruning or no
   pruning, and one predeclared economic ranking score. Never compute test metrics inside
   trials.
5. **Confirm the finalist across seeds.** Use at least three predeclared seeds; five if
   affordable. Report all values and do not select a lucky seed. Seeds measure training
   variability, not time variability.
6. **Evaluate each decision state once.** For named fixed windows, use exact contract-
   appropriate exposure weights. Keep Poisson simulation only as a reproduction view or
   a one-time high-sample proof of the deterministic reducer.
7. **Report chains separately.** Show the seed-by-period matrix for each chain. Give paired
   method differences, median/IQR or mean/SD as descriptive summaries, and no default
   p-value. Do not turn blocks, overlapping origins, seeds, and chains into one flat `n`.
8. **Use a small metric set.** Candidate primary: long-run gas-weighted base-fee spend
   savings. Candidate secondary: mean-request savings, feasible-oracle regret, harmful
   rate, deadline/fallback rate, wait, and tie-aware hit. Keep paper metrics explicitly
   labeled as comparison metrics.
9. **Open the test after freezing the protocol.** Testing all predeclared baselines and the
   frozen finalist once is valid. Changing features, HPO, metrics, or period selection
   afterward converts that test into development evidence and requires a new final holdout.

This protocol does not need confidence intervals. Raw paired results across periods and
seeds expose the two important variability sources more honestly. Add a chain-local block
bootstrap only if an inferential interval is required and its stationarity assumptions can
be defended.

## 9. Ticket implications

No ticket was created or edited. The shared map should incorporate these changes:

| Ticket implication | Required acceptance |
| --- | --- |
| Correct the Poisson/deterministic prototype | Test fixed-window exposure reduction; test uniform-random-start kernel reduction; state when named windows intentionally change the estimand; cover duplicate timestamps and block-vs-time weighting. |
| Correct the uncertainty ticket | Say sampled replay windows are IID conditional Monte Carlo draws even when they overlap; forbid interpreting their SE as deployment uncertainty; keep seeds, periods, blocks, and chains as separate units. |
| Preserve the intentional offset-zero route as a candidate | Define `I_i`, the interval in which forming block `i` is actionable, and prove every feature is available there. Do not auto-shift labels to `+1`. |
| Purge split outcomes | Assert zero forward target dependencies across role cutoffs while allowing past-context overlap. |
| Choose economic estimands and names | Distinguish mean request, per-period spend ratio, pooled ratio, and finite random ratio; choose gas weighting and base-fee scope; ban generic “profit.” |
| Choose tie/deadline policy | Define feasible action set, raw-value ties, latency tie-break, overflow fallback/penalty, harmful action, and nonnegative feasible regret. |
| Repair intentional HPO | Validation-only trial summaries; bounded declared budget; common origins; loss-based pruning; deterministic economic trial rank; multi-seed frozen finalist; no best-seed reporting. |
| Reassess historical results | Preserve both stored event means and reconstructed fee-sum ratios under explicit old semantics; record the 80 sign disagreements; do not silently relabel archival values. |
| Modernize evaluation docs after decisions | Teach the fixed-window derivation, random-window kernel, finite-ratio caveat, uncertainty-unit table, split fixture, tie example, and validation/test seal. |

Dependency order remains: decision clock and feasible action set -> split ownership and
metric definitions -> deterministic evaluator -> validation/HPO protocol -> final thesis
evaluation. Statistical polish cannot rescue a mismatched action contract.

## Reproducible local probes

Historical query shape:

```sql
with p as (
  select o.observation_id, o.chain_name,
         max(case when m.metric_id='profit_over_baseline' then m.value end) as event_mean,
         max(case when m.metric_id='baseline_fee_sum' then m.value end) as b,
         max(case when m.metric_id='realized_fee_sum' then m.value end) as r
  from result_observations o
  join metric_values m using (observation_id)
  where m.source='evaluation'
  group by o.observation_id, o.chain_name
)
select chain_name,
       count(*) as n,
       avg(event_mean),
       avg((b-r)/b),
       (sum(b)-sum(r))/sum(b),
       sum((event_mean<0) != ((b-r)/b<0))
from p
group by chain_name;
```

All database access used `sqlite3 -readonly`. Numerical probes used the locked `uv`
environment and fixed RNG seed `20260710`. No result, corpus, artifact, or production
file was written.

## Primary sources

- Professor paper: `/Users/edo/Documents/Obsidian/the-vault/university/Thesis/ICDCS_2026.pdf`, especially the experimental setup and temporal evaluation on pp. 7-9.
- Current replay/accounting implementation: `src/spice/evaluation/poisson_replay.py`,
  `block_poisson_replay.py`, `temporal_accounting.py`, and
  `_temporal_replay_metric_catalog.py`.
- Current split and action implementation:
  `src/spice/modeling/dataset_builders/fixed_sequence_temporal.py` and
  `src/spice/temporal/execution_policy/strict_deadline_miss.py`.
- Current serving aggregate: `src/spice/serving/analytics.py` and
  `src/spice/serving/inference.py`.
- [MIT 6.262 Poisson-process notes, conditional arrival theorem](https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/resources/mit6_262s11_chap02/)
- [Tashman, out-of-sample forecast evaluation](https://doi.org/10.1016/S0169-2070(00)00065-0)
- [Künsch, block bootstrap for stationary observations](https://doi.org/10.1214/aos/1176347265)
- [Cawley and Talbot, model-selection overfitting](https://www.jmlr.org/papers/v11/cawley10a.html)
- [Bouthillier et al., variance in ML benchmarks](https://proceedings.mlsys.org/paper/2021/hash/0184b0cd3cfb185989f858a1d9f5c1eb-Abstract.html)
- [Hurlbert, temporal pseudoreplication](https://doi.org/10.2307/1942661)
