# Full-census fee-condition view methodology

Status: primary-source methodology review for Issue 48. This note changes no
production code, tracker state, data, artifact, or protocol decision.

## Decision

The full eligible testing range is sufficient for the primary result. It does not
show whether the result is concentrated in particular fee conditions, so one small
secondary view has thesis value:

- keep the full-range census as the only headline;
- for the primary `K=5` condition only, show performance against trailing fee level
  and trailing base-fee log-change dispersion;
- construct both descriptors at every origin from information available through its
  closed parent;
- group every eligible origin into four chain-specific value-quantile bins per
  descriptor and aggregate the approved raw accounting inside each bin;
- use no selected evaluation windows, extra durations, rolling outcome windows,
  smoothers, intervals, or hypothesis tests.

This preserves the useful idea in the Obsidian TODO—describe results across fee level
and fee variability—without its representative-window selection machinery. It is a
descriptive partition of the same census, not another test or dataset.

## Why the full range alone is not the whole story

The full-range result answers the main question: what did the fixed artifact do over
all eligible block opportunities in this testing range? Nothing else is required to
make that claim.

A condition view answers a narrower question: where inside this observed range were
savings larger, smaller, or harmful? Conditional forecast evaluation is useful when
current information may explain differences hidden by an unconditional average;
Giacomini and White formulate that distinction explicitly in terms of information
available at the forecast date ([Giacomini and White
2006](https://doi.org/10.1111/j.1468-0262.2006.00718.x)). This is relevant to SPICE
because fee level and recent fee changes are available when the action is selected.

The view remains optional. If the thesis makes only an overall finite-period claim,
full-range-only reporting is honest. If it discusses when waiting is economically
useful, the two-axis condition profile earns its small cost.

## Smallest sound construction

Let `h` be an eligible closed-parent origin, `f_t` the positive raw base fee at block
`t`, and `C` the already-approved visible model context length. Define

```text
level(h) = median(f_t : t = h-C+1, ..., h)

r_t = log(f_t / f_(t-1))
dispersion(h) = population_sd(r_t : t = h-C+2, ..., h)
```

Reusing `C` is methodologically sound for this purpose. Both descriptors are known at
`h`; no target `h+1...h+K` enters them. `C` already defines the model's causal local
state, so it avoids a new reporting-width choice. The second descriptor should be
called **trailing per-block base-fee log-change dispersion**, not generic volatility
or volatility per hour. Realized-volatility work likewise treats the sampling
interval and observation frequency as part of the measure, rather than an incidental
plot setting ([Andersen et al.
2003](https://doi.org/10.1111/1468-0262.00418)).

Use separate panels and thresholds per chain. Show the realized UTC span of `C`
blocks descriptively because the same block count can cover different elapsed time by
chain and period. Do not pool chains into one regression or correlation.

For each chain and descriptor:

1. Calculate the descriptor for every common eligible testing origin.
2. Calculate the 25th, 50th, and 75th percentile values across those origins using one
   fixed quantile convention.
3. Assign every origin to one of the four value intervals. Keep identical descriptor
   values together rather than splitting ties merely to force equal counts.
4. Plot each cell at its median descriptor value. Report its cutpoints and origin
   count.

Quantile bins are a readable visualization of a large bivariate dataset; their
formal role as a nonparametric partitioning display is developed by Cattaneo et al.
([2024](https://doi.org/10.1257/aer.20221576)). Four bins are enough here. More bins or
a fitted smoother add resolution, tuning choices, and tail instability without a
separate undergraduate-thesis claim.

The main plot should use the approved target-base-fee savings name, not the old
`profit_over_baseline` label. A compact companion table should include opportunity
and regret too, because higher dispersion can mechanically create more hindsight
opportunity; larger savings alone do not establish better forecasting skill.

## Exact aggregation

For bin `b`, retain the approved per-origin raw values `S_i`, `G_i`, `Q_i`, and `B_i`
and calculate

```text
savings_b     = sum(i in b, S_i) / sum(i in b, B_i)
opportunity_b = sum(i in b, G_i) / sum(i in b, B_i)
regret_b      = sum(i in b, Q_i) / sum(i in b, B_i)
captured_b    = sum(i in b, S_i) / sum(i in b, G_i)  if sum G_i > 0
```

Publish each numerator, denominator, and origin count. `savings_b + regret_b =
opportunity_b` remains exact. The full-range result is recomputed from all origins, or
equivalently from the sums of the four bin numerators and denominators. Never average
the four ratios. Never pool currencies across chains.

This distinction matters because a ratio of sums is a baseline-fee-weighted mean of
per-origin fractions, while an ordinary scatter or binscatter of `S_i/B_i` targets an
equal-origin mean of fractions. Gneiting shows more generally why the evaluation
criterion and target functional must be fixed together rather than swapped after
results are visible ([Gneiting
2011](https://doi.org/10.1198/jasa.2011.r10138)). The approved SPICE ratio-of-sums
contract decides the reducer here.

## Comparison of the candidate layouts

| Layout | What it adds | Main problem | Decision |
|---|---|---|---|
| Representative windows selected by fee/dispersion | A small sample of regimes | Redundant after a census; drops origins and gives the selector an implicit weighting scheme | Delete |
| Fixed 300/1,200-block or multi-hour windows | Episode-level results | Width and start are extra estimand choices; multiple overlapping widths reuse origins and cannot be read as replicates | Delete |
| Rolling outcome summaries over time | A local performance path | Heavy overlap, another width, and visually smoothed dependence; justified only for an explicit instability claim | Delete |
| Raw per-origin scatter | Direct use of all origins | Millions of dependent, overplotted points; the natural per-origin y-ratio conflicts with the approved ratio of sums | Delete |
| Kernel/LOESS smoother | A continuous conditional curve | Bandwidth and boundary behavior add choices; still must be redesigned as a local ratio of sums | Delete |
| Four all-origin condition bins | Readable heterogeneity with complete coverage | Coarse and descriptive, which is acceptable here | Keep as the sole secondary view |
| Full range only | Leanest correct headline | Can hide condition-specific concentration | Keep as primary; acceptable alone if no heterogeneity claim |

Sampling selected windows would be useful only if scoring the census were infeasible.
Finite-population sampling requires a design and known inclusion probabilities to
recover population totals under unequal selection
([Horvitz and Thompson 1952](https://doi.org/10.1080/01621459.1952.10483446)). The
approved exhaustive replay already observes the finite population, so a purposive
"representative" subset loses information without buying computational necessity.

Rolling local performance can be informative when temporal instability itself is the
research question; Giacomini and Rossi show why a local performance path can reveal
information lost by a global average ([2010](https://doi.org/10.1002/jae.1177)). It is
not free evidence. It introduces a window width and correlated overlap. Issue 48 does
not need that separate claim.

## Selection and interpretation limits

The TODO's window median and dispersion use the complete realized fee path inside each
evaluation window. Relative to an origin near the window start, much of that condition
is future information. Such a plot can describe completed periods, but it cannot mean
"performance given the state known when acting." The trailing-`C` construction fixes
that mismatch.

The stronger failure is choosing or removing windows after seeing economic outcomes.
That changes the displayed population toward favorable or "clean" results. White's
data-snooping analysis explains why searching specifications on the same outcomes can
create apparent predictive superiority
([White 2000](https://doi.org/10.1111/1468-0262.00152)). Freeze the two descriptors,
their formulas, the quartile rule, and `K=5` emphasis before the official scoring run;
no registry or extra machinery is needed.

Origin-known conditioning still does not make the relationship causal. Fee conditions,
calendar time, load, protocol state, available hindsight opportunity, and model error
move together. Wording should be "savings were larger in high-dispersion origins," not
"volatility caused savings." The bins are also not independent replicates. Adjacent
origins share context and up to `K-1` target blocks, and forecast-comparison methods
explicitly allow serially correlated losses
([Diebold and Mariano 1995](https://doi.org/10.1080/07350015.1995.10524599)). Under the
approved finite-census interpretation, show no IID confidence interval, Pearson
`p`-value, or trend significance test.

Use these labels:

- full range: `finite-window census; no interval`;
- condition cells: `finite-window census stratified by origin-known condition; no interval`.

They are descriptive partitions, not repeated tests, training-seed evidence, causal
effects, or claims about future periods.

## Blocks versus wall clock

Use `C` blocks. This matches the block-origin estimand, uses the exact causal history
already required by the model, and adds no duration. Its physical span differs across
chains, so keep chain panels separate and report the realized span.

A trailing wall-clock descriptor could be valid if the thesis instead asked about
conditions over the preceding hour or day. It would have to end at `h`, use only closed
blocks, declare a duration and boundary rule, and cope with varying block counts and
coarse timestamp ties. It would change only the x descriptor; it would not justify
wall-clock weighting of the y outcome. No such extra market-time claim is needed here.

The old 4--72-hour, 300-block, and 1,200-block matrices therefore answer neither the
approved headline nor the smallest conditional question. Archive their artifacts, but
remove their selectors, random starts, Poisson repeats, replay intervals, Pearson
tests, outcome-filtered "bulk" plots, and duration matrix from the final protocol.
