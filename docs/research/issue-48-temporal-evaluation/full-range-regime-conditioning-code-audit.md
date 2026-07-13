# Full-range regime-conditioning code audit

Date: 2026-07-12. Status: read-only code and frozen-artifact audit. No production
module, configuration, test, corpus, artifact, database, export, figure, or Obsidian
note was changed.

## Recommendation

Use the exhaustive full-range census as the only headline, then derive two descriptive
views from every scored origin: one by causal fee level and one by causal fee volatility.
Use deterministic within-chain bins, not selected evaluation windows. This fully replaces
the old 300/1,200-block, multi-duration, fee-quartile, volatility-quartile, edge-case, and
Poisson window-selection machinery for the final protocol.

The conditioning window should be the model's already-approved visible block context
`C`, once its numeric value is chosen. This adds no second duration hyperparameter and
keeps one descriptor definition across every K within a chain. For origin `h`, use only
closed parents in `h-C+1 ... h`:

```text
fee_level[h] = median(raw_base_fee_per_gas[h-C+1 : h+1])

volatility[h] = sample_std(
    log(raw_base_fee_per_gas[b] / raw_base_fee_per_gas[b-1])
    for b in h-C+2 ... h
)
```

This requires `C >= 3` and positive raw base fees. Convert fee level to gwei only for
display. The volatility is dimensionless. Block count is preferable to wall time because
Issue 47 already fixes visible context by block number and requires its realized UTC span
to be descriptive, not membership-defining
([Issue 47 Decision 4](../issue-47/issue-47-owner-decisions.md#decision-4--direct-block-count-context-semantics)).
Using K itself as the trailing width would make the x-axis change across the K sweep;
using `K_max=200` would introduce an arbitrary reporting context when `C` already owns
the causal state.

For each chain, calculate descriptor ranks once on the common `K_max=200` eligible
testing-origin intersection. Split the ranks into four deterministic equal-count bins,
with block number as the tie-break. Reuse those memberships for every K. For each bin,
plot the median descriptor on x and the approved ratio of raw sums `sum(S)/sum(B)` on y;
also publish `sum(S)`, `sum(B)`, and origin count. Do the same for approved safety/action
diagnostics. Never average origin ratios or bin ratios to reconstruct the full result.
Use separate chain panels and no cross-chain fee pooling. These are descriptive
conditioned views, with no p-values, confidence intervals, or IID claim.

## Why direct bins replace selected windows

| Route | What it adds | Cost and defect | Verdict |
| --- | --- | --- | --- |
| A. Full range only | Smallest valid headline | Hides whether performance changes with known fee conditions | Valid but less informative |
| B. All-origin causal bins | Fee-level and volatility figures from the same census; every origin remains represented | One rolling descriptor and grouped reducer | Recommended |
| C. Selected fixed windows | Period-level episode points and duration sensitivity | Adds duration, stride, ranking, selection, suite generation, repeated reporting, and period-selection semantics | Keep only if the thesis asks a separate episode-level question |

The old figures do not need separate evaluation runs in principle. The model already
predicts every outer-window origin before replay selection, then the replay adapters
discard or duplicate predictions during accounting
([scoring](../../../src/spice/modeling/scoring.py#L55-L74),
[runner](../../../src/spice/evaluation/temporal_replay_runner.py#L101-L137)). A clean
full-range evaluator can retain one compact row per origin and create all condition plots
without another forward pass.

Selected windows answer a different question: performance in deliberately chosen
episodes. They are not needed to answer "how does performance vary with the fee state
known at decision time?" If a later chapter needs period persistence, aggregate the
already-scored origin ledger into fixed, non-overlapping, chronologically exhaustive
windows. Do not select those windows by fee or volatility.

## What current code computes

The block scanner partitions post-cutoff rows into contiguous fixed-size windows. For
each whole window it computes the median raw base fee and the sample standard deviation
of block-to-block log fee changes, ranks all candidate windows, then selects 27
representatives from each fee or volatility quartile
([block scanner](../../../benchmarks/scripts/scan_block_count_quartile_windows.py#L75-L178)).
The default stride equals the block count, so its candidate windows are non-overlapping.

The wall-clock scanner uses 4-72 hour windows starting hourly, computes the same
whole-window descriptors, ranks them separately by duration, then chooses three
non-overlapping representatives per duration/axis/quartile
([wall-clock scanner](../../../benchmarks/scripts/scan_wall_clock_quartile_windows.py#L155-L296)).
Its candidates overlap heavily. It also filters non-positive fees and executes
`unique(subset=["timestamp"], keep="first")`, which silently deletes valid
same-timestamp blocks
([load path](../../../benchmarks/scripts/scan_wall_clock_quartile_windows.py#L114-L135)).
That conflicts with Issue 47's block-number identity and valid-equal-timestamp contract.

Both descriptors use rows inside the evaluated period. For an origin near a window's
start, most descriptor rows are future rows; target rows may also contribute. This is
not model-input leakage because the values are added after inference, but it is
future/outcome-conditioned period selection. It cannot be described as a causal state
known at origin `h`.

A hand fixture is enough to expose the distinction. Give two origins the identical
known history `[10, 10, 10]`. Let one future path be `[10, 10]` and the other
`[100, 100]`. Both causal descriptors are median `10` and volatility `0`. A scanner
window `[h, h+2]` instead sees `[10,10,10]` versus `[10,100,100]`, changing both the
median and volatility solely because the unseen future differs. No executable prototype
is needed for this arithmetic.

The renderers join only selected scan rows to aggregate benchmark results. Base-fee
plots use fee-selected windows and volatility plots use volatility-selected windows;
their y values come from Poisson run summaries, while whiskers are derived from replay
repetitions
([renderer join](../../../benchmarks/scripts/render_lstm_block_count_quartile_results.py#L168-L231),
[renderer plots](../../../benchmarks/scripts/render_lstm_block_count_quartile_results.py#L466-L576)).
The frozen manifest preserves these outputs as archival evidence
([manifest](../spice-pre-break-evidence-manifest.tsv)); they should not constrain the
new protocol.

## Clean-break implementation consequences

Replace the replay selector seam with one exhaustive evaluator that realizes positions
`0 ... N-1` exactly once. Its config needs only an evaluator id; range membership remains
owned by the existing evaluation-window selection, and K remains owned by the trained
artifact/action width. Delete Poisson rate, repetition, seed, random-start, and
`window_metrics` concepts from final evaluation. Rename event counts to eligible/scored
origin counts. Full support through K makes deadline overflow and post-window fallback
invalid rather than measurable outcomes.

The current store retains only clipped float32 log fees
([feature series](../../../src/spice/features/core.py#L299-L325)), and current accounting
reconstructs economic values with `exp`
([accounting](../../../src/spice/evaluation/temporal_accounting.py#L85-L130)). The clean
evaluator needs raw integer `base_fee_per_gas` for exact B/R/O/S/G/Q accounting and ties.
The conditioned descriptors should also use that raw series, not scaled model features.

Current summaries preserve only aggregates and replay runs; benchmark collections omit
per-origin decisions
([runtime summary](../../../src/spice/modeling/results.py#L198-L282),
[collection record](../../../src/spice/benchmarks/result_records.py#L39-L85)). Direct
condition plots therefore require either a compact per-origin columnar result or
predeclared bin accumulators inside evaluation. A small Parquet sidecar per chain/K is
the more useful clean surface: origin identity, descriptor values, selected k, B/R/O,
S/G/Q, waits, tie flags, and required diagnostics. Keep JSON summaries aggregate-only.

Once the replacement works, remove the active Poisson modules, replay config models and
YAML, replay-run/window-summary reducers, selector tests, and Poisson-specific docs.
Remove the active quartile/edge scanner, suite-writer, selected-window benchmark configs,
and old renderers from the final pipeline. Replace them with lean tests for: all eligible
origins scored once; fixed-K target mapping; exact raw-integer accounting/ties; causal
descriptor bounds ending at h; stable common-origin bin membership; and bin raw sums
recombining to the full-range sums. Preserve the hash-frozen SQLite/CSV/figure assets as
archive data, not executable protocol machinery.
