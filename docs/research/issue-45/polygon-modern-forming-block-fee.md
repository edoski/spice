# Modern Polygon forming-block base fee

Status: focused evidence for [Prototype the current-block action and cross-layer parity](https://github.com/edoski/spice/issues/45). Audited against Polygon PoS mainnet and Bor `v2.9.0` on 2026-07-11. This report does not change production code or the ticket.

## Bottom line

Preserving `k=0 = the forming block` is sound. What modern Polygon removes is not that action; it removes the claim that a public observer can always know the forming block's exact base fee from the closed parent alone.

The lean causal contract is therefore:

- context ends at the last closed parent;
- `k=0` labels the block currently about to be formed;
- its base fee is an outcome to forecast, not an input already known;
- no row is discarded because its eventual fee disagrees with an assumed producer formula.

This preserves the intentional `k=0` extension without a chain-specific virtual-fee oracle or target leakage.

## Why Polygon changed, in plain language

Before Lisovo, Polygon's rule was like a calculator bolted to the wall. Given the parent block's fee, gas used, and gas limit, everyone had to obtain the same child fee. A block with any other answer was invalid.

Since Lisovo, the parent supplies a **lane**, not one answer. The next producer may place the child fee anywhere sufficiently close to the parent fee. Other validators ask only, “is it still inside the lane?” They no longer ask, “did the producer use my exact formula?” [PIP-79 explicitly replaces exact-match validation with bounded validation and permits any in-range producer choice](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/c65ce300229593bea17ff21f569c259121b4dd11/PIPs/PIP-79.md#L50-L58). Mainnet activated Lisovo at block `83,756,500` on 2026-03-04 ([Bor v2.6.0 release](https://github.com/0xPolygon/bor/releases/tag/v2.6.0)).

The deployed Bor `v2.9.0` check is:

```text
allowed_change = max(floor(parent_base_fee * 5 / 100), 1 wei)
abs(child_base_fee - parent_base_fee) <= allowed_change
```

That is the exact implementation rule; see [post-Lisovo header verification](https://github.com/0xPolygon/bor/blob/920556e8f7859526ad33fca57ef3f2f42ee91fff/consensus/misc/eip1559/eip1559.go#L38-L108). At ordinary multi-gwei fees it means “within roughly ±5%.”

Stock Bor still offers producers a calculator. It uses these inputs:

| Input | Publicly known from the closed parent? |
| --- | --- |
| Parent base fee | Yes |
| Parent gas used | Yes |
| Parent gas limit | Yes |
| Fork/block number | Yes |
| Producer's gas target or dynamic-target policy | No; runtime node configuration |
| Producer's base-fee change denominator | No; runtime node configuration |
| Child transactions or child execution result | Not used by the stock calculation |

The calculation and integer rounding are in [Bor's `CalcBaseFee`](https://github.com/0xPolygon/bor/blob/920556e8f7859526ad33fca57ef3f2f42ee91fff/consensus/misc/eip1559/eip1559.go#L110-L199). The variable parameters are explicitly [per-node runtime miner configuration, not genesis/header facts](https://github.com/0xPolygon/bor/blob/920556e8f7859526ad33fca57ef3f2f42ee91fff/params/config.go#L936-L948), and the miner writes the result into the child header before executing its transactions ([worker construction](https://github.com/0xPolygon/bor/blob/920556e8f7859526ad33fca57ef3f2f42ee91fff/miner/worker.go#L1842-L1868)). Thus the producer knows its answer before child execution, but an outside SPICE client does not necessarily know the producer's private/runtime knobs.

Giugliano, activated on mainnet at block `85,268,500` on 2026-04-08 ([Bor v2.7.0 release](https://github.com/0xPolygon/bor/releases/tag/v2.7.0)), added `GasTarget` and `BaseFeeChangeDenominator` to the **child's** signed header. This makes past behavior auditable through `bor_getBlockGasParams` or the `borExtra` block-RPC option. It does not make the fields available before that child is published. Moreover, validators check only that the fields exist, not that the producer truthfully used them; [PIP-83 calls them self-reported informational metadata](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/9a7feed01afdf6923bfac3dd10bbb4631ed50099/PIPs/PIP-83.md#L283-L322), matching [Bor's presence-only verification](https://github.com/0xPolygon/bor/blob/920556e8f7859526ad33fca57ef3f2f42ee91fff/consensus/bor/bor.go#L498-L507).

## What recent mainnet blocks actually do

A read-only, contiguous probe used the Polygon-documented mainnet RPC and `eth_getBlockByNumber(..., false, true)` for blocks [`90,028,802`](https://polygonscan.com/block/90028802) through [`90,028,902`](https://polygonscan.com/block/90028902). The endpoint and `borExtra` response are documented by [Polygon's RPC endpoint guide](https://docs.polygon.technology/pos/reference/rpc-endpoints) and [PIP-83](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/9a7feed01afdf6923bfac3dd10bbb4631ed50099/PIPs/PIP-83.md#L294-L320).

For the 100 parent-to-child transitions:

- 69 child headers reported gas target `24,000,000`;
- 31 reported gas target `112,000,000`;
- all 100 reported denominator `64`;
- all 100 child fees exactly reconstructed from the parent plus the child's reported parameters.

The fixed endpoint hashes were `0xacc50193623f3f6f9f2f0630ee567f2054b83782847c60f578fcc1b160f22bea` and `0xd99330208bd8be905219503d4f22da5a8cb15d9d6c9e468449b4553fdeb9016f`.

With a `160,000,000` parent gas limit, those targets are 15% and 70%. In this window they also fit a simple controller: below 250 gwei use 15%, otherwise use 70%, with denominator 64. That is useful evidence that current producers are coordinating on a parent-driven policy. It is **not** a protocol guarantee: the policy was inferred after observing completed children, no authoritative pre-block publication of those exact settings was found, and a valid producer may change them on the next block.

Therefore modern Polygon is not random. It is operationally structured but protocol-permissive. The distinction matters: a historical child can be reconstructed exactly; a forming child is only exactly parent-predictable if its producer policy was known and frozen in advance.

## Can SPICE download a suitable subset?

Yes, with two different claims kept separate.

A contiguous post-Lisovo range is valid for training and evaluating `k=0` as a **forecast target**. Select it by height/date before examining child outcomes, retain every transition, and give the model only parent-known information. This is the recommended lean route.

A narrower “fixed producer policy” case study is also possible, but requires a discovery/validation design:

1. use one earlier range to infer or obtain the policy;
2. freeze its parameters and admissible height/date scope;
3. evaluate on a later untouched contiguous range;
4. retain and report every mismatch as a regime break.

Filtering the corpus afterward to keep only children that match a chosen formula is invalid for causal evaluation. It uses the answer—the completed child fee—to decide whether the example exists. The resulting accuracy would partly measure selection rather than forming-block predictability.

No general post-Lisovo range provides a consensus-guaranteed exact parent-only fee. A declared, stable producer policy can provide conditional operational predictability, but the simplest defensible thesis implementation does not need it: keep `k=0` as the forming block, end features at its parent, and forecast the forming fee.
