# Progress

## Current State

- Branch: `codex/temporal-parity`
- Primary benchmark surface: `paper_replay_2h`
- Diagnostic surfaces:
  - `notebook_rollout_fullset`
  - `notebook_basefee_fullset`

## Main Paths

- Unsafe reference path:
  - presets: `icdcs_2026_oracle_intermediate*`
  - feature sets: `icdcs_2026_professor*`
  - semantics: current-block action space, fixed ex-ante classes, current-row pricing, post-block features
  - why unsafe: model can act on the same block row whose finalized block facts it already sees
  - status: best paper/professor reproduction so far

- Safe current-block path:
  - presets: `icdcs_2026_oracle_block_open*`
  - feature sets: `icdcs_2026_professor_block_open*`
  - semantics: current-block action space, fixed ex-ante classes, current-row pricing, block-open feature contract
  - safety rule: finalized current-block features are lagged; current base fee is kept
  - status: clean causal sibling path, still underperforming on Ethereum

## Verified Facts

- The professor artifacts are likely using an unsafe current-block convention.
- The professor-like path appears to use fixed ex-ante classes.
- The old realized-future action-mask oracle was too unsafe and is not the reference target.
- Unsafe intermediate is closer to the professor setup than the old realized-mask oracle.
- Notebook rollout is more permissive than replay because it re-decides one row at a time until the model emits `0`.

## Cross-Chain Replay Results

Percent values below are `profit_over_baseline` on `paper_replay_2h`.

| Chain | Paper Fig. 6 approx | Unsafe reference | Safe block-open |
| --- | --- | --- | --- |
| Ethereum | `2.55 / 2.62 / 2.58` | `2.59 / 2.62 / 2.59` | `1.04 / 1.12 / 0.89` |
| Polygon | `0.20 / 0.20 / 0.19` | `0.46 / 0.34 / 0.32` | `0.40 / 0.23 / 0.36` |
| Avalanche | `0.95 / -0.15 / 0.58` | `1.25 / 1.35 / 1.23` | `1.21 / 0.47 / 0.09` |

Model order: `LSTM / Transformer / Transformer-LSTM`

## What Worked

- Unsafe current-block reference reproduces or exceeds the paper band across all three chains.
- Safe block-open remains viable but is materially below the unsafe reference on Ethereum.
- Cross-chain baseline picture is now complete for both safe and unsafe paths.

## What Did Not Work

- The fully safe next-block oracle path did not preserve the professor-like gain.
- Safe block-open still loses too much of the Ethereum gain.
- Split-local preprocessing is deferred; it is not the current architectural direction.

## Latest Completed Wave

- Wave: Ethereum-only time-feature ablations
- Scope:
  - both paths: unsafe reference and safe block-open
  - all 3 families
  - feature variants:
    - `full`
    - `no_time_since_start`
    - `no_time_features`
    - `calendar_only_time`
    - `time_since_start_only`
- Primary surface: `paper_replay_2h`

### Unsafe reference replay results

| Family | Full | No `time_since_start` | No time features | Calendar only | `time_since_start` only |
| --- | --- | --- | --- | --- | --- |
| LSTM | `0.0228` | `0.0264` | `0.0266` | `0.0265` | `0.0255` |
| Transformer | `0.0265` | `0.0258` | `0.0261` | `0.0253` | `0.0263` |
| Transformer-LSTM | `0.0262` | `0.0264` | `0.0262` | `0.0261` | `0.0259` |

### Safe block-open replay results

| Family | Full | No `time_since_start` | No time features | Calendar only | `time_since_start` only |
| --- | --- | --- | --- | --- | --- |
| LSTM | `0.0096` | `0.0113` | `0.0119` | `0.0116` | `0.0096` |
| Transformer | `0.0099` | `0.0122` | `0.0106` | `0.0116` | `0.0110` |
| Transformer-LSTM | `0.0107` | `0.0121` | `0.0117` | `0.0123` | `0.0109` |

### Main conclusions

- `time_since_start` alone does **not** preserve most of the gain.
- Dropping `time_since_start` is often neutral-to-helpful and is a credible simplification candidate.
- On the safe path, full time features were never the best completed variant for any family.
- The strongest simplifying wins are:
  - safe `lstm`: `no_time_features` (`0.0119`) over full (`0.0096`)
  - safe `transformer`: `no_time_since_start` (`0.0122`) over full (`0.0099`)
  - safe `transformer_lstm`: `calendar_only_time` (`0.0123`) over full (`0.0107`)
- There is no single universal winner across all families.
- Notebook metrics were directionally consistent with the replay findings.

## Next After This Wave

- Interval estimation:
  - Goal:
    - improve fixed ex-ante action sizing without using future realized timestamps
    - recover some of the unsafe-path gain while staying causal
  - Core requirement:
    - chain agnostic
    - online-safe
    - past-only
    - no launch until results from the current wave are reviewed in-thread
  - Why this matters:
    - the task is time-budgeted, not purely block-count-budgeted
    - a fixed nominal interval like `12s` or `1.6s` is simple but crude
    - if the interval is set too high, the action space is too narrow
    - if it is set too low, the action space is too wide and overflow / miss behavior increases
    - a better causal estimate may recover some performance without reintroducing leakage
  - Planned seam:
    - explicit `action_interval_estimator` inside the timestamp-window compiler
    - no chain-specific branching in acquisition or evaluation
    - artifact stores the resolved estimator provenance needed for rebuilds and auditability
  - Candidate estimator families:
    - `nominal`
      - use `chain.runtime.nominal_block_time_seconds`
      - baseline and default comparator
    - `recent_deltas_mean`
      - mean of recent positive inter-block deltas over the last `N` blocks
    - `recent_deltas_median`
      - median of recent positive inter-block deltas over the last `N` blocks
      - likely more robust than mean
    - `recent_deltas_quantile`
      - quantile of recent positive inter-block deltas, e.g. p25 / p50 / p75
      - gives a tunable conservative or aggressive width
    - possible later extensions if needed:
      - exponentially weighted versions
      - clipped / winsorized variants
      - chain-conditioned but still generic parameter sets
  - Likely first practical candidates:
    - rolling median over recent deltas
    - rolling quantile over recent deltas
    - these are simple, robust, and easy to explain
  - Semantics:
    - estimator resolves one fixed interval for the artifact from the selected training chronology
    - that interval determines the artifact's fixed ex-ante action width
    - evaluation must reuse the trained artifact width
    - evaluation must not inspect future realized evaluation-day timestamps to resize the action space
  - Safety rule:
    - estimator may use only past positive deltas available at training / deployment time
    - no realized future candidate-count help in loss, decode, or eval
  - Benchmark plan when this phase begins:
    - Ethereum `36s` first
    - both paths:
      - unsafe intermediate reference
      - safe block-open
    - all 3 families
    - compare nominal vs recent-deltas estimators on the same evaluator surface
    - `paper_replay_2h` remains primary
  - What would count as success:
    - clear replay improvement on safe block-open without architectural degradation
    - ideally preserves or improves unsafe reference too, but safe-path improvement is the main target
  - Failure modes to watch:
    - estimator overfits training chronology and does not transfer
    - estimator width is too optimistic and increases misses
    - estimator width is too conservative and collapses useful action options
    - gains are chain-specific and do not justify promotion
  - Governance:
    - no compiler default change without explicit in-thread approval

## Deferred Future Feature Ideas

- Range-position features
  - Goal: tell the model where the current fee sits inside a recent local range, not just the raw fee level.
  - Candidate features:
    - distance to rolling min / rolling max
    - normalized position inside rolling min-max band
    - percentile rank of current fee within the last `N` blocks
    - drawdown from recent local maximum
  - Why this may help:
    - the decision problem is economic and wait-based
    - “am I already near a local cheap point?” is often more important than absolute level
    - we already expose rolling minima and means, but not the current fee's relative position inside the recent range
  - Safety notes:
    - straightforward to make causal on both unsafe and safe paths
    - for safe block-open, use current known base fee and past-only windows

- Regime spread features
  - Goal: make regime shifts explicit instead of forcing the model to infer them from separate short and long rolling stats.
  - Candidate features:
    - `roll10_mean_logfee - roll200_mean_logfee`
    - `roll10_std_logfee / roll200_std_logfee`
    - short-vs-long spreads for gas pressure / utilization
    - short-vs-long trend-slope differences
  - Why this may help:
    - these directly encode whether the chain is heating up, cooling off, or remaining stable
    - they are especially relevant for “wait one more block or not?” decisions
  - Safety notes:
    - cheap to add; fully causal if built from the existing rolling stats

- Curvature features
  - Goal: capture acceleration / deceleration, not just direction.
  - Candidate features:
    - second difference of log base fee
    - second difference of gas pressure
    - change in trend slope over recent windows
    - acceleration of utilization relative to target
  - Why this may help:
    - first differences say where the series is moving
    - curvature says whether that move is strengthening or weakening
    - this is directly relevant to timing decisions near turning points
  - Safety notes:
    - causal if derived from current-and-past safe observables only

- Persistence / streak features
  - Goal: encode how persistent the current congestion or relief regime has been.
  - Candidate features:
    - consecutive blocks with positive `dlog_base_fee`
    - consecutive blocks with negative `dlog_base_fee`
    - consecutive blocks with gas utilization above target
    - fraction of last `N` blocks above target
    - fraction of last `N` blocks with falling base fee
  - Why this may help:
    - rolling averages can hide whether the signal came from one spike or a sustained run
    - persistence is useful for judging whether mean reversion is likely
  - Safety notes:
    - for safe block-open, compute from lagged realized history and current known base fee only

- Protocol-aware pressure features
  - Goal: encode fee-relevant pressure in the protocol's own terms, not just generic utilization.
  - Candidate features:
    - `gas_utilization - target_utilization`
    - rolling mean of positive excess over target
    - rolling mean of slack below target
    - share of recent blocks materially above target
    - signed cumulative excess over the last `N` blocks
  - Why this may help:
    - EIP-1559 reacts to utilization relative to the target, not just raw gas usage
    - this is more directly tied to next-block fee dynamics
  - Safety notes:
    - works with current data; no new source required

- Cadence uncertainty / opportunity-density features
  - Goal: model not just fee movement, but how many timing opportunities likely fit inside the wait budget.
  - Candidate features:
    - rolling mean / std / coefficient of variation of `dt_seconds`
    - recent count of blocks in the last `60s`, `120s`, `300s`
    - fraction of recent blocks faster than nominal interval
    - recent opportunity density implied by observed inter-block times
  - Why this may help:
    - the action space is fundamentally time-budgeted
    - more blocks arriving quickly means more chances to wait without overshooting the deadline
  - Safety notes:
    - especially relevant for the future interval-estimation wave
    - must remain past-only on the safe path

- Robust quantile features
  - Goal: make the feature surface less sensitive to heavy tails and transient spikes.
  - Candidate features:
    - rolling fee quantiles: p10 / p25 / p50 / p75 / p90
    - rolling pressure quantiles
    - interquartile range
    - distance from current level to rolling median / p10 / p90
  - Why this may help:
    - mean / std are often brittle on fee series with bursts
    - quantiles can encode local distribution shape more robustly
  - Safety notes:
    - more expensive than mean/std, but still feasible with current data volumes

- New-data-source features if we expand ingestion later
  - Goal: move beyond post-block summaries into more directly causal inclusion-pressure signals.
  - Candidate sources:
    - mempool backlog / arrival-rate features
    - pending transaction age distribution
    - priority-fee / tip distribution
    - transaction-count / block-composition features
  - Why this may help:
    - these would likely be more powerful than extra calendar tricks if collected cleanly
    - they may allow a stronger same-slot or late-slot causal formulation
  - Constraint:
    - not part of the current data surface
    - requires explicit ingestion and problem-definition work

## Deferred Cleanup

- Do not delete old paths blindly.
- After the experimental surface stabilizes:
  - keep one unsafe reference path
  - keep one safe path
  - rename implementations around semantics, not provenance
  - remove stale configs only with explicit justification
