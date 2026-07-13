# Legacy window-selector audit

Status: independent research input for
[issue 48](https://github.com/edoski/spice/issues/48). It records no owner decision.

## Finding

The old evaluation-window selectors are not needed under the approved exhaustive
test-range census. Retaining them would change the unit from an eligible origin to a
deterministically chosen period, omit most origins, and preserve arbitrary duration and
replay machinery. The lean replacement is to score every eligible origin once, attach
two past-only operating-condition descriptors to that same origin, and aggregate the
already approved additive metric components over small display strata. Fixed
contiguous 300/1,200-block or 4--72-hour windows are not required.

This is a descriptive association: performance *conditional on an origin-available fee
state*. It is not evidence that fee level or volatility causes performance. Conditional
forecast evaluation is naturally stated in information available at the forecast date
([Giacomini and White 2006](https://doi.org/10.1111/j.1468-0262.2006.00718.x)).

## What the old routes actually did

The local Obsidian `TODO.md` records three increasingly systematic but still
selected-period views in its 15/06, 22/06, 29/06, and 06/07 sections:

The 08/06 figures are a different axis: they plot horizon-specific loss,
classification, regression, and legacy economic results against prediction-window
seconds
(economic figure (`benchmarks/figures/delay_degradation_completed_profit_lstm_only_fig6_style.png`),
classification figure (`benchmarks/figures/delay_degradation_completed_classification_metrics_lstm_only_fig6_style.png`),
regression figure (`benchmarks/figures/delay_degradation_completed_fee_regression_metrics_lstm_only_fig6_style.png`)).
They support the separately approved K-sweep investigation, but define no
fee/volatility window selector and contribute no reason to retain one here.

- The first plot compared five hand-labelled Ethereum periods. The next edge-case scan
  made hourly-start 4, 6, 8, 12, 16, 24, 36, 48, and 72 hour candidates, labelled each
  duration's bottom/top fee and volatility deciles, and selected up to six most extreme
  non-overlapping periods per duration/class
  ([scanner](../../../benchmarks/scripts/scan_edge_case_windows.py#L189-L299)). This
  deliberately displays tails, not the ordinary post-training distribution. The
  class-only figures visibly omit the middle of both axes
  (fee figure (`benchmarks/figures/ethereum_pectra_jun20_lstm_profit_vs_base_fee_class_only.png`),
  volatility figure (`benchmarks/figures/ethereum_pectra_jun20_lstm_profit_vs_base_fee_volatility_class_only.png`)).
- The wall-clock quartile route formed the same nine duration families at one-hour
  strides, ranked median fee and log-change volatility separately within each duration,
  and picked three positions inside every metric/quartile: 216 source rows per chain
  ([construction](../../../benchmarks/scripts/scan_wall_clock_quartile_windows.py#L189-L224),
  [selection](../../../benchmarks/scripts/scan_wall_clock_quartile_windows.py#L251-L307)).
  Non-overlap is enforced only inside one duration/metric/quartile group, not across
  groups or durations. Exact-ID merging cannot remove partial overlaps
  ([merge](../../../benchmarks/scripts/scan_wall_clock_quartile_windows.py#L309-L335),
  [suite writer](../../../benchmarks/scripts/write_evaluation_suite_from_window_csv.py#L19-L68)).
- The 300/1,200 route did **not** enumerate every possible contiguous start. It tiled the
  post-cutoff rows at a stride equal to the block count, discarded any numerically
  gapped tile, ranked the resulting disjoint tiles by median fee and volatility, then
  selected 27 rank-spaced tiles in each of four quartiles for each axis
  ([tile construction](../../../benchmarks/scripts/scan_block_count_quartile_windows.py#L75-L126),
  [selection](../../../benchmarks/scripts/scan_block_count_quartile_windows.py#L129-L193)).
  Fee tiles are selected first; volatility selection moves to the nearest still-unused
  tile. The result is 216 distinct tiles per chain, not a random sample and not a full
  range.

The selected 1,200-block set is only 216 of 1,158 candidate tiles on Ethereum, 216 of
5,630 on Polygon, and 216 of 9,757 on Avalanche: about 18.7%, 3.8%, and 2.2%. For 300
blocks the shares are about 4.7%, 1.0%, and 0.6%. The selected widths also represent
very different elapsed exposure. Their median elapsed times are about 4.0 hours,
40 minutes, and 20.9 minutes at 1,200 blocks, and 60, 10, and 5.3 minutes at 300 blocks
for Ethereum, Polygon, and Avalanche respectively. These counts and times come directly
from the tracked selected/candidate CSVs under
`evaluation_window_scans`.

The wall-clock scanners have a more fundamental incompatibility with the approved
origin identity: they drop all but the first row at a duplicate whole-second timestamp
([load path](../../../benchmarks/scripts/scan_wall_clock_quartile_windows.py#L114-L135));
the edge-case scanner does the same
([load path](../../../benchmarks/scripts/scan_edge_case_windows.py#L106-L127)). Same-second
Avalanche blocks are distinct origins by block number, so those scanners cannot be
reused for a block-origin census.

## Selection, outcome use, and aggregation

Ranking windows by fee/volatility alone is not model-outcome cherry-picking. It is still
purposeful case selection: it supports a statement about those selected fee regimes,
not the complete test range. The legacy descriptors also use the full selected period,
including fees after early origins. They can characterize a realized period after the
fact, but cannot support an origin-time claim such as "the model works better when
currently volatile." The future fees also help define hindsight opportunity, so their
association with economic outcomes is partly mechanical.

One renderer does select on the model outcome. Its Polygon volatility "bulk" view drops
rows outside a 5-IQR fence computed from legacy `profit_over_baseline`
([code](../../../benchmarks/scripts/render_lstm_block_count_quartile_results.py#L361-L390)).
The tracked outputs exclude two 1,200-block rows and three 300-block rows. That route is
outcome-conditioned and must not survive. The fee-level bulk view drops ten Polygon
rows at each width from an x-only log-fee fence
([code](../../../benchmarks/scripts/render_lstm_block_count_quartile_results.py#L321-L358));
it is not y-selected, but it still hides census extremes and is unnecessary when chain
facets and a log x-axis are available. Searching for outcome-optimizing cutpoints is a
known source of serious bias ([Altman et al. 1994](https://doi.org/10.1093/jnci/86.11.829)).

The selected windows were then evaluated with a second sampling layer:

- Wall-clock windows of 4--72 hours supplied only a two-hour random Poisson replay per
  repetition. The x descriptor summarizes the outer period while y summarizes sampled
  inner episodes
  ([benchmark](../../../src/spice/conf/benchmark/lstm_36s_wall_clock_quartile_eval.yaml),
  [evaluator](../../../src/spice/conf/evaluator/poisson_replay.yaml)).
- A 300/1,200 suite item contains exactly 300/1,200 origins, so the block replay's only
  possible start is zero. Its repetitions merely give origins seeded Poisson
  multiplicities
  ([benchmarks](../../../src/spice/conf/benchmark/lstm_36s_block_count_quartile_eval.yaml),
  [300 benchmark](../../../src/spice/conf/benchmark/lstm_36s_block300_quartile_eval.yaml),
  [evaluators](../../../src/spice/conf/evaluator)). This is the issue-53 audit result:
  the outputs are sampled-event evidence, not fixed-K/exhaustive evidence
  ([resolution](../fixed-block-comparability-and-exhaustive-replay.md#old-300--and-1200-block-evidence)).

The renderers use the mean and population standard deviation across replay repetitions
for each point, attach `1.96 * sd / sqrt(repetitions)` Monte Carlo whiskers, then compute
ordinary Pearson p-values and separate normal intervals across the selected window
means
([join and point interval](../../../benchmarks/scripts/render_lstm_block_count_quartile_results.py#L174-L218),
 [window reducer](../../../benchmarks/scripts/render_lstm_block_count_quartile_results.py#L745-L833)).
Those intervals do not measure temporal, regime, or training-seed uncertainty. The old
duration choice is visibly material: Avalanche's selected-window volatility correlation
changes from `+0.219` at 1,200 blocks to `-0.095` at 300 blocks
(1,200 report (`benchmarks/exports/lstm_36s_block_count_quartile_report.md`),
 300 report (`benchmarks/exports/lstm_36s_block300_quartile_report.md`)). This is
evidence that the aggregation scale changes the old picture, not evidence for choosing
either scale.

## Lean replacement

Keep the approved one testing range per chain and score every eligible origin once. For
origin `h`, attach:

```text
fee_level(h) = raw chain-native base_fee_per_gas at closed parent h

fee_change_volatility_L(h)
  = declared standard deviation of log(F_j / F_{j-1})
    over one fixed trailing block span ending at h
```

Fee level needs no extra duration. Volatility necessarily needs a declared lookback,
formula, and degrees-of-freedom convention. Use only block-number-ordered history known
at `h`, preserving duplicate timestamps. The lean candidate is to reuse issue 47's
approved context span `H` when it contains enough fee transitions; otherwise issue 48
must freeze one symbolic trailing block span `L` before outcomes. This is a descriptor
lookback, not an evaluation window, reporting role, action horizon, or wall-clock
duration. It enters no model input unless separately approved.

For readable ratio-of-sums plots, freeze a small set of descriptor bins from validation
before opening testing, then apply those numeric boundaries unchanged to testing.
Quartiles are the smallest familiar candidate. Every testing origin remains in exactly
one fee band and one volatility band; outer bands are open-ended, counts may differ, and
no row is sampled or dropped. For each chain/K/band publish the approved raw additive
components, denominator, and eligible count, and derive the approved ratio from those
sums. Plot one point per band at its observed median descriptor value. Keep chains in
separate facets and use a log axis for fee level. Do not add a confidence ribbon or
Pearson p-value to this exact finite census.

Bins are a display reducer, not a required scientific estimand. Continuous-variable
categorization loses information and outcome-derived boundaries bias results
([Royston, Altman, and Sauerbrei 2006](https://doi.org/10.1002/sim.2331)); formal
binscatter itself has tuning and inference choices
([Cattaneo et al. 2024](https://doi.org/10.1257/aer.20221576)). Four
validation-frozen bands are justified here only by readability and additive accounting.
Do not call them evidence of a threshold. A smoother, rolling outcome curve, many bins,
or two-dimensional fee-by-volatility grid adds choices without distinct thesis value.

Safe interpretation is: "Within this complete finite test census, the approved metric
had these values across predeclared, origin-available fee-state bands." Unsafe
interpretations include causal effects, future deployment guarantees, selected extreme
regimes, independent-bin inference, or a reason to change K/model/claims after testing.

## Clean-break consequence

If this route is approved, the active clean evaluator needs no selector abstraction.
Retire rather than generalize:

- the edge-case, wall-clock-quartile, and block-count-quartile scanners plus
  `write_evaluation_suite_from_window_csv.py`;
- their `*edge_case*`, `*wall_clock_quartile*`, `*block_count_quartile*`, and
  `*block300_quartile*` evaluation/benchmark configs;
- their dedicated renderers, selected-window Pearson/CI summaries, class tags, bulk
  filters, and outlier exports;
- block/time Poisson adapters, replay runner/result/window-metric catalog, configs,
  registry branches, and focused tests once no separately approved request-arrival
  estimand remains. The new Decision-3 accounting should be implemented from its raw
  per-origin components, not kept behind legacy metric names.

The tracked frozen CSVs, figures, SQLite result index, and evidence manifest remain
archival provenance; do not delete or reinterpret them. Raw block-number/base-fee rows,
chain faceting, log-scale fee display, and the mathematical idea of trailing log-change
volatility are reusable. Implement the replacement as one census evaluator and one
small descriptive reducer/plot path, not a new window framework.
