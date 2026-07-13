# Issue 48 temporal-evaluation decision contract

Status: resolved owner-approved contract for
[Prototype and choose temporal evaluation and thesis-evidence semantics](https://github.com/edoski/spice/issues/48).
Only explicitly approved decisions appear under **Approved**. Research candidates and
pending recommendations are not approval.

## Approved

### Decision 1: primary testing estimand and named-window route

Edo explicitly approved this decision on 2026-07-12:

- Testing is the sealed, strictly later, sufficiently broad corpus role.
- Exhaustive once-per-eligible-origin evaluation is the only primary testing estimator.
- Within every predeclared named regime-contained test range, score every issue-47-eligible closed-parent origin exactly once with equal block-opportunity weight.
- Offline origin identity is `(content_bound_corpus_id, chain_id, block_number)`, never timestamp; live decisions separately retain `(h, hash(h))`.
- Remove Poisson arrivals, replay repetitions, random starts, wall-clock weighting, and Monte Carlo intervals from the primary test.
- Report realized `h -> h+K` elapsed time descriptively by chain and regime.
- Multiple predeclared reporting windows are views inside the one testing role, not extra dataset roles.
- The primary headline is an exact finite-window census and claims chain-native block opportunities, not random users, equal seconds, inclusion, or actual execution.
- Old outcome-conditioned representative-quartile window selection cannot define the primary headline.
- The new evaluator uses the full eligible test range. The old 300/1,200-block machinery probably will not survive, but that is direction rather than an exact secondary-view decision. Whether any predeclared fee/volatility strata or 300/1,200 descriptive view earns retention remains a later single issue-48 choice.
- No dates, exact range sizes, or secondary view were approved by this decision.

### Decision 2: fixed-K LSTM horizon experiment and serving horizon choices

Edo explicitly amended and approved this decision on 2026-07-12. This wording replaces
all earlier Decision-2 drafts:

- `K` counts available actions `k=0...K-1`, mapped to targets `h+1...h+K`. `K=2`
  means act now for `h+1` or wait one block and act for `h+2`. There is no `K=1`
  experimental condition or synthetic plot point; immediate `k=0` is the comparator
  inside every K.
- The exact mandatory grid is
  `K in {2,3,4,5,10,15,30,50,100,200}`.
- The mandatory scope is LSTM only, independently trained at every K for Ethereum,
  Polygon, and Avalanche, with the same K condition across chains. The initial matrix is
  exactly 10 horizons by 3 chains: 30 trained artifacts.
- Use exactly one fixed, predeclared ML training seed for this initial matrix. An ML seed
  controls pseudorandom initialization, dropout, and batch order; it is not a blockchain
  or chain seed. Issue 49 owns the numeric value and all compute, stopping, and retry
  rules.
- The curve is explicitly single-seed descriptive evidence. It does not estimate
  robustness to neural-network randomness, must not show seed-based intervals, and must
  not generalize as if it were multi-seed evidence.
- Extra-seed work is deferred, not an adaptive extension. It needs a new explicit owner
  decision and separately named robustness protocol. It may not selectively rerun
  interesting K/chain cells from these testing outcomes or retroactively relabel the
  initial curve as confirmatory multi-seed evidence. A later all-cell or predeclared
  fixed-subset seed study may be considered under a fresh resource/evidence contract; if
  it changes model or protocol claims after testing, preserve the spent-test/fresh-suffix
  rule.
- `K=5` is the primary, default, and headline research/serving/mobile contract.
  Serving/mobile supports exactly `K in {2,3,4,5}` through separately trained artifacts.
  `K=2...4` are secondary/demo choices and do not change the primary `K=5` thesis
  headline. No `K>5` artifact is served.
- Replace the prototype's seconds slider with a discrete block-horizon slider containing
  exactly `2, 3, 4, 5`. The chosen K selects the corresponding chain-by-K artifact before
  inference. Never convert slider seconds to blocks or mask a larger artifact.
- A served request uses fixed actions `k=0...K-1` and targets `h+1...h+K`. Persist selected
  K, artifact identity, `(h, hash(h))`, selected action, and intended target. Use the
  simplest explicit chain-by-K artifact mapping; add no plugin, registry, research-sweep
  UI, or other serving machinery.
- Each `(chain, K)` cell gets its own independently trained K-wide output head. Within
  each chain, use one fixed approved LSTM configuration across K under the same paired
  protocol. Do not mask a max-K model or run per-K HPO.
- Pair every K within a chain on the common issue-47-eligible origin intersection with
  complete support through `K_max=200`, keyed by
  `(content_bound_corpus_id, chain_id, block_number)`. Use the same features, context,
  roles, metric definitions, compute/checkpoint/stopping rule, and one ML seed across K.
  Keep chain counts separate.
- Decision 1 remains unchanged: sealed exhaustive testing scores every common eligible
  origin exactly once in every predeclared named range with equal block-opportunity
  weight and no Poisson arrivals, random starts, or repeated replay.
- For every K, report the later-approved exact immediate comparison, K-specific hindsight
  opportunity and oracle gap/regret, captured-opportunity and action diagnostics,
  parameter count, and realized `h -> h+K` elapsed time by chain/regime. Larger K
  mechanically enlarges the oracle opportunity set; raw savings alone cannot be
  presented as forecasting skill. `K=200` is a block-opportunity horizon, not equal
  seconds, inclusion, or actual execution.
- Testing cannot select a visually best K; `K=5` remains primary. Complete all 30 cells
  or revisit scope before outcome inspection rather than truncate the matrix mid-sweep.
- Execute the sweep in a dedicated downstream Wayfinder task and do not multiply issue
  50's structural-ablation matrix. Never use the stale `codex/fast-ab-training` branch
  or obsolete configurations.
- At execution time, use only the executor explicitly approved by the accelerator-
  placement route: ordinary main if acceleration is rejected or not yet approved; or the
  later reconstructed, parity-proved, materially faster executor if issues 55, 56, 40,
  and 57 approve it. Resource authorization assumes no unproved speedup.
- If an execution-only branch wins, pin semantic-main and fast-execution commits, use a
  temporary checkout/worktree only, transfer complete hashed artifacts, and prove main
  code loads and evaluates them independently. If lean main integration wins, use that
  one main path. Maintain no two production paths; executor choice cannot change model
  semantics or configuration.
- Other model families and exact HPO eligibility are deferred. Any later family expansion
  or finalist HPO needs its own approved scope and may not be triggered by favorable
  testing results.
- This decision approves no dates, role sizes, numeric seed value, compute budget, exact
  HPO, metric denominator, secondary window view, other model family, `K>5` serving
  option, or accelerator-placement outcome.

### Decision 3: finite accounting and required paper/TODO diagnostic suite

Edo explicitly approved this complete revised decision on 2026-07-12 and explicitly
retained the auxiliary fee-regression head. Edo later narrowed only the predictive
suite: earliest-argmin accuracy replaces tie-specific diagnostics, and native-unit
regression MAE is removed. The wording below incorporates both corrections:

- For every eligible origin `i`, let `f[i,k]` be the raw integer chain-native target base
  fee per gas at `h[i]+1+k`, and let `p[i]` be the selected action. Define
  `B[i]=f[i,0]` (immediate-k0 reference), `R[i]=f[i,p[i]]` (selected target),
  `O[i]=min_k f[i,k]` (hindsight best within K), `S[i]=B[i]-R[i]` (savings),
  `G[i]=B[i]-O[i]` (hindsight opportunity), and `Q[i]=R[i]-O[i]` (hindsight
  regret). Preserve `S[i]+Q[i]=G[i]` exactly.
- The canonical primary economic surface, computed separately per chain/K/named range
  over every eligible origin once, is:
  - `finite_target_base_fee_per_gas_savings_ratio_vs_immediate_k0 = sum(S)/sum(B)`;
  - `finite_target_base_fee_per_gas_hindsight_opportunity_ratio_vs_immediate_k0 = sum(G)/sum(B)`;
  - `finite_target_base_fee_per_gas_hindsight_regret_ratio_vs_immediate_k0 = sum(Q)/sum(B)`;
  - `signed_captured_hindsight_opportunity_ratio = sum(S)/sum(G)` when `sum(G)>0`.
- Publish every numerator, denominator, eligible-origin count, chain, K, and range. A zero
  denominator is undefined with raw values retained. Combine disjoint windows by adding
  numerators and denominators, never by averaging window ratios. Never pool currencies
  across chains. These are exact finite-window descriptive ratios, not expectations,
  long-run spend, transaction cost, inclusion, execution, or generic profit.
- The required secondary paper-alignment economic views are:
  - `mean_origin_target_base_fee_per_gas_savings_fraction_vs_immediate_k0 = mean(S[i]/B[i])`
    over origins with `B[i]>0`;
  - `mean_origin_selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_K = mean(Q[i]/O[i])`
    over origins with `O[i]>0`;
  - `mean_origin_immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_K = mean(G[i]/O[i])`
    over origins with `O[i]>0`.
- For each mean-origin view, publish the raw sum of defined fractions, finite-origin
  count, zero-denominator exclusion count, and total eligible count; an empty finite
  subset is undefined. Zero-denominator origins remain in every other applicable metric.
  These views use different per-origin denominators, do not satisfy the canonical
  additive identity, and can materially differ from the ratio-of-sums; the savings view
  can reverse sign. They are secondary paper-alignment diagnostics and never share the
  ambiguous legacy name `profit_over_baseline`.
- Required frozen-artifact predictive diagnostics are:
  - `earliest_hindsight_label_accuracy = sum(1[p[i]=o[i]])/N`, where
    `o[i]=min{k:f[i,k]=O[i]}` is the deterministic earliest argmin label under raw
    integer equality;
  - standards-conformant macro-F1 for `p[i]` against earliest-hindsight labels, inheriting
    issue 21's exact class-universe, support, absent-class, and zero-division contract;
  - frozen-checkpoint objective total loss and classification loss on validation and
    testing under exact approved reducers, denominators, units, and checkpoint split.
- The one-off corpus audit found 29 tied `K=5` origins among 13,435,494 post-Granite
  Avalanche origins and none in the audited modern Ethereum and Polygon corpora. Ties
  remain possible, but require no special mode. Selecting a later equal minimum is an
  earliest-label classification miss while raw-fee accounting gives it zero hindsight
  regret. Do not report tie-aware or unique-action metrics, tied/unique counts, or other
  tie-specific counters, tests, or machinery.
- Issue 21 implements `earliest_hindsight_label_accuracy` by summing true positives from
  its approved `MulticlassStatScores` state and dividing by `N`; add no separate Accuracy
  object, wrapper, compatibility mode, or extra test matrix.
- Publish class supports. Do not preserve the current nonstandard target-supported
  macro-F1 for historical continuity. Aggregate frozen-checkpoint losses by their
  contributing examples/elements, never unweighted minibatch means. Training minibatch
  loss while weights change is operational progress, not a fitted-model score. Losses
  remain descriptive across K when output width, weighting, or class distribution differ.
- SPICE retains the auxiliary fee-regression head. The required suite therefore
  includes target-explicit frozen-checkpoint Smooth-L1 loss plus target-explicit
  log-view MAE and MSE, each with exact condition/eligible counts and approved reducers.
  It requires no native-unit regression MAE, inverse-reporting view, or inverse
  provenance merely for scoring; raw chain-native economic accounting remains separate.
- This decision does **not** infer the regression target transform, loss weight,
  scaling/inversion contract, checkpoint rule, or architecture. Those remain
  with their owning decisions. Canonical tracker ownership is: [head existence in issue
  23](https://github.com/edoski/spice/issues/23#issuecomment-4950344149), [loss/scorer
  consequences in issue 21](https://github.com/edoski/spice/issues/21#issuecomment-4950344146),
  and [ablation-protocol consequences in issue
  49](https://github.com/edoski/spice/issues/49#issuecomment-4950344147).
- The compact safety/action surface includes harmful-action rate
  `sum(1[R[i]>B[i]])/N` (equality is not harmful), selected-action counts by K,
  `extra_wait_block_opportunities_vs_immediate_k0=p[i]`, and selected broadcast-trigger
  wait seconds equal to zero for `p[i]=0` and otherwise
  `timestamp(h[i]+p[i])-timestamp(h[i])`. This wait is not target displacement, service
  latency, receipt time, or inclusion delay. Decision 2's realized `h -> h+K` elapsed
  time remains separate.
- Offline structural coverage reports candidate and eligible counts plus issue-47
  exclusion reasons. Missing inference at an eligible offline origin invalidates the
  evaluation; it is never dropped or replaced by k0. Serving remains a separate
  conditional request-to-snapshot-to-inference-to-action-opportunity-to-broadcast-to-
  receipt funnel with every numerator and preceding-stage denominator. It never changes
  offline denominators or proves intended-target inclusion.
- There is no deadline/fallback model metric and no synthetic or whole-block gas
  weighting. A real-gas extension requires a separately predeclared action-invariant
  request-gas vector and still measures counterfactual target-base-fee amount, not actual
  paid cost or inclusion.
- All metrics are single-seed descriptive evidence for the mandatory curve. They produce
  no seed interval or robustness claim and cannot select K or a model from testing.
- Old 300/1,200-window and replay-CI machinery does not survive automatically. Any
  paper/time/window view beyond the three named mean-origin reducers remains for the
  later secondary-view gate.

### Decision 4: standard chronological testing without replacement-data machinery

Edo explicitly approved this simplified decision on 2026-07-12. It supersedes both the
rigid new-suffix-only proposal and the elaborate versioned-reuse proposal:

- Use only the standard chronological roles training, validation, and testing. Testing
  is after training and validation.
- Use one predeclared testing range per chain. Existing or newly acquired chain data is
  acceptable. A fresh suffix is optional and never mandatory.
- Before the official evaluation, freeze eligibility, features/context, model
  configuration, K contract, ML seed, checkpoint, metrics, ranges/windows, and claims.
- Add no prior-exposure registry, disclosure field, protocol-version machinery,
  reused-range taxonomy, or special reuse labels.
- Never discard chain data. Reruns are allowed, especially for correctness fixes and
  reproducibility, without demanding a new suffix.
- Preserve the minimal scientific process rule: training fits, validation selects, and
  testing scores do not select features, hyperparameters, model architecture, K,
  metrics, or emphasized claims.
- If later thesis work necessarily becomes iterative on the same testing range, report
  that methodological limitation once in plain prose. Do not build machinery or require
  replacement data.
- Continue exhaustive once-per-eligible-origin evaluation and all approved accounting.
- This decision chooses no dates, range sizes, or reporting-window layout.

### Decision 5: full-census causal fee-condition view

Edo explicitly approved this decision on 2026-07-12:

- Keep the exhaustive full testing range as the only headline for every
  `K in {2,3,4,5,10,15,30,50,100,200}`. Use no selected evaluation windows.
- Add exactly one secondary condition profile for the primary `K=5` artifact only; do
  not multiply it across the 10-K sweep.
- At each eligible origin `h`, define only two direct decision-time x descriptors:
  - `closed_parent_base_fee_per_gas = base_fee_per_gas[h]`;
  - `signed_one_block_base_fee_log_change = log(base_fee[h]/base_fee[h-1])`.
- Parent `h` is not immediate target `h+1`. Neither x descriptor uses `B[i]`, selected
  `R[i]`, hindsight `O[i]`, or any future target. The second descriptor is the direction
  and magnitude of one observed block step, not volatility. Do not add `abs(r)`, a second
  movement plot, trailing median, rolling dispersion, or another duration unless a later
  distinct thesis question earns it.
- For each chain and descriptor, derive 25th/50th/75th percentile cutpoints from the
  complete common `K_max=200`-eligible testing descriptor values using the empirical
  inverse CDF `q(p)=inf{x:F_N(x)>=p}`. The rule is frozen before scoring; the numeric
  cutpoints describe the test x-distribution and use no model/economic y outcome.
- Assign values to `(-inf,q25]`, `(q25,q50]`, `(q50,q75]`, and `(q75,inf)`. Equal values
  stay together. Do not split ties to force equal counts, merge empty cells, remove
  outliers, or rebalance. Report duplicate cutpoints, empty cells, boundaries, each
  cell's median descriptor, and origin count.
- Every origin appears exactly once for each descriptor. Within each cell aggregate the
  approved raw `sum(S)`, `sum(G)`, `sum(Q)`, and `sum(B)` values. Assert that the four
  cells recombine exactly to the full `K=5` totals.
- Display raw parent-fee bins on a logarithmic x-axis because fee levels are positive and
  strongly skewed; raw fee values still define the cutpoints and are reported in chain-
  native units. Display signed log-change bins on a linear axis with zero visible.
- Economic condition figures plot only the canonical finite savings, hindsight-
  opportunity, and hindsight-regret ratios in separate chain panels. One ML condition
  figure plots `earliest_hindsight_label_accuracy`, matching the paper/TODO accuracy
  question with an additive numerator and denominator.
- Harmful-action rate and exact losses/regression errors are mathematically defined
  within a nonempty cell when their approved denominator exists, but add no condition
  figures without a distinct claim. Macro-F1 is also definable under issue 21 with class
  supports and absent-class rules, but is non-additive and does not recombine; keep it
  full-range only. Keep all frozen-checkpoint losses, regression metrics, and the wider
  approved predictive suite full-range only.
- Label the view `finite-window census stratified by origin-known condition; no
  interval`. It is a descriptive association, not a causal effect, IID sample,
  confidence interval, or training-seed claim.
- Retire representative-window selectors, 300/1,200-block and multi-duration suites,
  future-window descriptors, Poisson/random replay, rolling outcome smoothers,
  outcome-based bulk filters, Pearson correlations, p-values, and replay confidence
  intervals from the final protocol. Preserve their frozen artifacts as archival
  evidence.
- This decision chooses no test date/range size and changes no approved metric formula.

### Decision 6: maximal post-validation testing range per chain

Edo explicitly approved this decision on 2026-07-12 and later amended only its
affordability and frozen-endpoint boundary. The maximal-range requirement remains:

- For each chain, use one maximal contiguous post-validation corpus range remaining
  inside one approved regime as the official testing range.
- Start after validation and the required purge. End at the frozen corpus endpoint.
- Only issue-47-eligible origins with complete target support through `K_max=200` enter
  the testing census. Score every such origin exactly once under Decision 1; retain and
  report all structural exclusions.
- Do not impose a common block count, eligible-origin count, elapsed duration, or other
  cross-chain equalization. Publish each chain's exact start and end, candidate and
  eligible counts, exclusion counts by approved reason, and elapsed span.
- The corpus snapshot may contain existing or separately approved newly acquired data.
  After any approved one-time suffix acquisition, freeze exactly one endpoint per chain
  before official scoring. Later acquisition never auto-appends to a frozen test.
- Before official outcomes open, first calculate exact origin and batch counts without
  inference. If the final approved executor lacks proved throughput, Issue 49 may freeze
  one small metrics-blind contiguous-prefix preflight for the final artifact/input
  shapes. Persist only elapsed throughput, completion/failure, and the minimum memory or
  resource facts needed to project the complete matrix.
- The preflight computes, persists, publishes, and inspects no decoded action, loss,
  accuracy, economic metric, harmful-action rate, prediction, or plot. It cannot select
  a model, endpoint, or range. Add no profiler, sweep, adaptive probe, evaluator-level
  parallelism, or reusable preflight framework.
- If the projected complete maximal-range matrix fits the frozen budget, run official
  exhaustive scoring once. If it does not, stop before any official testing outcome is
  opened and return to Edo for one predeclared cap amendment. Never score a partial
  official range, inspect results, and then truncate. No numeric testing cap is approved.
- Executor placement and concurrency are downstream concerns. They may assign complete
  artifact-evaluation jobs independently, but cannot change ranges, origins, metrics,
  reducers, or results.
- Issues 47 and 49 supply the upstream eligibility, purge, regime, training/validation,
  resource, and stopping inputs needed to calculate exact endpoints. This decision does
  not choose those upstream values or authorize testing before they freeze.

### Decision 7: narrow validation-only leanness tolerance

Edo explicitly approved this decision on 2026-07-12:

- Apply this rule only at the primary `K=5`, and only when a later owning ticket
  explicitly predeclares both a materially leaner candidate and its more complex
  reference before validation.
- On identical eligible validation origins, compute
  `C = sum(S)/sum(G)` when `sum(G)>0`. The lean candidate passes the economic margin
  only when `C_lean >= C_complex - 0.05` separately for every chain and every ML
  training seed approved by issue 49. The margin is five absolute percentage points of
  captured hindsight opportunity, not five percent of the complex model's score.
- The lean candidate's harmful-action rate may not exceed the reference's rate in any
  required chain/seed cell. All previously approved causal-correctness, coverage, and
  serving-safety gates remain outside the tradeoff.
- Testing cannot select either candidate. An undefined or failed chain/seed cell cannot
  justify simplification, and results may not be pooled or averaged to hide one.
- This is a deterministic validation rule for the declared finite validation evidence,
  not statistical equivalence, an IID claim, or a testing result. Publish the raw
  numerators, denominators, counts, and equivalent difference in canonical savings-ratio
  points.
- The rule is not general simplification authority, creates no obligation to search for
  or adopt a leaner candidate, and has no effect when no candidate/reference pair is
  explicitly declared by its owning ticket.
- It does not reopen or remove any fixed choice, including the auxiliary regression
  head, K grid, serving horizons, or accelerator-parity boundary. Issue 49 retains
  ownership of candidates, configurations, seed values/count, common validation origins,
  and compute/stopping protocol.

## Final approval

Edo explicitly approved the compact complete-contract recap on 2026-07-12. The
[single resolution comment](https://github.com/edoski/spice/issues/48#issuecomment-4950650999)
records the complete contract, and the issue is closed as completed. No issue-48 owner
gate remains.

No later gate may reinterpret target opportunity as transaction inclusion or actual
execution, introduce generic `profit`, add an internal-test role, or reopen Decision 1
without explicit owner correction.
