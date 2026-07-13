# Current evaluator and frozen-evidence audit

Date: 2026-07-11. Code revision: `b9b9a53f42e3e88855ae5488ffff06d3d334fdee`.

Status: local-source evidence for issue 48. This report makes no owner choice. It did
not train a model or mutate production code, corpora, artifacts, databases, benchmark
assets, or Obsidian notes. Evaluation code and evaluator configuration have no local
diff; the historical renderer has a pre-existing local diff, so frozen output bytes,
not the current renderer revision, are the evidence boundary.

## Result

The current evaluation path is not a fixed-`K`, once-per-eligible-origin evaluator.
It predicts all outer-window origins once, then selects those predictions repeatedly
with Poisson multiplicities. The historical 300- and 1,200-block suites leave no
random start to sample because each outer origin set is exactly the evaluator's block
width. Their only replay randomness is duplicate event weighting.

The current accounting also answers different questions under similar names:

- `profit_over_baseline` is a mean of per-event base-fee-per-gas percentages, not
  profit;
- `cost_over_optimum` and `baseline_cost_over_optimum` use the optimum fee as their
  denominator, so they do not form a baseline-denominated opportunity/regret identity;
- raw fee sums are unweighted sums of base fee per gas over synthetic arrivals, not
  transaction cost;
- no offline harmful-action rate, wait measure, tie-aware hit, unique-optimum
  accuracy, transaction-gas-weighted ratio, or finite-ratio interpretation exists;
- deadline overflow is not a metric. It is run metadata, while the selected action is
  moved to the first post-window row and receives ordinary economic credit.

The frozen evidence remains useful for checking old code, old selected periods,
window-length sensitivity, and reducer sensitivity. It cannot support issue 46's
closed-parent `h`, targets `h+1...h+K`, common fixed `K`, exhaustive-origin, clean
retraining contract. The approved contract explicitly makes old artifacts archival
and rejects deadline miss as a primary model outcome
([issue 46 resolution](https://github.com/edoski/spice/issues/46#issuecomment-4948024446)).

## Executable path

One evaluation currently executes this sequence:

1. The outer timestamp or block suite selects inference origins. Block suites require
   exactly one contiguous sample per integer block in `[start_block, end_block)`
   ([artifact inference](../../../src/spice/modeling/artifact_inference.py#L195-L241),
   [fixed-sequence inference selection](../../../src/spice/modeling/dataset_builders/fixed_sequence_temporal.py#L158-L201)).
2. The persisted artifact is loaded, its old temporal capability is reconstructed, and
   the model decodes one offset for every selected origin before replay selection
   ([artifact inference](../../../src/spice/modeling/artifact_inference.py#L79-L192),
   [scoring](../../../src/spice/modeling/scoring.py#L55-L74)).
3. A replay adapter returns one or more integer arrays of positions. Repeated positions
   are legal; there is no uniqueness check
   ([runner](../../../src/spice/evaluation/temporal_replay_runner.py#L101-L137),
   [position validation](../../../src/spice/evaluation/temporal_replay_runner.py#L157-L172)).
4. The execution policy maps every selected offset to realized, baseline, and optimum
   rows. Accounting exponentiates stored float32 log fees and reduces the selected
   events ([policy](../../../src/spice/temporal/execution_policy/strict_deadline_miss.py#L110-L150),
   [accounting](../../../src/spice/evaluation/temporal_accounting.py#L76-L131)).
5. Aggregate metrics, run-level metrics, run metadata, and run summaries are persisted
   in artifact state. Benchmark collections retain aggregate metrics and window
   summaries but omit the full runs and their metadata
   ([runtime summary](../../../src/spice/modeling/results.py#L198-L217),
   [collection record](../../../src/spice/benchmarks/result_records.py#L101-L174)).

This means exhaustive inference is already paid for in the old 300/1,200 evaluations.
The repetition factor affects selection/accounting, not model forward passes. Old
decoded actions were not preserved per origin, so they cannot be recovered from the
frozen collection without rerunning old-artifact inference.

## Current temporal meaning

The old compiler is timestamp-bounded, not fixed-block. For anchor row `h` it sets:

```text
context end                 = h
candidate start / baseline = h
candidate end               = first row with timestamp > timestamp[h] + delay
action width                = floor(max_delay / nominal_spacing) + 1
```

The end search uses `side="right"`, so every row at exactly `timestamp[h] + delay`
is included. The configured 36-second artifacts therefore have widths 4, 19, and 23
for Ethereum, Polygon, and Avalanche, not one shared `K`
([compiler](../../../src/spice/temporal/compilers/observed_time_window.py#L313-L320),
[store construction](../../../src/spice/temporal/compilers/observed_time_window.py#L332-L402),
[historical artifact facts](../issue-53/chain-regime-results-audit.md#provenance-and-what-was-checked)).

`strict_deadline_miss` exposes every nominal offset as selectable. If fewer physical
candidate rows exist, training truth masks the absent offsets, but decoding still may
select them. Realization then maps every unavailable offset to `candidate_end`, the
first post-window row, and sets `overflow_count`; several requested offsets can resolve
to that same row
([action space and outcome facts](../../../src/spice/temporal/execution_policy/strict_deadline_miss.py#L33-L107),
[realization](../../../src/spice/temporal/execution_policy/strict_deadline_miss.py#L110-L150)).
The checked-in test deliberately accepts a negative `cost_over_optimum` when that
post-window row is cheaper
([accounting test](../../../tests/evaluation/test_temporal_accounting.py#L94-L118)).

This is neither issue 46's complete fixed-`K` target set nor a serving availability
outcome. Under the approved contract, origins without all `h+1...h+K` outcomes are
structurally excluded, while live inference/parent failures fail closed. Issue 47 still
owns exact preprocessing eligibility and feature-span semantics. A prototype must use
symbolic or fixture eligibility until that ticket resolves them; this audit does not
choose them.

The current Sepolia service has a separate old mapping: observed closed row `h`,
baseline `h+1`, broadcast after `h+k`, and target `h+k+1`. Receipt accounting multiplies
both baseline and actual-inclusion base fees by the transaction's actual gas used
([serving mapping](../../../src/spice/serving/inference.py#L63-L110),
[receipt accounting](../../../src/spice/serving/inference.py#L112-L139)). This is useful
evidence for the old parity defect, not authority for issue 48. Issue 46 now fixes
target opportunity and actual inclusion as different objects.

## Replay selectors and weighting

| Path | Start | Arrivals and mapping | Effective weighting |
| --- | --- | --- | --- |
| Time Poisson | Continuous uniform start from first anchor timestamp through `last - window_seconds` | Exponential interarrivals; each arrival maps to the last anchor timestamp `<= arrival` | Wall-clock holding exposure plus a random-start edge kernel; an origin may repeat |
| Block Poisson | Discrete uniform start in `0...N-window_blocks` | Exponential interarrivals on artificial sample offsets; each arrival maps to the preceding offset | Equal block positions in expectation inside a fixed block window, modified by the random-start discrete edge kernel; an origin may repeat |
| Frozen 300/1,200 block suites | Only start `0`, because `N == window_blocks` | Same block-arrival mapping | Seeded Poisson multiplicities only; no random-window integration |

Sources: [time replay](../../../src/spice/evaluation/poisson_replay.py#L28-L108),
[block replay](../../../src/spice/evaluation/block_poisson_replay.py#L29-L137), and
[evaluator configs](../../../src/spice/conf/evaluator).

The time path sorts timestamps stably and uses `searchsorted(..., side="right") - 1`.
For duplicate integer-second timestamps, the last origin in the tied group receives all
positive holding exposure; earlier tied origins are not selected by continuous arrivals.
The block path instead sorts by block number and gives each sample offset a separate
block opportunity. Current tests cover latest-prior mapping and block-number ordering,
but not the duplicate-timestamp exposure result
([replay tests](../../../tests/evaluation/test_temporal_replay.py#L55-L83),
[block-order test](../../../tests/evaluation/test_temporal_replay.py#L126-L148)).

The time adapter's start support is based on the first and last selected anchor, not the
declared outer window boundaries. A start between anchors can map an early arrival to an
origin just before the sampled inner start. This is coherent only if that origin owns
the holding interval; the code does not retain the arrival time or name that interval.
The exact uniform-start kernel is therefore not materialized anywhere in runtime output.

The block adapter uses `arange(sample_count)` rather than numeric block differences.
Historical block suites are protected by the outer contiguous-block check. The adapter
alone would treat gapped block numbers as adjacent positions.

Both adapters instantiate `default_rng(config.seed)` for every evaluation. Every
same-width historical window therefore receives the same random-start/arrival stream.
For the frozen block suites this gives the same position-multiplicity pattern across all
windows and chains. The result index confirms identical total event counts:

| Evaluator | Origins | Repetitions | Rate | Expected total | Frozen total in every observation |
| --- | ---: | ---: | ---: | ---: | ---: |
| `block_poisson_replay_300` | 300 | 200 | 0.3/block | 18,000 | 17,858 |
| `block_poisson_replay` | 1,200 | 50 | 0.3/block | 18,000 | 17,876 |

The rate and repetition settings come from
[`block_poisson_replay_300.yaml`](../../../src/spice/conf/evaluator/block_poisson_replay_300.yaml)
and [`block_poisson_replay.yaml`](../../../src/spice/conf/evaluator/block_poisson_replay.yaml).
The counts are a read-only query of the hash-frozen result index described below.

For time-selected quartile suites, the outer windows are 4, 6, 8, 12, 16, 24, 36, 48,
or 72 hours, but the evaluator samples 50 two-hour episodes at 0.05 arrivals/second.
A 72-hour label is not a 72-hour replay result (local Obsidian `TODO.md` source;
[existing audit](../issue-53/chain-regime-results-audit.md#what-the-comparisons-actually-estimate)).
The maintained `nov9_2025_2h` suite is also narrower than the current adapter's usual
coverage check: an end-exclusive discrete two-hour origin set normally has
`last_timestamp - first_timestamp < 7200`, while the adapter requires at least 7,200
seconds. This config/code edge has no focused test and should not be assumed runnable.

## Exact reducers and units

For selected event `i`, current code defines:

```text
B_i = exp(float32_log_fee[baseline_row_i])
R_i = exp(float32_log_fee[realized_row_i])
O_i = exp(float32_log_fee[earliest_reachable_argmin_row_i])

profit_over_baseline_i        = (B_i - R_i) / B_i
cost_over_optimum_i           = (R_i - O_i) / O_i
baseline_cost_over_optimum_i  = (B_i - O_i) / O_i
exact_optimum_hit_i           = 1[realized_row_i == optimum_row_i]
```

Each run reports the arithmetic mean of those four event values plus `sum R_i`,
`sum B_i`, and `sum O_i`
([accounting](../../../src/spice/evaluation/temporal_accounting.py#L91-L125),
[metric catalog](../../../src/spice/evaluation/_temporal_replay_metric_catalog.py#L32-L83)).

Across runs, `EvaluationSummary.metrics` pools all event numerators and divides by total
events. Runs with more arrivals receive more weight. Fee sums are added. In contrast,
`window_metrics` is the unweighted mean and population standard deviation (`ddof=0`) of
run-level means
([aggregate accounting](../../../src/spice/evaluation/temporal_accounting.py#L55-L73),
[window reducer](../../../src/spice/evaluation/_temporal_replay_metric_catalog.py#L223-L239)).

The current renderer source reads the unweighted window mean for
`profit_over_baseline` and `exact_optimum_hit_rate`, but reads the event-pooled aggregate
for both optimum-cost metrics. It then uses `1.96 * population_std / sqrt(configured
repetitions)` for point whiskers
([renderer](../../../benchmarks/scripts/render_lstm_block_count_quartile_results.py#L140-L215)).
Thus one joined CSV row mixes finite reducers. For the frozen Ethereum 300-block row
`ethereum_block300_fee_level_q1_017_24003386`, the result index stores pooled
`profit_over_baseline = 1.2871078%`, while the joined CSV stores the unweighted
run-mean value `1.2909070%`
(joined row (`benchmarks/exports/ethereum_pectra_jun20_lstm_block300_quartile_joined.csv`)).
The difference is small there, but the names do not disclose it.

`B`, `R`, and `O` are base fee per gas in the EVM integer unit (wei/gas in these
corpora), reconstructed through a float32 log. Their sums therefore add wei/gas values
over synthetic repeated events. They are not wei transaction costs. The scanner divides
the same raw field by `1e9` for gwei display
([scanner](../../../benchmarks/scripts/scan_block_count_quartile_windows.py#L50-L123)).

No additive opportunity identity follows from current headline metrics because savings
uses denominator `B_i`, while both gaps use `O_i`. The raw sums permit an unweighted
finite replay ratio `(sum B - sum R) / sum B`, but code gives it no metric ID and gives
no interpretation as a finite random ratio versus a ratio of expected sums.

The only current gas-weighted ratio is in serving analytics:

```text
sum_i gas_i * (baseline_base_fee_i - included_base_fee_i)
---------------------------------------------------------
             sum_i gas_i * baseline_base_fee_i
```

It uses actual receipt gas and actual inclusion. Offline block corpora contain whole-block
`gas_used`, not a synthetic request's transaction gas. Substituting block gas would
change the estimand and is not supported by current code or frozen evidence
([serving totals](../../../src/spice/serving/analytics.py#L120-L154)).

## Requested issue-48 concepts versus stored evidence

| Concept | Current executable meaning | Can old frozen output answer it? |
| --- | --- | --- |
| Immediate `k=0` comparison | Baseline is old candidate row `h` offline; `h+1` in old serving | No. Issue 46 fixes offline opportunity to `h+1`; retraining/replay must change. |
| Hindsight best within fixed `K` | Earliest minimum over reachable rows in a variable 36-second candidate window | No fixed-`K` result. |
| Base-fee savings | Mean event ratio under Poisson duplicates, mislabeled profit | Only under old sampled-event semantics. |
| Baseline-denominated gap/regret | Absent; current gap uses optimum denominator | No. Aggregate fee sums can show a reducer example, not origin-level clean-contract regret. |
| Gas-weighted ratio of sums | Absent offline | No request-gas vector exists. |
| Harmful-action rate `P(R>B)` | Absent | No per-origin `R/B` rows are frozen. |
| Waiting | Absent offline; old serving estimates `round(k * nominal_spacing)` | No selected-offset or realized-wait vector is frozen. |
| Tie-aware fee-optimal behavior | Absent; exact row equality to earliest `argmin` | No raw tie set or per-origin prediction is frozen. |
| Unique-action accuracy | Absent; training `offset_accuracy` compares every prediction to earliest `argmin` | No uniqueness-conditioned count is frozen. |
| Deadline/fallback rate | `overflow_count` metadata; unavailable action is moved post-window | Not in frozen collections/exports. It is not valid issue-46 model performance. |
| Structural/serving availability | No separate evaluator outcome taxonomy | No. Current overflow mixes geometry and action realization. |
| Finite ratio versus ratio of expectations | Unnamed | No workload or target interpretation is stored. |

Training truth uses `np.argmin` on float32 log-fee outcomes, so the first minimum wins.
`offset_accuracy` is ordinary exact class equality; `exact_optimum_hit_rate` is exact row
equality. A later equal-fee action is a miss under both. The store does not retain raw
integer outcome fees beside model inputs, so exact raw-value tie reconstruction is not
part of evaluation
([target materialization](../../../src/spice/prediction/families/min_block_fee_multitask/batch.py#L13-L35),
[training metrics](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L133-L165),
[optimum realization](../../../src/spice/temporal/execution_policy/strict_deadline_miss.py#L48-L56)).

## Frozen 300/1,200 evidence

The authoritative freeze is
[`spice-pre-break-evidence-manifest.tsv`](../spice-pre-break-evidence-manifest.tsv),
whose manifest SHA-256 is
`213e31475bcd9a56e44385fcc61f9be40ff18d4120adfdf95063d742ccdb143b`.
The current `benchmarks/results.sqlite` still matches its frozen SHA-256
`ba70a8f65e9210edc2cfee63243d69e46f55235f5b78f39d7dd5cdd83bf724b0`.
It contains the two currently readable block collections only: 648 observations each,
216 per chain, for 1,296 total. Each observation records `sample_count` as 300 or 1,200
plus aggregate evaluation metrics and window summaries; it does not store the origins
([inventory](../issue-8/evaluation-suite-data-findings.md#results-exports-and-figures)).

Each suite selects 108 fee-level and 108 volatility windows per chain, with 27 windows
per quartile on each selection axis. The scanner uses full contiguous candidate windows
with stride equal to window length, then selects metric-quantile representatives. This
is deliberate outcome-regime stratification, not a random sample of periods
([scanner](../../../benchmarks/scripts/scan_block_count_quartile_windows.py#L75-L178),
local Obsidian `TODO.md` section 06/07).

The frozen joined outputs support one limited descriptive statement: shortening the old
outer window increased dispersion without reversing the broad old chain ordering.

| Chain | Old 1,200-block window mean +/- SD | Old 300-block window mean +/- SD |
| --- | ---: | ---: |
| Ethereum | `+1.169% +/- 0.466` | `+1.194% +/- 0.640` |
| Polygon | `-0.071% +/- 1.140` | `-0.051% +/- 2.306` |
| Avalanche | `+0.407% +/- 0.953` | `+0.362% +/- 1.868` |

These are descriptive across selected windows under the old displayed reducer, not
deployment intervals, training-seed evidence, fixed-`K` results, or proof of profit
([TODO/results audit](../issue-53/chain-regime-results-audit.md#full-2906-versus-0607-result)).
The current files also cannot establish their exact generating renderer revision; their
bytes are frozen archival evidence
([asset inventory](../research-evaluation-publication-assets-inventory.md#script-and-publication-provenance)).

The result index's fee sums permit reducer audits. Across its 1,296 rows, the existing
statistics review found 80 cases where mean-event savings and per-observation fee-sum
savings had opposite signs; Polygon's mean old event result is negative while its pooled
fee-sum ratio is positive. This proves denominator/reducer choice is material. It does
not select the right metric
([statistics cross-review](../issue-1/temporal-evaluation-statistics-cross-review.md#3-economic-estimands-and-the-historical-sign-flip)).

Artifact state still holds replay-run metadata. A present-day immutable read matched all
1,296 frozen result job IDs and found nonzero overflow in the old rows below:

| Chain | 300: affected evaluations; sampled overflow/events | 1,200: affected evaluations; sampled overflow/events |
| --- | ---: | ---: |
| Ethereum | 108/216; 18,620/3,857,328 (0.483%) | 197/216; 19,358/3,861,216 (0.501%) |
| Polygon | 1/216; 6,844/3,857,328 (0.177%) | 4/216; 18,414/3,861,216 (0.477%) |
| Avalanche | 23/216; 16,027/3,857,328 (0.415%) | 58/216; 16,292/3,861,216 (0.422%) |

This table is corroboration, not frozen evidence: corpus and artifact bytes were
deliberately excluded from the content manifest. `overflow_count` counts repeated
sampled events, not unique origins, and the frozen collection omits it. The old economic
metrics cannot be repaired by subtracting these counts because neither affected
origin/action identities nor their fee contributions are in the collection
([freeze limits](../issue-8/evaluation-suite-data-findings.md#status-and-limits)).

## Exact low-cost prototype inputs

No old model is needed to test selector, denominator, tie, harmful-action, or
duplicate-timestamp formulas. The smallest evidence sources are:

1. **Hand fixture:** integer base-fee and gas-unit literals. This is the only source that
   can make every expected metric and tie set hand-computable without inheriting old
   semantics.
2. **Frozen aggregate reducer probe:** immutable
   `benchmarks/results.sqlite`. It has `B/R/O`
   fee sums and old mean-event metrics, enough to demonstrate mean-of-ratios versus
   ratio-of-sums. It has no clean-contract origins, gas vector, waits, or ties.
3. **Modern-regime raw trace probe:** one tracked 300/1,200 suite pair per chain. The
   pairs below are nested and already have frozen old outputs, but must be used as raw
   trace/selector fixtures only:

| Chain | 1,200-block fixture | Contained 300-block fixture | Corpus |
| --- | --- | --- | --- |
| Ethereum | `ethereum_block1200_fee_level_q2_004_24680786` (`24,680,786...24,681,985`) | `ethereum_block300_fee_level_q2_006_24680786` (`24,680,786...24,681,085`) | `cor_7bea5a071afaf090c05a` |
| Polygon | `polygon_block1200_volatility_q3_025_85809690` (`85,809,690...85,810,889`) | `polygon_block300_volatility_q4_001_85810590` (`85,810,590...85,810,889`) | `cor_61fb33e47c948a9cebd0` |
| Avalanche | `avalanche_block1200_volatility_q2_016_82421952` (`82,421,952...82,423,151`) | `avalanche_block300_volatility_q2_001_82422852` (`82,422,852...82,423,151`) | `cor_3ef359c91addcab77e9f` |

All six windows lie inside issue 54's recommended modern-regime boundaries. They were
selected after inspecting fee/volatility and old outcomes, so they are diagnostics, not
sealed testing candidates. Their suite definitions are under
[`src/spice/conf/evaluations`](../../../src/spice/conf/evaluations), their frozen
selection rows under
`benchmarks/exports/evaluation_window_scans`,
and their frozen old summaries under
`benchmarks/exports`. Loading raw rows needs only the
named corpus Parquet and no training.

A focused duplicate-timestamp fixture is
`avalanche_block300_fee_level_q2_014_84011652`, blocks
`84,011,652...84,011,951`. It is post-Granite and contains:

| Block | Unix second | Raw base fee per gas | Whole-block gas used |
| ---: | ---: | ---: | ---: |
| 84,011,829 | 1,777,290,243 | 29,909,271 | 1,120,571 |
| 84,011,830 | 1,777,290,243 | 29,665,203 | 1,347,615 |

The time selector assigns continuous-arrival exposure at that second to the latter
origin; the block selector and exhaustive block-origin estimator keep both. These raw
rows are in
`avalanche__blocks__84009162_to_84013257.parquet`.
The suite/selection/output paths are byte-frozen, but corpus/model bytes are not; this is
a reproducible current local probe, not an independently frozen thesis result.

Issue 54 counts 177/216 Ethereum and 51/216 Polygon selected 300-block windows inside
its modern boundaries; all 216 Avalanche windows are post-Granite. The corresponding
1,200 counts are 183, 56, and 216. Regime containment alone does not seal a test or
repair old action semantics. Final role periods, exact eligible origins, features,
context, and `K` remain unresolved owner inputs
([issue 54 resolution](https://github.com/edoski/spice/issues/54#issuecomment-4947306822)).

## What can survive issue 46

Reusable evidence:

- raw contiguous block numbers, integer base fees, timestamps, and core block fields;
- the existence and byte identity of old selected-window definitions and outputs;
- old within-semantics sensitivity to outer-window length and reducer choice;
- exact examples showing timestamp duplicates, ties, overflow, and event weighting;
- existing manifests/configs as provenance for what was run.

Not reusable as clean-contract performance evidence:

- old model rankings or savings claims;
- old 4/19/23 action widths and nominal 36-second labels;
- Poisson repeat whiskers as deployment, period, or seed uncertainty;
- generic profit language;
- `exact_optimum_hit_rate` as tie-aware fee-optimal accuracy;
- old overflow economics, deadline/fallback interpretation, or actual-inclusion claims;
- any cross-chain pooled fee total or common-currency interpretation.

This matches the closed issue-53 result: exhaustive once-per-eligible-origin replay is
the researched primary block-origin candidate, while Poisson survives only for an
explicit timestamp-preserving request-arrival estimand. The 300/1,200 results remain
archival sampled-event evidence
([issue 53 resolution](https://github.com/edoski/spice/issues/53#issuecomment-4946214017),
[research report](../fixed-block-comparability-and-exhaustive-replay.md)).

## Read-only probes

The audit used `sqlite3` URI `mode=ro&immutable=1` for the frozen result index and local
artifact state. The core frozen count query was:

```sql
select benchmark, evaluator_id, chain_name, count(*),
       min(sample_count), max(sample_count),
       min(total_events), max(total_events)
from result_observations
group by benchmark, evaluator_id, chain_name;
```

The three raw-window probes used Polars lazy Parquet filters on explicit block ranges.
The focused evaluator suite passed 31 tests. No script wrote output. The research-skill
background subdivision was attempted, but the shared four-agent limit was already full;
this pass was completed locally.
