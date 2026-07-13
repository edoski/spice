# Issue 47 Ethereum regime-anchor red team

Status: bounded planning evidence for [issue 47](https://github.com/edoski/spice/issues/47). This report changes no corpus, implementation, artifact, or owner decision.

## Verdict

Withdraw BPO2 as the Ethereum eligibility anchor. For Issue 47's actual execution-base-fee and retained-feature contract, the earliest defensible local anchor is the first Pectra block in `cor_7bea5a071afaf090c05a`: block **22,431,084**, timestamp **2025-05-07T10:05:11Z** (`1746612311`). The corpus manifest starts exactly there and contains 2,923,988 contiguous rows through block 25,355,071.

This recommendation defines a feature-semantic regime, not a stationary-distribution claim and not a promise that Ethereum's entire execution protocol is unchanged. Pectra-to-Fusaka changes can alter transaction mix, gas use, gas limit, and fee distributions. They do not alter the approved feature construction, units, causal availability, or EIP-1559 execution-base-fee recurrence. Record Fusaka in provenance; do not discard pre-Fusaka rows merely to hide a visible distribution change.

## Contract tested

The approved/admitted Ethereum inputs are:

- `log_base_fee_per_gas` and `gas_utilization = gas_used / gas_limit`;
- Ethereum-only `log_exact_forming_base_fee_per_gas`, computed only from the closed parent's execution base fee, gas used, and gas limit;
- indivisible candidate `log_gas_limit + log1p_tx_count`; and
- indivisible candidate `hour_sin + hour_cos`.

Priority-fee, blob, cadence, lag, rolling, elapsed-time, and day-of-week inputs are out of the current contract. The target and headline economics use execution `base_fee_per_gas`, not blob base fee.

## Boundary comparison

| Candidate | Local first block/time | Relevant protocol change | Issue 47 consequence |
|---|---|---|---|
| Pectra | 22,431,084; 2025-05-07T10:05:11Z | Pectra activation and start of this corpus | Earliest available clean anchor. Every retained field has the same unit, close-time availability, and formula used later in the corpus. |
| Fusaka/Osaka | 23,935,694; 2025-12-03T21:49:11Z | Transaction gas cap, gas repricing and block-size changes; coordinated higher default block gas limit; blob changes | Material distribution/capacity event, but no retained-feature definition or EIP-1559 recurrence change. A defensible conservative anchor, not the leanest required anchor. |
| BPO2 | 24,179,383; 2026-01-07T01:01:11Z | Blob target/max and blob-base-fee update fraction | No retained input, target, claim, unit, availability rule, or execution-fee formula depends on it. Not a defensible mandatory cut for the approved contract. |

[EIP-7892](https://eips.ethereum.org/EIPS/eip-7892) defines BPO forks as configuration changes to only the blob `target`, `max`, and `baseFeeUpdateFraction`. The official [Fusaka activation record](https://eips.ethereum.org/EIPS/eip-7607) likewise says BPOs raise blob capacity without additional protocol changes. SPICE has excluded every blob-derived feature and claim, so BPO2 cannot earn an execution-fee eligibility boundary.

[EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) defines the child execution base fee from the parent's execution base fee, gas used, and gas target derived from its gas limit. Neither the official [Pectra EIP list](https://eips.ethereum.org/EIPS/eip-7600) nor the [Fusaka EIP list](https://eips.ethereum.org/EIPS/eip-7607) replaces that recurrence. The already-frozen local evidence independently found zero mismatches across all 2,923,987 adjacent Pectra-through-corpus-end transitions; Issue 47 needs no new replay or verifier ([existing evidence](../ethereum-current-row-causality-and-options.md#why-the-ethereum-forming-fee-is-causal)).

Fusaka is still a real execution change. [EIP-7825](https://eips.ethereum.org/EIPS/eip-7825) caps per-transaction gas, while [EIP-7935](https://eips.ethereum.org/EIPS/eip-7935) coordinates a 60M default block gas limit. These can change observed `tx_count`, `gas_used`, `gas_limit`, utilization, and fee distributions. They do not change what those columns mean or when a closed block exposes them. The model directly receives the changed physical `gas_limit` if the capacity/activity candidate survives, and utilization already divides by each row's actual limit. Treating every distribution change as a new semantic regime would be impossible and would silently turn regime selection into outcome-dependent filtering.

Pectra itself is a real fork and therefore supplies a clean left boundary: the official [Pectra activation](https://blog.ethereum.org/2025/04/23/pectra-mainnet) is 2025-05-07T10:05:11Z, and the [Ethereum execution-spec history](https://github.com/ethereum/execution-specs#ethereum-protocol-releases) identifies Prague block 22,431,084. The local manifest requests and covers exactly from that block and timestamp. No earlier row exists in this content-bound corpus.

## Consequence

Using Pectra instead of BPO2 preserves 2,923,988 rather than 1,175,689 physical rows before context/outcome eligibility. At `C=200`, `H=0`, the regime-level maximum is 2,923,784 eligible origins for `K=5`, or 2,923,589 under common `K_max=200` support. Role boundaries will reduce these counts; this report selects none.

The corrected owner choice should ask whether Ethereum's Issue 47 feature-semantic regime starts at Pectra block 22,431,084, while retaining Fusaka/BPO activations as provenance facts rather than mandatory sample cuts. A future blob feature, blob-cost claim, or materially changed execution-base-fee recurrence would require a new explicit regime decision.
