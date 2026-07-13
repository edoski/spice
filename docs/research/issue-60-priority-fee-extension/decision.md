# Issue 60: minimum defensible priority-fee extension

Status: research evidence for [Issue 60](https://github.com/edoski/spice/issues/60). It makes no corpus, model, evaluator, serving, artifact, or acquisition change.

## Decision

The current clean baseline omits priority-fee inputs, a tip policy, and adjusted accounting. Retain Issue 48's base-fee-only, fixed-`K` counterfactual headline. Do not acquire priority fields, full transactions, or receipts; do not create an ablation, model/evaluator/serving change, tip policy, post-hoc overlay, mempool/MEV/bundle machinery, or inclusion claim now.

This defers priority fees from the foundation. It does not make them irrelevant or permanently excluded. After core preprocessing, training, evaluation, and serving stabilize, reopen one dedicated post-baseline inquiry from map fog with a fresh owner decision on a feature, tip heuristic, and/or post-hoc accounting route.

## Primary semantics

EIP-1559 transactions declare `max_priority_fee_per_gas` and `max_fee_per_gas`. For an included transaction, effective tip is `min(max_priority_fee_per_gas, max_fee_per_gas - base_fee_per_gas)`; the payer pays base fee plus that tip, subject to its cap. The base fee is burned. This makes a realized tip an included-transaction outcome, not a universal inclusion threshold. [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559)

`eth_feeHistory` returns completed-block base-fee and gas-use summaries plus requested `reward` percentiles: transactions are sorted by effective tip per gas, weighted by gas consumed. A client may return a shorter historical range. The extra next-base-fee element is derivable from the newest closed block; the rewards for a target block are not known at a decision before that block. [`eth_feeHistory`](https://ethereum.github.io/execution-apis/api/methods/eth_feeHistory/)

`pending` is only the node's local sample, not a complete network mempool. Full transactions expose caps; receipts expose post-inclusion outcomes. Neither observes unsubmitted, private, dropped, replaced, or bundled transactions. [`eth_getTransactionReceipt`](https://ethereum.github.io/execution-apis/api/methods/eth_getTransactionReceipt/)

Polygon documentation uses `eth_feeHistory` percentiles in its estimator, but that establishes an endpoint convention, not Ethereum-equivalent semantics. Avalanche exposes `eth_feeHistory`, with endpoint availability configuration-dependent. Any future use needs an explicit provider/range/schema probe per selected chain. [Polygon Gas Station](https://docs.polygon.technology/tools/gas/polygon-gas-station) and [Avalanche C-Chain RPC](https://build.avax.network/docs/rpcs/c-chain/eth/eth_feeHistory)

## Current evidence

| Selected modern corpus | Rows | Priority-field coverage |
|---|---:|---:|
| Ethereum | 1,175,689 | 0% |
| Polygon | 1,756,067 | 0% |
| Avalanche | 13,435,499 | 0% |

The only local non-null interval is historical Ethereum blocks 22,664,726–23,765,143 (1,100,418 rows), ending 2025-11-09 and outside the selected regime. Null filling would invent signal. See [Issue 47 availability evidence](../issue-47/issue-47-chain-schema-feature-availability.md).

The legacy catalog has 32 outputs from shifted p10/p50/p90/spread values, p50/spread transforms, lags, and 10/50/200-block rolling statistics; its maximum warm-up is 200 rows. It is not a minimal group and duplicates history already available to the sequence model. [Legacy feature code](../../../src/spice/features/sets/core_fee_dynamics/_priority_fee.py)

The existing adapter already requests only p10/p50/p90 from `eth_feeHistory`, checks exact returned alignment and shape, and fails closed. It does not acquire transactions or receipts. [RPC acquisition](../../../src/spice/acquisition/rpc/client.py)

## Causal availability and claim boundary

| Fact | Available before broadcast for target `b`? | Permitted meaning |
|---|---|---|
| Rewards from completed parents through `b-1` | Yes | Historical gas-weighted realized-tip distribution only |
| Ethereum next base fee derived from `b-1` | Yes | Forming-block base-fee fact only |
| Reward, transaction, or receipt from `b` | No | Hindsight outcome only |
| Node `pending` set | Not defensibly complete | Local-node observation only |
| Receipt for SPICE's submitted transaction | Only after inclusion | Actual observed execution report only |

No row supports a required-tip, inclusion-probability, mempool-completeness, proposer/builder policy, MEV classification, or bundle claim. A near-zero percentile is not an MEV label; empty blocks can yield zero and fee history summarizes only included transactions.

## Four routes

| Route | Smallest possible scope | Result |
|---|---|---|
| Omit entirely | None | **Choose now.** Keeps the clean causal base-fee foundation and no new acquisition. |
| Feature only | One closed-parent p50/spread group, new feeHistory suffix, one validation comparison | Causal but unsupported benefit; duplicates sequence history and reopens the feature budget. |
| Tip/accounting only | Predeclared fixed tip and cap, no retraining | Cannot prove inclusion. When both actions remain cap-valid, the same tip cancels from immediate-versus-selected cost difference; it adds no action evidence. |
| Minimal combined extension | Feature group plus fixed tip/cap | Inherits both costs and neither missing inference becomes observable. |

Issue 47 already approved omission of all priority-fee model inputs and the 32 legacy outputs from the current contract. This research finds no distinct thesis benefit sufficient to reopen that decision before the foundation stabilizes. See [Issue 47 owner record](../issue-47/issue-47-owner-decisions.md#decision-20--omit-priority-fee-model-inputs).

## Why accounting does not survive

Issue 48 defines `B` and `R` as immediate and selected *base fee per gas* outcomes. With one declared gas amount and unchanged tip `q`, valid cap conditions give `(B + q) - (R + q) = B - R`. If a cap fails, the result is an eligibility/missed-execution case, not a fee comparison. Replacing `q` with target-block realized rewards leaks hindsight and describes other included transactions. Receipts report one actual later execution; they cannot recover the counterfactual immediate execution. The base-fee headline therefore remains explicitly non-profit, non-inclusion accounting. [Issue 48 decision contract](../issue-48-temporal-evaluation/decision-contract.md)

## Minimal requirements if scope is redrawn

Do not act on these now. The cheapest future start is one bounded Ethereum `eth_feeHistory` provider/range/provenance probe, followed by a fresh owner decision on feature, tip heuristic, and/or post-hoc accounting. Stop if coverage is unsupported, shortened, or cannot be recorded. Only a surviving decision may require a new content-bound Ethereum suffix acquired once after fields and ranges freeze: p10/p50/p90 effective-tip summaries, exact derived spread, requested percentile vector, returned range, provider/version, endpoint, and acquisition time. `eth_feeHistory` suffices; full transactions or receipts must first prove a separately approved transaction-level estimand.

Preserve existing corpora. Do not extend their identity. Do not plan an Avalanche suffix. Polygon needs independent provider and semantic evidence before any field is requested. Issue 27 owns acquisition/sealing mechanics; Issue 48 owns range need. No downstream ticket graduates now, and Issue 60 does not block Issue 49.
