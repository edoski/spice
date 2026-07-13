# Modern-regime coverage and evidence periods

Status: AFK research for [Measure modern-regime coverage and candidate evidence periods](https://github.com/edoski/spice/issues/54). This report does not select `K`, features, a model, metrics, or owner policy.

## Recommendation

Use one recent, internally consistent regime per chain, then use every eligible origin in that regime for the primary per-chain comparison. Do **not** force equal sample counts across chains: it discards valid information and still fails to equalize cadence, fee level, dependence, or user waiting time. If wanted, add a deterministic equal-count truncation as a clearly labelled sensitivity.

Treat an origin `h` as eligible only when its complete causal span is in the regime: all warmup/context rows through closed parent `h`, and every target `h+1...h+K`. Split by time/block order and purge forward outcomes at each boundary. Freeze the external role before looking at it.

The lean fixed-block candidate is `K in {5, 10, 15, 20}`. It avoids turning empirical seconds into a label definition. It is a candidate range, not a choice from held-out results.

## Material-boundary review

| Chain | Recommended local modern boundary | Why it is material | Scope qualification |
|---|---|---|---|
| Ethereum | First row at/after BPO2: `2026-01-07T01:01:11Z`, block 24,179,383 locally | Fusaka raised L1 capacity; its scheduled BPO1/BPO2 steps then changed blob target/max, with BPO2 setting 14/21. | This is stricter than post-Fusaka. It is required if blob capacity/fee inputs or capacity claims enter the study; a plain EIP-1559-only feature set should state why an earlier boundary is sufficient. |
| Polygon | Giugliano block 85,268,500, local first row `2026-04-08T14:03:57Z` | Bor gates early-announcement transaction prefetching at Giugliano, affecting live availability/propagation claims. | Primary evidence does **not** show a new finalized-block fee recurrence, gas target/limit, cadence rule, or header schema. It is a conservative operational boundary, not proof of a distinct finalized-row process. |
| Avalanche | Granite: `2025-11-19T16:00:00Z`, block 72,240,649 locally | ACP-226 adds millisecond timestamp and dynamic minimum-block-delay state, so cadence and time-sensitive target claims change. | For a strictly block-indexed model with no elapsed-time feature, it is a conservative rather than necessary boundary. |

Ethereum’s official [Fusaka announcement and BPO schedule](https://blog.ethereum.org/2025/11/06/fusaka-mainnet-announcement) gives the activation/BPO times; the [official Fusaka page](https://ethereum.org/roadmap/fusaka/) describes its capacity change. Polygon’s [Giugliano PIP](https://forum.polygon.technology/t/pip-84-giugliano-hardfork/21808), [release notice](https://forum.polygon.technology/t/bor-v2-7-0-and-erigon-v3-5-0-for-mainnet/21830), and [Bor fork configuration](https://github.com/maticnetwork/bor/blob/v2.7.0/params/config.go#L435) support the operational claim, not a fee-rule claim. Avalanche’s [Granite activation record](https://build.avax.network/blog/granite-upgrade) and [ACP-226](https://build.avax.network/docs/acps/226-dynamic-minimum-block-times) support the cadence boundary.

These are protocol-process boundaries, not evidence that targets are stationary. Later changes must be checked before a future external period is sealed.

## Local corpus facts

| Chain | Corpus / provenance | Raw rows and blocks | UTC range | In-regime rows and blocks |
|---|---|---|---|---|
| Ethereum | `cor_7bea5a071afaf090c05a`; PublicNode | 2,923,988; 22,431,084–25,355,071 | 2025-05-07T10:05:11Z–2026-06-19T23:59:59Z | 1,175,689; 24,179,383–25,355,071 |
| Polygon | `cor_61fb33e47c948a9cebd0`; Tenderly community RPC | 13,584,311; 73,440,256–87,024,566 | 2025-07-01T08:48:33Z–2026-05-17T15:44:59Z | 1,756,067; 85,268,500–87,024,566 |
| Avalanche | `cor_3ef359c91addcab77e9f`; PublicNode | 25,776,042; 59,900,106–85,676,147 | 2025-04-08T15:00:00Z–2026-05-17T15:44:59Z | 13,435,499; 72,240,649–85,676,147 |

Each corpus is manifest-validated `clean`. It has unique contiguous block numbers, no block gaps or duplicates, no timestamp decrease, and no null core field, non-positive base fee/gas limit, or `gas_used > gas_limit`. The canonical 14 `Int64` columns include `block_number`, `timestamp`, `base_fee_per_gas`, `gas_used`, `gas_limit`, `tx_count`, size/blob fields, and priority-fee fields.

Timestamps are whole Unix seconds. Ethereum and Polygon timestamps are unique. Avalanche has 70,493 adjacent same-second blocks (25,705,549 unique timestamps), so a timestamp alone is not an origin key. Adjacent timestamp ranges are Ethereum 12–60 s, Polygon 1–620 s, Avalanche 0–25 s. This rules out claiming a uniform seconds-to-block conversion.

The core fee feature set needs the six core columns above. Its largest rolling warmup is 200 rows. Priority-fee features are not cross-chain usable: all Polygon/Avalanche priority fields are null; Ethereum has a complete contiguous segment only through 2025-11-09, before the selected modern regime.

## Conditional eligibility counts

Fixed facts: the currently configured problem is a 600-second lookback with a 36-second maximum delay; current artifacts have fixed contexts of 64 Ethereum, 300 Polygon, and 600 Avalanche rows. These are not approved final semantics. The tables reserve these as a conservative working assumption, plus the 200-row feature warmup.

For a contiguous `N`-row regime, let `W=200`, `C` be the final fixed context reservation, and use target rows `h+1...h+K`. Then:

```text
first eligible h = first_regime_row + W + C
last eligible h  = last_regime_row - K
eligible(N, W, C, K) = N - W - C - K
```

Here `C` is the number of past rows reserved before `h`; the inclusive origin interval is `[first_regime + W + C, last_regime - K]`, which gives the displayed formula. This deliberately requires all causal history to remain in-regime. With a time-based context, replace `C` with the actual earliest in-regime context index per origin; do not estimate it from nominal cadence.

| Chain (`C`) | K=5 | K=10 | K=15 | K=20 |
|---|---:|---:|---:|---:|
| Ethereum (64) | 1,175,420 | 1,175,415 | 1,175,410 | 1,175,405 |
| Polygon (300) | 1,755,562 | 1,755,557 | 1,755,552 | 1,755,547 |
| Avalanche (600) | 13,434,694 | 13,434,689 | 13,434,684 | 13,434,679 |

Counts are conditional, not results from the current time-window compiler: its variable candidate span and unpurged chronological split are not fixed-`K` evidence. The fixed-row report must recompute eligibility after final context/features are approved.

## Concrete provisional evidence periods

For planning only, use `K=20` to set conservative chronological role boundaries: 60% train, 15% validation/tuning, 10% internal test, and the final 15% sealed external evaluation. This is an allocation convention, not a sufficiency result. The default **target-only purge** ends an earlier role 20 origins before the next role begins, so its targets cannot enter the later role. The omitted 60 origins across three boundaries are the purge. Past context may legally read earlier-role rows: it is causal history, not a future label. If an owner instead requires no raw-row overlap at all, use a stricter `K+C` boundary gap and recompute every count; do not call that a target-leakage requirement.

| Chain | Train origins | Validation origins | Internal-test origins | Sealed external origins |
|---|---|---|---|---|
| Ethereum | 24,179,647–24,884,869 (705,223) | 24,884,890–25,061,179 (176,290) | 25,061,200–25,178,720 (117,521) | 25,178,741–25,355,051 (176,311) |
| Polygon | 85,269,000–86,322,307 (1,053,308) | 86,322,328–86,585,639 (263,312) | 86,585,660–86,761,193 (175,534) | 86,761,214–87,024,546 (263,333) |
| Avalanche | 72,241,449–80,302,235 (8,060,787) | 80,302,256–82,317,437 (2,015,182) | 82,317,458–83,660,905 (1,343,448) | 83,660,926–85,676,127 (2,015,202) |

For another `K`, retain the same declared role starts, move each earlier role end back by the actual `K`, and recompute its last origin as `last_block-K`. This keeps all targets in-role. A final configuration must freeze these boundaries before external replay. Fit/tune only on train/validation; use the internal test once for the frozen development decision; run external origins once, exhaustively, with three predeclared seeds and report all seeds rather than selecting the best.

The available counts are ample for fitting, validation, an internal test, three seeds, and exhaustive once-per-origin external replay. Divide each frozen external tail into three contiguous, non-overlapping reported subperiods before scoring; they provide period variation but not independent deployment draws. They do not make adjacent origins independent. No acquisition is needed for this bounded plan. It is not enough for an additional, chronologically later sealed regime period after the present tail: the smallest acquisition is a contiguous suffix immediately after each corpus tail, with the six existing core fields, long enough for one predeclared external window plus `W+C+K` history. Add Avalanche millisecond timestamp and minimum-delay state only if the approved feature/claim requires cadence-exact semantics.

## Evaluation windows

The existing 300- and 1,200-block definitions remain useful only as frozen, named, regime-contained reporting windows. They are not `K`: old block-Poisson replay config uses a 300/1,200 block window with repeated simulated arrivals, whereas fixed `K` is a per-origin choice among the next `K` blocks. Exhaustive origins estimate a block-origin estimand, not arrival-weighted performance. Keep both widths only when selected before outcomes; otherwise use a few non-overlapping named windows plus the exhaustive external period.

## Reproduction and limits

Run these read-only commands from the repository root:

```sh
sqlite3 -header -column outputs/corpora/ethereum/cor_7bea5a071afaf090c05a/.spice/state.sqlite \
  'select * from dataset_manifest; select * from acquire_runs;'

uv run python - <<'PY'
import polars as pl
for name, path, predicate in [
    ('ethereum', 'outputs/corpora/ethereum/cor_7bea5a071afaf090c05a/blocks/*.parquet', pl.col('timestamp') >= 1767747671),
    ('polygon', 'outputs/corpora/polygon/cor_61fb33e47c948a9cebd0/blocks/*.parquet', pl.col('block_number') >= 85268500),
    ('avalanche', 'outputs/corpora/avalanche/cor_3ef359c91addcab77e9f/blocks/*.parquet', pl.col('timestamp') >= 1763568000),
]:
    print(name, pl.scan_parquet(path).filter(predicate).select(
        pl.len(), pl.col('block_number').min(), pl.col('block_number').max(),
        pl.col('timestamp').min(), pl.col('timestamp').max()).collect())
PY
```

The professor paper and historical Poisson outputs are context only. They cannot approve fixed-`K` semantics. Owner decisions still required: final information set, block-vs-time context, exact `K`, feature set, whether Polygon’s operational boundary is necessary for the final claim, final metrics, and the sealed-window list.

Local evidence: `src/spice/conf/problem/current_row_nominal.yaml`, `src/spice/features/sets/core_fee_dynamics/_fee_context.py`, `src/spice/modeling/dataset_builders/fixed_sequence_temporal.py`, `docs/research/issue-1/temporal-preprocessing-theory-audit.md`, and `docs/research/fixed-block-comparability-and-exhaustive-replay.md`.
