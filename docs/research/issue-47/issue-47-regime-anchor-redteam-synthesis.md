# Issue 47 regime-anchor red-team synthesis

Status: bounded planning evidence for
[Choose causal preprocessing, split, feature, and context semantics](https://github.com/edoski/spice/issues/47).
This note records no owner decision and authorizes no acquisition.

## Corrected recommendation

Use **Fusaka/Osaka** for Ethereum, **Lisovo** for Polygon, and preserve the
already-approved **Granite** start for Avalanche.

The governing boundary test is narrow: cut when a protocol change materially changes
the execution-base-fee rule or the protocol process generating an approved/admitted
feature or target. Do not cut only for blob parameters, completed-child metadata,
prefetch behavior, or ordinary distribution drift that leaves this contract unchanged.

## Ethereum: Fusaka, not BPO2 or Pectra

The local Fusaka/Osaka suffix begins at block `23,935,694`,
`2025-12-03T21:49:11Z`. Fusaka does not replace Ethereum's EIP-1559 parent-only
execution-base-fee recurrence, but it does materially change the process behind
retained/admitted fields: transaction gas capping, execution gas repricing, execution
block-size constraints, and the coordinated 60M default gas limit affect `tx_count`,
`gas_used`, `gas_limit`, `gas_utilization`, and future execution-base-fee outcomes.
Starting at the Pectra corpus row would cross that material retained-feature process
boundary.

BPO1/BPO2 are later blob-parameter-only changes. They change blob target/max and the
blob-base-fee update fraction, while Issue 47 retains no blob input, blob target, or
blob-cost claim. BPO2 therefore cannot earn a mandatory execution-feature cut.

Primary evidence:

- [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559)
- [Fusaka meta EIP](https://eips.ethereum.org/EIPS/eip-7607)
- [BPO definition](https://eips.ethereum.org/EIPS/eip-7892)
- [Fusaka activation and BPO schedule](https://blog.ethereum.org/2025/11/06/fusaka-mainnet-announcement)

Through the current block `25,355,071`, the post-Fusaka interval contains
`1,419,378` rows. With `C=200`, `H=0`, it permits at most `1,419,174` origins for
`K=5`, or `1,418,979` origins with common `K_max=200` support, before role boundaries.

One independent pass preferred Pectra because the feature formulas and EIP-1559
recurrence remain stable. That is too narrow a definition of Decision 3's regime:
Fusaka changes consensus constraints and capacity governing several admitted fields and
their targets, not merely an uncontrolled market distribution. Fusaka is the earliest
post-boundary interval that remains materially consistent through the current corpus.

## Polygon: Lisovo, not Giugliano

The local Lisovo suffix begins at block `83,756,500`,
`2026-03-04T14:03:51Z`. PIP-79 changes consensus from one deterministic child base fee
to a producer-selected fee inside a parent-relative bound. That directly changes the
process generating the mandatory base-fee sequence and outcomes.

Giugliano later adds early block propagation and completed-child, producer-reported gas
parameters. Issue 47 does not consume those fields, use cadence, or guarantee inclusion;
reading the child metadata before close would violate the approved information set.
Giugliano is provenance, not a retained-feature boundary.

Primary evidence:

- [PIP-79 bounded fee validation](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/c65ce300229593bea17ff21f569c259121b4dd11/PIPs/PIP-79.md)
- [Bor v2.6 fee verifier](https://github.com/0xPolygon/bor/blob/v2.6.0/consensus/misc/eip1559/eip1559.go)
- [PIP-83 completed-child parameter metadata](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/9a7feed01afdf6923bfac3dd10bbb4631ed50099/PIPs/PIP-83.md)

Through current block `87,024,566`, the post-Lisovo interval contains `3,268,067`
rows. With `C=200`, `H=0`, it permits at most `3,267,863` origins for `K=5`, or
`3,267,668` origins with common `K_max=200` support, before role boundaries. This
preserves exactly `1,512,000` more rows than Giugliano without crossing the fee-rule
boundary.

## Avalanche and acquisition boundary

Keep Granite block `72,240,649`, `2025-11-19T16:00:00Z`. ACP-226 changes protocol
time and the ACP-176 gas-capacity/fee process; Decision 21 already fixes the primary
training support there.

The approved coordination fog is separate from anchor selection. Wait to acquire one
later content-bound Ethereum/Polygon suffix until role/testing ranges, the bounded
testing rule, and Issue 60's final fields freeze. Avalanche needs no suffix absent new
evidence. Existing corpora remain immutable; no acquisition is authorized here.
