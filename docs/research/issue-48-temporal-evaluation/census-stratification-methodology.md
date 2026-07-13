# Census stratification methodology

Status: independent research input for
[issue 48](https://github.com/edoski/spice/issues/48). It approves no owner
choice, numeric lookback, bin count, or plot suite.

## Recommendation

Retire evaluation-window selection. The approved full testing range is already
the finite population of interest: score every eligible origin once, then attach
decision-time descriptors to those same origins. Selecting “representative”
contiguous windows would change the population and its weights; it adds no
sampling benefit to a census. A census removes sampling error for that finite
range, but not eligibility, implementation, model, or future-period error
([US Census Bureau methodology](https://www.census.gov/programs-surveys/sas/technical-documentation/methodology.html#reliability-of-the-estimates)).

Use two secondary descriptors, separately by chain:

1. **Fee level:** the positive raw fee scalar that the approved issue-46/47
   contract says is available at origin `h`, displayed on a log axis. Do not use
   a target fee that is unknown at `h` merely to make chains look symmetric.
2. **Trailing block-to-block fee variability:** the exact retained causal
   volatility feature if one survives feature selection. Otherwise approve one
   trailing block lookback `L_vol` and define, for decision-time fee observations
   `z`,

   ```text
   d_t = log(z_t) - log(z_(t-1))
   v_h = sample_sd(d_(h-L_vol+1), ..., d_h).
   ```

   Freeze the scalar source, transform, lookback, endpoint convention, degrees
   of freedom, minimum history, and zero/invalid handling before testing.
   Issue 47 uses `C` for visible model-context rows and `H` for extra feature
   warm-up; `H` is not a volatility horizon. Reusing a retained feature
   definition is leanest. If none survives, the `C-1` log changes wholly inside
   `C` may be considered for `L_vol`, but that requires approval rather than
   inference.

“Volatility” is not window-free. Methodology distinguishes variability over a
fixed interval from conditional or instantaneous volatility, and realized
volatility is built from changes over a declared aggregation horizon
([Andersen, Bollerslev, Diebold, and Labys](https://www.nber.org/papers/w8160)).
Here the honest name is therefore
`trailing_L_vol_block_log_fee_change_sd`. It is per-block variability, not
per-second or annualized volatility. Report the realized seconds spanned by its
trailing block lookback by chain/regime. This descriptor lookback selects no
evaluation origin and is not a 300/1,200-block evaluation window.

For readable canonical ratio-of-sums plots, use a small outcome-blind partition
of each continuous descriptor. The lean candidate is a fixed count of
chain-specific quantile bins whose rule and edges are frozen from validation,
with unbounded outer bins so every testing origin is assigned exactly once. For
each bin `b`, recompute the approved additive metric from its raw components:

```text
savings_ratio_b     = sum[i in b] S_i / sum[i in b] B_i
opportunity_ratio_b = sum[i in b] G_i / sum[i in b] B_i
captured_ratio_b    = sum[i in b] S_i / sum[i in b] G_i, if sum G_i > 0
```

Show cutpoints, descriptor range/median, every numerator and denominator,
eligible count, and undefined bins. Never average origin ratios and label the
result as a ratio of sums. The opportunity and captured panels are useful
companions to savings because they separate a larger hindsight opportunity set
from the model's captured share. They add no new metric.

Bins are presentation strata, not selectors. They lose continuous detail, so
retain the continuous descriptor in the result data and do not treat steps at
bin edges as real thresholds. Statistical guidance warns that categorizing
continuous variables loses information and that outcome-derived cutpoints bias
associations; it also calls for reporting cutpoints and counts
([Royston, Altman, and Sauerbrei](https://ora.ox.ac.uk/objects/uuid%3A31fc8902-1644-48a4-b44b-5a3b6c90f6e2),
[STROBE explanation](https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.0040297)).
A fixed LOWESS curve is methodologically possible
([Cleveland 1979](https://doi.org/10.1080/01621459.1979.10481038)), but its span,
degree, robustness iterations, and boundary behavior create extra choices.
Smoothing per-origin fractions also does not produce the canonical ratio of
sums. Transparent fixed bins are leaner here.

## Safe and unsafe conditioning

Safe descriptive conditioning has all of these properties:

- the descriptor uses only information available through origin `h`;
- its definition and the complete display rule are frozen before testing
  outcomes;
- every eligible origin remains in exactly one displayed stratum;
- all strata, raw supports, and denominator failures are shown;
- chains remain separate and only approved metrics appear; and
- captions say “descriptive association in this testing census.”

Unsafe conditioning includes selecting windows, cutpoints, lookbacks, smoothing
spans, or highlighted panels after seeing economic outcomes; removing unfavorable
strata; using centered or forward fee variation as if it were decision-time
context; or treating many overlapping origins as independent replicates. Data
leakage can make ML evidence optimistic
([Kapoor and Narayanan](https://doi.org/10.1016/j.patter.2023.100804)), and fixing
an analysis before outcomes distinguishes testing from post-hoc explanation
([Nosek et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC5856500/)).

Decision-time availability prevents direct future leakage; it does not identify a
causal effect. Fee level and fee variability co-move with calendar time, protocol
state, load, and other market conditions. Even an arbitrarily large observational
census can retain confounding
([Hernan and Robins, *Causal Inference: What If*, ch. 7](https://www.hsph.harvard.edu/miguel-hernan/wp-content/uploads/sites/1268/2024/04/hernanrobins_WhatIf_26apr24.pdf)).
Do not write “volatility caused savings” or “high fees improve the model.”

No confidence ribbon or Pearson `p` value is warranted for this secondary view.
The full-range bin values are exact for the fixed artifact and testing census;
adjacent origins share contexts and K-step targets, and the mandatory horizon
curve has one ML seed. Any future-process interval would need a separately
approved dependence-aware estimand. Counts communicate support, not independence.

## Why the old windows do not survive

The old block scanner ranked candidate windows by median fee and volatility,
then chose evenly spaced representatives within quartiles
([scanner](../../../benchmarks/scripts/scan_block_count_quartile_windows.py)).
The wall-clock scanner tried nine durations and shortlisted extremes
([scanner](../../../benchmarks/scripts/scan_edge_case_windows.py)). The frozen
audit found that Avalanche's volatility association changed from `+0.659` to
`+0.219` to `-0.095` across wall-clock, 1,200-block, and 300-block constructions,
and that an old Polygon “bulk” view filtered on the economic outcome
([audit](../issue-53/chain-regime-results-audit.md)). That sensitivity is direct
evidence that selection geometry was part of the result.

Under exhaustive replay, neither fixed contiguous evaluation windows nor rolling
outcome windows are required. Rolling outcomes repeatedly repackage dependent
origins and invite arbitrary duration choices. Keep a contiguous subperiod only
for a separately predeclared protocol-event question; otherwise delete the
selector, 300/1,200 machinery, representative quartiles, correlation `p` values,
and replay confidence intervals. The resulting protocol is one full-range
headline plus secondary fee-level and trailing-variability descriptions made from
the same complete census.
