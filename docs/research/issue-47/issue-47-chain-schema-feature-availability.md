# Issue 47 chain schema and feature availability

Status: bounded planning evidence for [issue 47](https://github.com/edoski/spice/issues/47). This report audits corpus facts and feature availability only. It does not change a corpus, implementation, configuration, artifact, or owner policy.

## Lean recommendation

Use the issue-54 modern boundaries unchanged: Ethereum BPO2, Polygon post-Giugliano, and Avalanche post-Granite. Admit a sample only when its entire feature warmup and block context through closed parent `h`, plus every outcome `h+1...h+K`, stays inside one regime.

Use a direct block-count context. Do not derive its row count from a full-corpus median or call it a 600-second context. Keep the common protocol-observation core to `ln(base_fee_per_gas[h])` and `gas_used[h] / gas_limit[h]`. Put closed-parent capacity/activity, calendar/cadence, explicit lags, and rolling statistics into separately removable groups. Ethereum alone receives the approved exact forming execution-base-fee scalar; Polygon and Avalanche omit the dimension rather than receiving a placeholder.

Do not carry the 45-, 46-, or 77-feature catalogs forward unchanged. The common 45 mix stale `j-1` facts with `j` facts, five overlapping fee windows, undocumented minima, duplicate explicit history, and inconsistent standard-deviation conventions. The 46th elapsed feature has no stable offline/live origin and disagrees with the paper's stated unit. All 32 priority-fee additions are unavailable in every selected modern corpus.

## Measured modern corpus facts

The local Parquet schemas are identical: 14 nullable `Int64` columns. The manifests declare `clean`, block ordering, and the seven required core columns. Independent lazy scans produced these results:

| Chain and selected regime | Rows; inclusive blocks | UTC seconds | Gaps / duplicate heights / decreasing timestamps | Equal-second transitions | Core physical domains | Optional-field coverage |
|---|---|---|---|---:|---|---|
| Ethereum, BPO2 | 1,175,689; 24,179,383-25,355,071 | 1,767,747,671-1,781,913,599 | 0 / 0 / 0 | 0 | no null core value; fee and limit positive; `0 <= gas_used <= gas_limit`; count nonnegative | size/blob fields 100%; priority fields 0% |
| Polygon, post-Giugliano | 1,756,067; 85,268,500-87,024,566 | 1,775,657,037-1,779,032,699 | 0 / 0 / 0 | 0 | same | size 100%; blob and priority fields 0% |
| Avalanche, post-Granite | 13,435,499; 72,240,649-85,676,147 | 1,763,568,000-1,779,032,699 | 0 / 0 / 0 | 65,715 | same | size/blob columns 100%, but both blob columns are constant zero; priority fields 0% |

These boundaries come from the [issue-54 report](../modern-regime-coverage-and-evidence-periods.md). Primary activation evidence is Ethereum's [BPO schedule](https://blog.ethereum.org/2025/11/06/fusaka-mainnet-announcement), Polygon [PIP-83](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/9a7feed01afdf6923bfac3dd10bbb4631ed50099/PIPs/PIP-83.md), and Avalanche [ACP-226](https://build.avax.network/docs/acps/226-dynamic-minimum-block-times).

The only non-null local priority-fee interval is historical Ethereum blocks 22,664,726-23,765,143, ending at Unix second 1,762,732,799 (2025-11-09 23:59:59 UTC). It contains 1,100,418 rows and predates BPO2. Polygon and Avalanche contain no priority values anywhere. A priority experiment therefore needs a new, predeclared acquisition; null filling would invent a signal.

The selected Ethereum range reproduced the EIP-1559 child execution fee on all 1,175,688 adjacent transitions using integer parent fee, parent gas used, parent gas limit, elasticity `2`, denominator `8`, and the one-wei upward floor. Post-BPO2 blob changes do not replace that execution-fee recurrence. Ethereum [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) owns the exact formula; [EIP-7918](https://eips.ethereum.org/EIPS/eip-7918) changes blob-fee state, not this execution fee.

All 1,756,066 modern Polygon transitions stayed inside the parent-relative 5% validity bound. That does not make the child fee exact from parent facts: [PIP-79](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/c65ce300229593bea17ff21f569c259121b4dd11/PIPs/PIP-79.md) intentionally permits producer choice inside the range, while PIP-83's completed-child gas parameters are self-reported metadata. Avalanche's [ACP-176](https://build.avax.network/docs/acps/176-dynamic-evm-gas-limit-and-price-discovery-updates) fee uses state and elapsed time absent from the canonical schema. These facts support issue 46's Ethereum-only scalar.

## Raw schema inventory and units

`available_at=close(j)` means after block `j` is observed as the closed canonical parent and its RPC response is complete. It does not mean finalized. Offline values come from the canonical Parquet row; online values come from `eth_getBlockByNumber(j, false)` unless noted. The local extraction is in [`corpus/contract.py`](../../../src/spice/corpus/contract.py), and the live/acquisition path is in [`acquisition/rpc/client.py`](../../../src/spice/acquisition/rpc/client.py).

| Raw field | Exact unit / meaning | `available_at` | Modern E / P / A | Candidate use and parity caveat |
|---|---|---|---|---|
| `block_number` | dimensionless chain height | `close(j)` | yes / yes / yes | identity/order metadata, not a normalized model input |
| `timestamp` | integer Unix seconds | `close(j)` | yes / yes / yes | parent calendar/cadence only; Avalanche loses protocol millisecond precision |
| `base_fee_per_gas` | native-asset wei per execution gas | `close(j)` | yes / yes / yes | protocol core and target source |
| `gas_used` | execution-gas units consumed in `j` | `close(j)` | yes / yes / yes | protocol pressure numerator |
| `gas_limit` | execution-gas units in the conventional header limit | `close(j)` | yes / yes / yes | pressure denominator; on Avalanche it is not ACP-176 live capacity |
| `tx_count` | included transaction count | `close(j)` | yes / yes / yes | completed parent activity only |
| `chain_id` | EVM chain identifier: 1 / 137 / 43114 | configuration and row | yes / yes / yes | partition/validation metadata |
| `block_size_bytes` | serialized block size in bytes returned by RPC | `close(j)` | yes / yes / yes | available but no approved hypothesis; omit initially |
| `blob_gas_used` | blob-gas units | `close(j)` | yes / no / constant zero | separate fee market; omit from execution-fee baseline |
| `excess_blob_gas` | blob-gas state units | `close(j)` | yes / no / constant zero | same |
| `priority_fee_p10/p50/p90` | gas-consumption-weighted effective tip percentile, native wei/gas | after `eth_feeHistory` for closed `j` | no / no / no | optional only after reacquisition/provider proof |
| `priority_fee_spread` | `p90-p10`, native wei/gas | same | no / no / no | same |
| `block_hash` | 32-byte execution block hash | `close(j)` | **not stored** | live/selected-evidence identity only; not an offline-row requirement or model feature |
| `timestampMilliseconds`, Avalanche | Unix milliseconds | `close(j)` | n/a / n/a / **not stored** | required for protocol-exact Granite cadence, not for coarse calendar |

The Ethereum Execution API defines [`eth_feeHistory`](https://ethereum.github.io/execution-apis/api/methods/eth_feeHistory/) rewards as effective priority fees per gas selected after sorting tips and accounting for gas consumed. SPICE requests percentiles 10, 50, and 90. They are completed-block summaries and are not available before their block closes.

## Proposed per-feature `available_at` table

Every ordinary row feature below is evaluated only for `j <= h`. `P->R` means the same formula over offline Parquet rows and closed-block RPC rows. `W` is the number of earlier rows needed before the first finite value. Natural logs apply to the numeric value in the stated raw unit and are later scaled; they do not change availability.

| Feature | Formula and derived unit | `available_at` | Modern E / P / A | Offline / online source | `W` | Status and parity caveat |
|---|---|---|---|---|---:|---|
| `log_base_fee_per_gas[j]` | `ln(base_fee_per_gas[j] in wei/gas)` | `close(j)` | yes / yes / yes | P->R base fee | 0 | **protocol core** |
| `gas_utilization[j]` | `gas_used[j] / gas_limit[j]`, ratio | `close(j)` | yes / yes / yes | P->R gas facts | 0 | **protocol core**; descriptive on Avalanche, not its hidden fee state |
| `log_gas_limit[j]` | `ln(gas_limit[j] in gas)` | `close(j)` | yes / yes / yes | P->R | 0 | optional capacity fact |
| `log1p_tx_count[j]` | `ln(1 + tx_count[j])` | `close(j)` | yes / yes / yes | P->R | 0 | optional activity fact |
| `exact_forming_base_fee_per_gas` | exact EIP-1559 `base_fee[h+1]`, wei/gas; model may encode its log as the same one logical scalar | `tau_h`, from closed `h` | **yes / omitted / omitted** | P->same pure function->R | 0 | approved Ethereum-only enhancement; no derived roll/lag/calendar companions |
| `seconds_since_previous_block[j]` | `timestamp[j]-timestamp[j-1]`, seconds | `close(j)` | exact whole seconds / exact whole seconds / quantized whole seconds | P->R timestamps | 1 | optional cadence; Granite-exact use needs millisecond acquisition |
| `hour_sin[j]` | `sin(2*pi*UTC-hour(timestamp[j])/24)`, ratio | `close(j)` | yes / yes / yes | P->R timestamp | 0 | optional parent calendar |
| `hour_cos[j]` | cosine companion, ratio | `close(j)` | yes / yes / yes | P->R timestamp | 0 | optional parent calendar |
| `dow_sin[j]` | `sin(2*pi*UTC-weekday(timestamp[j])/7)`, ratio | `close(j)` | yes / yes / yes | P->R timestamp | 0 | optional parent calendar |
| `dow_cos[j]` | cosine companion, ratio | `close(j)` | yes / yes / yes | P->R timestamp | 0 | optional parent calendar |
| `dlog_base_fee[j]` | `log_fee[j]-log_fee[j-1]`, log ratio | `close(j)` | yes / yes / yes | P->R fee history | 1 | optional explicit-history group |
| `dlog_base_fee_lag1` ... `lag6` | `dlog_base_fee[j-q]`, log ratio | `close(j-q)`; usable at `close(j)` | yes / yes / yes | P->R | `2...7` | optional; sequence already contains this history |
| `gas_utilization_lag1` ... `lag6` | `gas_utilization[j-q]`, ratio | `close(j-q)`; usable at `close(j)` | yes / yes / yes | P->R | `1...6` | optional; sequence already contains this history |
| `roll10_mean_logfee` | mean of rows `j-9...j`, log-value mean | `close(j)` | yes / yes / yes | P->R | 9 | optional rolling group |
| `roll10_std_logfee` | population standard deviation over same 10 rows, log-value spread | `close(j)` | yes / yes / yes | P->R | 9 | optional; use one declared `ddof=0` convention |
| `roll50_mean_logfee` | mean over `j-49...j` | `close(j)` | yes / yes / yes | P->R | 49 | optional rolling group |
| `roll50_std_logfee` | population standard deviation over same 50 rows | `close(j)` | yes / yes / yes | P->R | 49 | optional |
| `roll200_mean_logfee` | mean over `j-199...j` | `close(j)` | yes / yes / yes | P->R | 199 | optional rolling group |
| `roll200_std_logfee` | population standard deviation over same 200 rows | `close(j)` | yes / yes / yes | P->R | 199 | optional |
| `roll10_mean_gas_utilization` | mean ratio over `j-9...j` | `close(j)` | yes / yes / yes | P->R | 9 | optional rolling group |
| `roll10_std_gas_utilization` | population standard deviation of ratio | `close(j)` | yes / yes / yes | P->R | 9 | optional |
| `roll50_mean_gas_utilization` | mean ratio over `j-49...j` | `close(j)` | yes / yes / yes | P->R | 49 | optional |
| `roll50_std_gas_utilization` | population standard deviation of ratio | `close(j)` | yes / yes / yes | P->R | 49 | optional |
| `roll200_mean_gas_utilization` | mean ratio over `j-199...j` | `close(j)` | yes / yes / yes | P->R | 199 | optional |
| `roll200_std_gas_utilization` | population standard deviation of ratio | `close(j)` | yes / yes / yes | P->R | 199 | optional |
| `priority_fee_p10[j]` | effective tip percentile, wei/gas | after closed-block fee history | no / no / no | Parquet / `eth_feeHistory` | 0 | unavailable candidate |
| `priority_fee_p50[j]` | same, wei/gas | same | no / no / no | same | 0 | unavailable candidate |
| `priority_fee_p90[j]` | same, wei/gas | same | no / no / no | same | 0 | unavailable candidate |
| `priority_fee_spread[j]` | `p90-p10`, wei/gas | same | no / no / no | same | 0 | unavailable candidate |
| `log/dlog/lag/roll priority` | log numeric wei/gas, log ratios, or rolling log-value moments | no earlier than closed source rows | no / no / no | same formulas P->R | up to 199 unshifted | reject for current evidence; would need a new complete modern corpus |
| `elapsed_seconds[j]` | `timestamp[j]-timestamp[first frame row]`, seconds | only after an arbitrary frame start is named | computable / computable / coarse | P and R use different frame starts today | 0 | **delete**; not online/offline stable |

The 10/50/200 rolling group is a lean ablation candidate because it matches the professor paper's named windows. The paper's Table II says elapsed time is the **number of blocks since dataset start**; current [`_time.py`](../../../src/spice/features/sets/core_fee_dynamics/_time.py) instead computes seconds since the supplied frame start. Neither origin is a stable live fact unless it is made part of the deployed contract. Deleting it is clearer than repairing an arbitrary trend coordinate.

No target-row timestamp, calendar, cadence, elapsed, or realized fee is an input. The single exception is Ethereum's forming fee because it is calculated from `h`, never read from finalized `h+1`.

## Why the legacy catalogs do not survive intact

This table accounts for every current output family in [`conf/features`](../../../src/spice/conf/features):

| Legacy outputs | Current unit and warmup | Finding |
|---|---|---|
| `log_base_fee_per_gas` | log numeric wei/gas; 0 | safe when the ordinary context ends at closed `h` |
| `log_prev_gas_used`, `log_prev_gas_limit`, `prev_gas_utilization`, `log_prev_tx_count` | log numeric gas/count or ratio; 1 | at feature row `j` they read `j-1`; approved geometry makes this safe but needlessly stale. Use coherent unshifted closed-row facts |
| cadence plus four calendar outputs | seconds or ratios; 0/1 | causal only on historical rows; Avalanche cadence is second-quantized |
| fee rolls at 25/100, including minima | log-value moments; 24/99 | overlap the 10/50/200 family without a stated hypothesis; not in the paper's table |
| `dlog_base_fee`, binary trend, six fee lags | log ratio or +/-1; 1-7 | explicit history duplicates sequence input; zero change currently maps to `+1`, so “trend” means nondecreasing vs decreasing |
| six utilization lags | ratio; 2-7 because the base feature is already shifted | same duplication and extra staleness |
| fee rolls at 10/50/200, including minima | log-value moments; 9/49/199 | optional means/stds are defensible; minima need separate evidence. Current std uses `ddof=1` here but `ddof=0` for 25/100 |
| utilization rolls at 10/50/200 | ratio moments; 10/50/200 because the base feature is shifted | optional after unshifting; use one std convention |
| 32 priority outputs | raw wei/gas, log values/ratios, or rolling moments; 1-200 | no selected modern corpus can build them |
| `elapsed_seconds` | seconds from frame start; 0 | offline/live parity failure and paper-unit mismatch |

Current transforms also clip negative counts to zero and nonpositive fees to one before logging. The measured corpora do not need this repair. Validate physical inputs once and fail with block context; do not turn corrupt facts into plausible features.

## Context and whole-sample containment

The current artifact row counts do not mean 600 seconds. In the selected regimes, inclusive sequence spans were:

| Chain | Current rows | Intervals | min / median / max observed span | Mean span |
|---|---:|---:|---:|---:|
| Ethereum | 64 | 63 | 756 / 756 / 840 s | 759.1 s |
| Polygon | 300 | 299 | 523 / 598 / 605 s | 574.8 s |
| Avalanche | 600 | 599 | 594 / 640 / 1,359 s | 689.5 s |

Avalanche has zero-second deltas in the canonical trace because ACP-226 keeps the standard seconds timestamp while adding a separate millisecond header field. A timestamp alone is not a unique origin key. These measurements reject median-derived “600 seconds” as a semantic guarantee; they do not select the final block count `C`.

For a fixed `C`-row context whose first row is `s=h-C+1`, require every source dependency of the features at `s` to remain at or after the regime start `r`, and require `h+K` not to exceed the regime end. With the proposed 200-row unshifted rolling group, the earliest dependency is `s-199`; with the legacy shifted utilization roll it is `s-200`. A direct executable gate is clearer than a generic reserve:

```text
earliest_feature_dependency(sample) >= regime_start
context_end(sample) = h
latest_outcome_dependency(sample) = h + K <= regime_end
```

Equal timestamps are valid. Duplicate heights, gaps, decreasing timestamps, wrong chain ID, null selected fields, nonpositive fee/limit, `gas_used` outside `[0, gas_limit]`, negative counts, and invalid priority ordering/spread must fail. Do not deduplicate, interpolate, pad, shorten, impute, or clip. Partition-file discovery may impose one explicit order during assembly, but a materialized canonical sequence should not be silently “repaired” by feature code.

## Approved offline and live identity boundary

Issue 46 says: “At decision time `τ`, freeze latest closed canonical parent `(h, hash(h))`, infer once, and persist `k` plus intended target `b=h+1+k`.” The owner approved that as a live decision-record requirement, not a mandatory hash column on every offline modeling row.

Offline origins use `(content-bound corpus_id, chain_id, block_number)`. The immutable corpus package binds exact chain/schema/units/regime/range facts, a canonical package/content digest, and every Parquet file's SHA-256; publication rejects the same ID with different content. Existing numeric Parquet remains reusable and is not republished merely to add hashes.

Future acquisition parses `hash` and `parentHash`, validates every adjacent parent link across rows and file boundaries plus ordering, chain, and the finality anchor, then keeps only compact boundary/acquisition evidence. Boundary hashes and contiguous numbers alone would not detect an interior mixed fork, so the acquisition-time link validation is mandatory.

Live decisions separately persist `(h, hash(h)), k, b`, with the parent facts and Ethereum forming-fee scalar bound to the same frozen response. A selected historical hash is retained or fetched only for a concrete physical-header parity, hash join, or reorg claim. Neither an inline hash nor a full hash sidecar is part of the baseline; a later full sidecar requires a concrete thesis claim.

## Reproduction and source trail

Read-only scans used `pl.scan_parquet(...).sort("block_number")` over the three corpus roots recorded in the issue-54 report. Checks covered schema, row and unique-height counts, min/max height and timestamp, adjacent timestamp differences, nulls, fee/limit/count physical domains, optional-field coverage, priority ordering/spread, current artifact spans, the complete Ethereum recurrence, and Polygon's validity bound.

Local implementation evidence:

- [`corpus/contract.py`](../../../src/spice/corpus/contract.py) and [`corpus/validation.py`](../../../src/spice/corpus/validation.py)
- [`features/sets/core_fee_dynamics`](../../../src/spice/features/sets/core_fee_dynamics)
- [`conf/features`](../../../src/spice/conf/features)
- [`acquisition/rpc/client.py`](../../../src/spice/acquisition/rpc/client.py)
- [issue-45 parity prototype](../current-block-action-cross-layer-parity-prototype.md), [Ethereum causality audit](../ethereum-current-row-causality-and-options.md), and [issue-54 coverage](../modern-regime-coverage-and-evidence-periods.md)

Primary protocol/API evidence:

- [Ethereum EIP-1559](https://eips.ethereum.org/EIPS/eip-1559), [`eth_getBlockByNumber`](https://ethereum.github.io/execution-apis/api/methods/eth_getBlockByNumber/), and [`eth_feeHistory`](https://ethereum.github.io/execution-apis/api/methods/eth_feeHistory/)
- Polygon [PIP-79](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/c65ce300229593bea17ff21f569c259121b4dd11/PIPs/PIP-79.md) and [PIP-83](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/9a7feed01afdf6923bfac3dd10bbb4631ed50099/PIPs/PIP-83.md)
- Avalanche [ACP-176](https://build.avax.network/docs/acps/176-dynamic-evm-gas-limit-and-price-discovery-updates) and [ACP-226](https://build.avax.network/docs/acps/226-dynamic-minimum-block-times)
