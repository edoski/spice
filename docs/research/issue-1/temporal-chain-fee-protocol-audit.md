# Temporal chain fee-protocol and decision-time audit

**Status:** investigation map; no route, code change, ADR replacement, or documentation claim in this report is approved.

**Scope:** the protocol facts needed to justify SPICE's intentional offset-zero/current-forming-block task on Ethereum, Polygon PoS, and Avalanche C-Chain; the protocol regimes crossed by the current corpora; feature availability; submission and inclusion timing; and parity with Sepolia serving.

**Priority:** theory correctness first. Among correct routes, prefer the one with the smallest concept count and the clearest undergraduate-level explanation. Protocol-specific machinery is not justified merely because it can reproduce more fields.

## Verdict

The current-row design is not uniformly valid or invalid. It is a coherent intentional extension, but the historical justification in commit `e0b2e68e`, `PROGRESS.md`, `ARCHIVE.md`, and the feature documentation generalizes an Ethereum fact too far.

For an Ethereum child block, EIP-1559 determines the base fee from the parent header. Polygon used closely related fixed recurrences during earlier corpus regimes, but the corpus crosses Lisovo, after which the gas target and base-fee denominator are producer-configurable within a bounded rule. Avalanche ACP-176 does not use the Ethereum parent gas-used recurrence: its child base fee depends on fee state encoded in the parent header and on the child's timestamp; Granite additionally changes the relevant time precision to milliseconds. The current canonical Avalanche corpus does not retain all of that state.

The lean correction is therefore not “shift offset zero” by default. The user has explicitly identified offset zero as the current/forming block, and that decision remains a first-class candidate. It must instead be stated as a decision-time contract and proved per chain and protocol era. A finalized historical value is a valid input for an open block only when the live system can construct the same value before a newly submitted transaction's inclusion opportunity closes.

There are two independent questions:

1. **Can the value be computed or observed before block execution?** This is a feature-causality question.
2. **Can a public transaction submitted then still be included in that block?** This is an actionability question.

A chain field may pass the first and fail the second. No base-fee formula guarantees inclusion: nonce validity, fee cap, priority fee, propagation, builder/proposer selection, and remaining block capacity still matter.

The immediate blockers are:

| Priority | Finding | Consequence |
|---|---|---|
| Blocker | “Current base fee is deterministic from the parent” is true for Ethereum but not a cross-chain invariant | One shared finalized-row implementation cannot be called a proved block-open representation |
| Blocker | Serving reads a block at `latest - confirmation_depth` and targets `observed + k + 1` | With the default depth of two, its baseline and earliest targets are already behind the latest head and are not actionable |
| Major | The current feature row uses the realized target-row timestamp and cadence | Those facts are not generally available to a public submitter while the target block remains open |
| Major | Polygon and Avalanche corpora cross material fee/cadence regimes without representing them explicitly | Training and evaluation aggregate different data-generating rules under one chain label |
| Major | Required Polygon/Avalanche protocol state is absent from the canonical schema | Exact retrospective/open-row reconstruction would require new acquisition fields or a leaner feature contract |

No production file, ADR, issue, corpus, artifact, or existing report was changed by this investigation.

## The decision contract that needs proof

Use distinct symbols for distinct physical states:

```text
h        latest fully closed block whose execution facts are available
t=h+1    candidate forming/open block
tau      public user's decision/submission time
k=0      intentional action: try to submit for t
k>0      wait through later action opportunities
```

Under this interpretation, an offline row labeled `t` is not simply a historical block row. It is a **virtual block-open row**. Every value in that row needs an `available_at` proof. Finalized `gas_used[t]`, `transaction_count[t]`, and similar outcomes are forbidden; the implementation correctly replaces them with facts from `h`. The same discipline must cover base fee, timestamp, chain-specific header state, and the exact time at which a transaction can still reach `t`.

The current compiler includes the anchor itself as the first candidate (`candidate_start_rows = anchor_candidates`) at `src/spice/temporal/compilers/observed_time_window.py:352-364`. That matches the intentional `k=0 -> t` definition. It does not, by itself, create a virtual open row: the feature table was built from finalized rows.

## Corpus and protocol map

The local materialized corpora are not single-regime datasets. The following boundaries were cross-checked against their manifests, canonical rows, official upgrade announcements, and implementation sources. Row counts and first/last timestamps are local-artifact facts, not network-wide claims.

| Chain and local corpus | Local coverage | Material boundaries inside coverage | Audit implication |
|---|---|---|---|
| Ethereum `cor_7bea...` | 2,923,988 rows; block 22,431,084 at 2025-05-07 10:05:11 UTC through block 25,355,071 at 2026-06-19 23:59:59 UTC | Pectra begins at first row; Fusaka/Osaka execution begins at block 23,935,694 on 2025-12-03 | Fee recurrence remains EIP-1559, but gas capacity and the surrounding distribution change; a “Pectra” corpus name hides a post-Fusaka regime |
| Polygon PoS `cor_61fb...` | 13,584,311 rows; block 73,440,256 at 2025-07-01 08:48:33 UTC through block 87,024,566 at 2026-05-17 15:44:59 UTC | Bhilai, Rio, Madhugiri, Dandeli, Lisovo at block 83,756,500 on 2026-03-04, 120M gas-limit expansion, and Giugliano at block 85,268,500 on 2026-04-08 | Fee parameters, target utilization, producer behavior, gas capacity, and cadence are not stationary |
| Avalanche C-Chain `cor_3ef...` | 25,776,042 rows; block 59,900,106 at 2025-04-08 15:00:00 UTC through block 85,676,147 at 2026-05-17 15:44:59 UTC | Starts exactly at Octane/Fortuna activation; Granite activates 2025-11-19 16:00 UTC | Entire corpus uses ACP-176 dynamic fees; the latter portion also uses Granite's millisecond header time and dynamic minimum block delay |

Primary upgrade evidence: Ethereum's [Pectra overview](https://ethereum.org/roadmap/pectra/) and [Fusaka mainnet announcement](https://blog.ethereum.org/2025/11/06/fusaka-mainnet-announcement); Polygon's [Bhilai proposal](https://forum.polygon.technology/t/pip-63-bhilai-hardfork/20872), [Rio proposal](https://forum.polygon.technology/t/pip-73-rio-hardfork/21268), [Dandeli client release](https://forum.polygon.technology/t/bor-v2-5-6-and-erigon-v3-3-6/21547), [Lisovo proposal](https://forum.polygon.technology/t/pip-81-lisovo-hardfork/21713), and [Giugliano announcement](https://polygon.technology/blog/giugliano-upgrade-faster-confirmations-predictable-fees-and-a-more-resilient-network-for-polygon-chain); Avalanche's [ACP-176](https://build.avax.network/docs/acps/176-dynamic-evm-gas-limit-and-price-discovery-updates) and [Granite activation announcement](https://build.avax.network/blog/granite-upgrade).

### Observed cadence is descriptive, not a protocol constant

A read-only scan of consecutive local timestamps found:

| Corpus | Mean observed delta | Median | 95th percentile | Qualification |
|---|---:|---:|---:|---|
| Ethereum | about 12.1 s | 12 s | 12 s | Missed slots create longer gaps; 12 s is the beacon slot duration, not a guarantee that every slot has an execution block |
| Polygon | roughly 1.92-2.16 s by sampled upgrade segment | 2 s in each segment | varies | Lisovo-to-Giugliano remains 99.9997% 2 s deltas; the material 1 s share begins after Giugliano (7.7718%, mean 1.92229 s). Lisovo is the separate fee-configurability boundary. |
| Avalanche | 1.354 s | 1 s | 3 s | 0.273% of adjacent canonical rows share a Unix second; Granite makes millisecond precision protocol-relevant |

The config values `12.0`, `2.0`, and `1.6` seconds can be useful modeling estimates. They should not be presented as one kind of fact across chains. Ethereum's value is a protocol slot duration. Polygon's and Avalanche's are empirical/configuration approximations whose meaning changes across upgrades. In particular, Avalanche's dynamic minimum block delay makes `1.6` neither a fixed protocol interval nor an exact mapping from a block offset to elapsed seconds.

## Cross-chain verdict

| Chain/regime | Exact child base fee from currently stored closed-parent columns? | Is the target-row timestamp known while a public transaction can still target it? | What offset zero would require |
|---|---|---|---|
| Ethereum Pectra/Fusaka | Yes: parent base fee, gas used, and gas limit are sufficient under EIP-1559 | The next scheduled beacon slot is known, but whether a slot is missed and which future non-empty slot includes the transaction are not | Synthesize the open row from `h`; use a declared scheduled-slot/decision-time feature rather than finalized `timestamp[t]`; treat inclusion as eligibility, never certainty |
| Polygon Bhilai through pre-Lisovo fixed-parameter eras | Yes if the correct fork-specific gas target and denominator are supplied | No general proof that finalized `timestamp[t]` is known early enough | Fork-aware recurrence plus decision-time clock; prove submission cut-off and exclude realized target-row timestamp |
| Polygon Lisovo before Giugliano | No: producers can choose bounded gas parameters and current canonical rows do not expose the choice | No | Either acquire/derive producer configuration before action, scope out this era, or omit the exact current-fee feature |
| Polygon Giugliano onward | Not from current canonical columns; the parameters are embedded in the child header and queryable | Observing a built/signed child header does not imply a new transaction can still enter that child | Prove an earlier actionable announcement/API, or treat header values as post-close for public submission; historical acquisition can still reconstruct the regime |
| Avalanche Octane before Granite | No: ACP-176 needs parent dynamic-fee state plus child time, and the canonical corpus lacks the parent extra state | Child time is a producer/header choice, not a public-user fact guaranteed before inclusion | Acquire parent extra state and define a causal child-time estimate, or omit exact current fee |
| Avalanche Granite onward | No: parent extra state plus millisecond child time are needed; current schema stores seconds | No exact public-user value | Acquire `timestampMilliseconds` and dynamic fee state for retrospective reconstruction, but expose only a live-computable estimate unless actionability is proved |

This matrix is deliberately stricter than “the formula can be implemented.” Offline reproducibility, live observability, and same-block actionability are three separate properties.

## Ethereum

### Fee recurrence

[EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) validates an execution block's base fee against its parent. Apart from the fork-initialization case, the child fee uses the parent base fee, parent gas used, and parent gas target derived from the parent gas limit and elasticity. Integer rounding and the minimum upward change are specified. The execution payload's transactions do not determine their own block's already-fixed base fee.

This supports the narrow historical claim behind `current_base_fee_per_gas[t]`: for Ethereum, a virtual child fee can be computed exactly from closed parent `h` before executing `t`. It does not justify reading the finalized child row in generic code unless a parity test proves that the live row constructor performs the same recurrence.

Pectra and Fusaka do not invalidate the EIP-1559 recurrence in this corpus. Fusaka did, however, raise the execution gas-limit default toward 60 million, changing capacity and potentially feature/target distributions; see the [Fusaka checkpoint update](https://blog.ethereum.org/2025/11/15/checkpoint-7). Results should therefore record the fork boundary even if no separate fee formula is needed.

### Timestamp and submission

Ethereum consensus uses 12-second slots; the execution payload timestamp is derived from the beacon slot in the [consensus specification](https://github.com/ethereum/consensus-specs/blob/master/specs/phase0/beacon-chain.md). A public user after closed block `h` can know the next scheduled slot time. The user cannot know that a particular future slot will produce a block or guarantee that the transaction reaches its proposer/builder before selection closes.

A lean causal replacement for finalized `timestamp[t]` is therefore one of:

- the decision wall-clock time `tau`, encoded cyclically if calendar features survive ablation;
- the next scheduled slot time, with a documented missed-slot interpretation; or
- no target-row cadence/calendar feature at all.

The last option has the smallest theory surface and should be the baseline. Keeping five time features is justified only if an ablation shows useful generalization and their live construction is identical.

### Eligibility is not inclusion

Ethereum's [transaction documentation](https://ethereum.org/developers/docs/transactions/) describes submission to the transaction pool and validator selection; the [gas documentation](https://ethereum.org/developers/docs/gas/) explains that the fee cap must cover base fee plus priority fee. For an offset-zero attempt to be eligible for `t`, at minimum:

- `tau` must precede the builder/proposer's effective transaction cut-off;
- the transaction must propagate to the relevant selection path;
- nonce and balance must be valid;
- `maxFeePerGas >= baseFee[t] + effectivePriorityFee`; and
- capacity and proposer policy must admit it.

These are eligibility conditions. SPICE should never document them as a next-block guarantee.

## Polygon PoS

### The corpus contains several distinct regimes

Bhilai activated at local block 73,440,256. Its protocol proposal moved the base-fee change denominator to 64, raised the block gas limit to 45 million, and retained a 50% gas target. Rio later changed block production/validation architecture and priority-fee distribution. Madhugiri changed consensus-period configuration. Dandeli changed the gas target to 65% while retaining denominator 64. These changes matter even before configurable gas parameters arrive.

Lisovo activated at block 83,756,500. [PIP-79](https://forum.polygon.technology/t/pip-79-bounded-range-validation-for-configurable-eip-1559-parameters/21711) and the [Lisovo client announcement](https://forum.polygon.technology/t/bor-v2-6-0-and-erigon-v3-4-0-for-mainnet-and-amoy/21757) allow block producers to configure EIP-1559 target/denominator behavior subject to a bounded parent-relative base-fee change. Bor v2.6.0's [EIP-1559 validation implementation](https://github.com/0xPolygon/bor/blob/v2.6.0/consensus/misc/eip1559/eip1559.go) checks this bounded rule; its [configuration](https://github.com/0xPolygon/bor/blob/v2.6.0/params/config.go) identifies the fork-dependent parameters.

This is the decisive correction to the generic parent-determinism premise. After Lisovo, the parent header and one universal target/denominator pair do not uniquely identify the child's base fee.

### The configurability is present in the data, not merely theoretical

A read-only replay compared consecutive canonical Polygon fees with the fixed post-Dandeli recurrence (65% target, denominator 64), using Bor's integer behavior. The fixed recurrence continued to match through block 84,072,255. At block 84,072,256, 2026-03-11 21:29:05 UTC, observed fees first departed from that recurrence. Across the remaining post-Lisovo portion, 2,945,908 of 3,268,067 child fees, 90.14%, differed from the fixed formula; the maximum observed parent-relative change was 5%, matching the bounded design.

This diagnostic does not infer each producer's private configuration and does not make block 84,072,256 a protocol fork. Lisovo is the fork. The later row is the first observed departure in this corpus and proves that a single fixed recurrence is materially wrong for actual training rows.

### Giugliano improves transparency but does not automatically prove actionability

Giugliano activated at block 85,268,500 on 2026-04-08. Polygon's [official announcement](https://polygon.technology/blog/giugliano-upgrade-faster-confirmations-predictable-fees-and-a-more-resilient-network-for-polygon-chain) says PIP-83 embeds gas target and base-fee denominator in each post-Giugliano block header and exposes them through `bor_getBlockGasParams` and optional Bor header data. That makes historical reconstruction and after-header observation cleaner.

It does not follow that a public transaction submitted after seeing those child-header parameters can still enter that same child block. PIP-66 announces block headers approximately 44 ms earlier in propagation, but a header for an already built/signed block is not an open transaction-selection window. SPICE needs evidence of a pre-build parameter announcement available to the submitting client before it can use those child parameters as offset-zero inputs.

### Polygon inclusion constraints

Polygon's [PoS EIP-1559 documentation](https://docs.polygon.technology/pos/concepts/transactions/eip-1559) describes the network's EIP-1559 behavior, while the [Gas Station documentation](https://docs.polygon.technology/tools/gas/polygon-gas-station) documents operational fee recommendations and a network minimum-priority policy. These client/network policies are not encoded by base fee alone. A transaction with a valid fee cap can still miss the intended block because of propagation, producer selection, nonce order, or capacity.

For leanness, do not add a large Polygon adapter until the owner chooses among these candidates:

1. **Era-scoped exact route:** preserve offset zero only for fixed-parameter ranges and train/evaluate configurable eras separately.
2. **Decision-time estimate route:** retain all eras, replace actual `base_fee[t]` with a live-computable estimate or parent fee, and train on that same representation offline.
3. **No current-fee route:** remove current-row fee/trend values and let the sequence end at closed parent `h`; keep `k=0` as an action, not as a finalized feature row.
4. **Protocol-state route:** acquire producer parameters and prove they are available before transaction selection. This is the most exact and most complex candidate; reject it unless it earns that complexity.

## Avalanche C-Chain

### ACP-176 is not the Ethereum recurrence

The Avalanche corpus starts exactly when Octane/Fortuna activates [ACP-176](https://build.avax.network/docs/acps/176-dynamic-evm-gas-limit-and-price-discovery-updates). ACP-176 tracks dynamic gas capacity, excess, and target-excess state over time. Coreth v0.15.1's [`base_fee.go`](https://github.com/ava-labs/coreth/blob/v0.15.1/plugin/evm/header/base_fee.go) and [`dynamic_fee_state.go`](https://github.com/ava-labs/coreth/blob/v0.15.1/plugin/evm/header/dynamic_fee_state.go) derive the next state and base fee using parent-header extra state and elapsed time to the child.

Consequently, the current canonical columns—block number, Unix-second timestamp, base fee, gas used, gas limit, and transaction facts—are insufficient to reconstruct a child base fee exactly. The finalized `base_fee_per_gas[t]` is an outcome unless a virtual row constructor also receives the parent dynamic-fee state and a causal child-time value.

Coreth's own estimation API names this distinction: a next-base-fee estimate can change if another block is produced before the caller's transaction. Avalanche's [transaction fee guide](https://build.avax.network/docs/rpcs/other/guides/txn-fees) and [C-Chain API](https://build.avax.network/docs/rpcs/c-chain/api) should therefore be treated as estimation/submission interfaces, not exact inclusion promises.

### Granite makes second-resolution rows insufficient

Granite activated on mainnet at 2025-11-19 16:00 UTC and implements [ACP-226](https://build.avax.network/docs/acps/226-dynamic-minimum-block-times). It adds `timestampMilliseconds` and dynamic minimum-delay state. Coreth v0.16.0's [`dynamic_fee_state.go`](https://github.com/ava-labs/coreth/blob/v0.16.0/plugin/evm/customheader/dynamic_fee_state.go) and [`time.go`](https://github.com/ava-labs/coreth/blob/v0.16.0/plugin/evm/customheader/time.go) use the custom header time when advancing fee state.

The corpus stores integer seconds. Adjacent rows can therefore have equal canonical timestamps even though protocol order and elapsed milliseconds differ. The loss is not cosmetic: time advances fee capacity/excess state. Exact post-Granite replay requires the original millisecond timestamp and parent extra state.

### Lean candidates

1. **Closed-parent representation:** end model inputs at `h`, keep offset zero as “submit now for the earliest eligible block,” and do not pretend `base_fee[t]` is known. This has the smallest chain-specific surface.
2. **Native estimate representation:** record the same Coreth/RPC estimate both offline and live, including an explicit `is_estimate` meaning. Backfill raw headers only if required to reproduce historical estimates.
3. **Exact protocol replay:** acquire raw header extra state and millisecond timestamps and implement/version ACP-176/226 transitions. This is scientifically strongest for protocol baselines but much less lean as a neural-model input path.

The exact replayer is valuable as a benchmark even if it is rejected as production feature machinery. It can quantify how much predictive value the neural model adds beyond protocol state. It should not be introduced until a small prototype demonstrates that the native library/API cannot provide the same baseline more clearly.

## Feature availability audit

The default core feature set contains 45 outputs. Its row-level safety is mixed:

| Feature group | Current implementation | Block-open verdict |
|---|---|---|
| Current base fee and same-row fee delta/trend | Reads finalized `base_fee_per_gas[t]`; delta and rolling transforms include it (`_base_fee.py:16-73`) | Ethereum can synthesize it; Polygon is regime-dependent; Avalanche cannot from current canonical fields |
| Gas used, gas limit, transaction count | Shifts source columns by one row (`_block_facts.py:27-83`) | Correct in principle: values at virtual `t` represent closed parent `h` |
| Priority-fee context | Shifted to previous-block facts | Causal if the live RPC acquires exactly the same transaction population and statistic |
| `seconds_since_previous_block` | Uses `timestamp[t] - timestamp[h]` (`_time.py:27-34,57-65`) | Finalized target-row fact; unsafe for a generic public block-open row |
| Hour/day cyclic values | Uses finalized `timestamp[t]` (`_time.py:37-54,66-93`) | Replace with decision time or scheduled-slot time, or remove |
| `elapsed_seconds` option | Uses finalized timestamp relative to corpus origin (`_time.py:21-24,97-105`) | Corpus-position feature with no stable live semantic; strongest candidate for deletion |

The important simplification is conceptual: `k=0` does not require model context to include a physical target row. An action can mean “submit now for the current/earliest eligible block” while the sequence contains facts only through closed parent `h`. This decouples **what the model knows** from **which action it chooses** and avoids inventing target-row feature values. It is a candidate interpretation compatible with the user's intentional immediate/current action, but it changes the historical same-row feature representation and needs approval.

If the virtual-row route is retained, require a per-feature table with these fields:

```text
feature_name | physical_source | available_at | offline_constructor
live_constructor | chain_regime | exact_or_estimate | parity_test
```

Without this table, “causal” remains too broad to verify.

## Serving and Sepolia

### Current serving clock is not the training clock

Serving fetches `latest`, subtracts `confirmation_depth`, and ends its feature window at that old confirmed block (`src/spice/serving/live_blocks.py:51-65`). It builds features from finalized rows, makes the last row the model anchor, then reports:

```text
observed block       h
selected offset      k
broadcast after      h + k
target               h + k + 1
baseline             h + 1
```

The mapping is explicit at `src/spice/serving/inference.py:63-108,144-198`. Offline training instead uses anchor/candidate `h` itself. The two clocks are not equivalent.

More seriously, with default `confirmation_depth = 2`, suppose RPC latest is `L`. Serving observes `h=L-2`; its baseline `h+1=L-1` is already closed, and offset-zero target `h+1` is also already closed. Waiting “after block h” is impossible because that event is in the past. This is an operational correctness defect independent of which offline contract the owner selects.

### Ethereum-mainnet training to Sepolia serving

Sepolia currently shares the EIP-1559 execution recurrence and 12-second beacon-slot family, and it has crossed corresponding Pectra/Fusaka testnet upgrades. That gives protocol-family compatibility. It does not give distributional or performance equivalence:

- gas demand, priority behavior, empty-block frequency, users, and capacity utilization differ;
- Sepolia has had upgrade-specific incidents, including the [Pectra testnet incident](https://blog.ethereum.org/2025/03/05/sepolia-pectra-incident);
- mainnet evaluation metrics cannot be presented as Sepolia serving validation; and
- a live demo should state that it is a protocol-compatible transfer experiment.

The lean serving repair candidate is to separate three numbers explicitly: `latest_rpc_head`, `last_finalized_context`, and `first_actionable_target`. If confirmation depth remains for stable context, the first actionable target must be computed from the current head/decision time, not by adding one to the old context anchor. If the model requires a virtual current row, serving must synthesize it; if inputs end at the closed parent, serving must map “submit now” to the next actionable inclusion opportunity.

Do not solve this with an unexplained constant offset. A three-block executable fixture should prove the whole mapping.

## Corrections required in the surrounding investigation map

These are proposed corrections, not automatic edits:

1. Replace every blanket statement that an “EIP-1559-like” current fee is deterministic from the parent with a chain-and-regime claim.
2. Do not characterize the offline `k=0` definition as an accidental one-block label error. Commit `e0b2e68e` proves it was intentional. The confirmed defect is that the historical finalized row has not been fully reconstructed as a live block-open information set and serving implements another clock.
3. Qualify `base_fee[t]` as exact only for Ethereum and fixed-parameter Polygon regimes with the right fork configuration. Mark configurable Polygon and Avalanche values as requiring additional state or estimation.
4. Treat realized `timestamp[t]` and `seconds_since_previous_block[t]` as unresolved leakage/availability risks in all forming-block routes.
5. Record corpus protocol boundaries in artifact metadata and evaluations. Chain name and a broad date label are insufficient.
6. Treat configured slot spacing as a modeling/presentation parameter, not one universal protocol guarantee.
7. Describe Sepolia serving as a protocol-compatible demonstration until its target clock and transfer performance are validated.

In particular, `docs/research/issue-1/temporal-preprocessing-theory-audit.md` correctly recovered the current-row intent but should absorb this report's final chain verdicts. `docs/research/issue-1/temporal-paper-alignment-audit.md` should retain its distinction between paper-next-block semantics and the intentional extension, while replacing preliminary chain qualifications with the regime map above. Historical ADRs and progress notes remain evidence of intent, not correctness authority.

## Candidate routes for owner approval

### Route A: universal closed-parent inputs, immediate action

Model context ends at closed block `h`. Offset zero means “submit immediately for the earliest block that is still actionable at `tau`.” The action/outcome layer, not the feature row, maps that submission to an eventual block.

Advantages: one information-set concept across chains; no invented child timestamp; no exact Avalanche/Polygon child-state acquisition; easiest to teach and serve. Cost: it changes the historical claim that the sequence includes a current/open row and may modestly reduce predictive signal.

This is the leanest candidate and should be the baseline, not an automatic decision.

### Route B: chain-aware virtual open row

Preserve physical forming block `t` as both feature anchor and offset-zero target. Implement a versioned constructor per chain/regime:

- Ethereum: exact EIP-1559 child fee plus decision/scheduled-slot time;
- Polygon: fixed recurrence where applicable, explicit configurable parameters/estimate elsewhere;
- Avalanche: parent dynamic-fee state plus causal child-time estimate.

Advantages: closest to recovered intent. Cost: more acquisition fields, chain adapters, regime metadata, and exact-versus-estimate concepts. It is only simpler than route A if mature native APIs eliminate most custom logic.

### Route C: explicit per-chain problem contracts

Use a virtual current row where provable and closed-parent/next-action semantics elsewhere. Advantages: maximum protocol honesty. Cost: artifacts and metrics no longer share one simple task; cross-chain comparisons become harder to explain. For an undergraduate thesis, this burden may outweigh the gain.

### Route D: next-block paper contract

Make `h` closed context and class zero the next eligible block. This aligns more directly with the paper and the intended economic baseline, but it changes the user's current-block extension. Keep it as an explicit comparator; do not silently supersede the extension.

## Owner gates and proof obligations

Before implementation, the owner should approve:

1. Whether “current block” means physical forming block `t`, or an immediate submission action whose first eligible realized block is determined later.
2. Whether one universal information set is more important than exact per-chain child-state modeling.
3. Whether protocol eras are split into separate artifacts/evaluations or represented inside one corpus with regime metadata.
4. Whether exact current-fee state earns the acquisition and adapter complexity on Polygon/Avalanche.
5. Whether target-row calendar/cadence features survive ablation; if yes, which decision-time value replaces the finalized timestamp.
6. Whether Sepolia is demo-only or expected to support performance claims.

Whichever route is selected must pass one small, human-readable fixture per chain/regime. Each fixture should contain:

```text
closed parent and close time
decision time tau
protocol state visible at tau
virtual/current row values, if any
submission time
first actionable target
fee-cap and priority assumptions
selected action k
realized inclusion or explicit miss
offline label, replay result, and serving response
```

The fixture is more valuable than broad transition tests because it states the theory in executable form.

## Wayfinder ticket implications

The overall map should add or sharpen these investigation nodes; none should be auto-approved or marked as superseding prior decisions:

- **Decision-instant contract:** choose physical forming-block versus immediate-action semantics and write the three-block fixtures.
- **Protocol-era manifest:** record fork/regime boundaries in corpus/artifact metadata; decide split, stratification, or scoped support.
- **Open-row prototype:** compare universal closed-parent inputs with the smallest chain-aware virtual-row constructor before committing to adapters.
- **Acquisition feasibility:** determine whether existing RPC/library APIs can supply Polygon gas parameters and Avalanche raw extra/millisecond time more clearly than custom parsing.
- **Protocol baseline:** benchmark Ethereum's exact recurrence, Polygon's era-aware recurrence/estimate, and Avalanche's native estimate/replay against persistence and the neural model.
- **Serving parity:** separate context head from actionable head, resolve confirmation depth, and share one action/outcome mapper with offline evaluation.
- **Feature ablation:** start with closed fee/history and lagged utilization; test whether decision-time calendar/cadence features add enough value to justify their concepts.
- **Documentation repair:** after owner approval, modernize architecture/implementation notes and historical claims with the chosen contract and regime table.

The protocol baseline is especially important for thesis clarity. A neural model should be compared with what the protocol itself already makes predictable. If a mature client/RPC estimate is as useful as a custom adapter, prefer the mature API. If a closed-parent model performs similarly to a virtual-row model, prefer the closed-parent model.

## Evidence and limitations

The investigation used:

- local feature, compiler, evaluation, serving, configuration, manifest, and canonical-corpus code/data;
- commit `e0b2e68e`, `PROGRESS.md`, `ARCHIVE.md`, and existing architecture/implementation notes;
- the paper as project foundation rather than correctness authority;
- official EIP/ACP/PIP specifications, official network announcements/documentation, and pinned client implementations; and
- read-only numerical checks of corpus coverage, timestamp deltas, and Polygon recurrence matches.

The local numerical diagnostics should become reproducible analysis commands if they are used in the thesis. They were designed to expose semantic scale, not to produce publication-ready confidence intervals. Historical Polygon producer configuration was not inferred. Exact public transaction cut-off behavior is builder/producer and network-path dependent; this report therefore states eligibility conditions rather than promising same-block inclusion.

The principal conclusion does not depend on those empirical estimates: the pinned primary implementations establish that Ethereum, configurable Polygon, and ACP-176/226 Avalanche do not share one parent-only child-base-fee information contract.
