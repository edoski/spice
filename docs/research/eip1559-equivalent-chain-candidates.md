# EIP-1559-equivalent chain candidates

## Decision

The evidence supports **Ethereum mainnet** as the only immediately qualifying exact-current-execution-base-fee chain.  **OP Mainnet and Base** are the smallest conditional shortlist for a second chain family: their deployed OP Stack execution client validates an exact child fee from closed parent-header fields, including the current fork-specific integer rules.  Admit either only after the acquisition prototype proves contiguous historic headers and a live transaction path with the same rule/version.  This report does not add a chain or make an owner decision.

Do not treat a chain as equivalent merely because it accepts EIP-1559 transactions.  The gate used here is:

> At the instant before the forming block's transaction selection, the execution base fee must be a unique, exact integer function of public closed-parent state and declared active protocol configuration.  The rule must be reproducible at fork boundaries.  L1 data fees, blob fees, tips, sequencer policy, and inclusion probability are separate quantities.

This is a fee-feature result, not a same-block inclusion guarantee.  A valid transaction can still miss a block through propagation, fee cap/tip, nonce/balance, capacity, builder/proposer, or sequencer policy.

## Accepted and conditional candidates

| Chain / deployed regime | Strict result | Exact state and integer behaviour | Scope |
|---|---|---|---|
| Ethereum mainnet, London onward | **Pass** | EIP-1559 derives child `baseFeePerGas` from parent base fee, gas used, gas limit/elasticity, and active parameters.  It specifies ordered integer division, a minimum one-wei upward increase, and non-negative downward result.  The fork's first block uses `INITIAL_BASE_FEE`. | Model the execution base-fee component only.  EIP-4844 blob base fee and priority fee are not this value. |
| OP Mainnet, Bedrock onward | **Conditional pass** | `op-geth` rejects a header unless `header.BaseFee == CalcBaseFee(config,parent,header.Time)`.  The calculation uses the EIP-1559 integer recurrence.  Holocene reads denominator, elasticity, and minimum base fee from the *closed parent* `extraData`; Jovian meters `max(parent.GasUsed,parent.BlobGasUsed)`.  Active forks are timestamp-configured. | Exact for a virtual execution-fee row when the active chain config and raw parent header are retained.  L1 data fee/operator fee and sequencer charges remain separate. |
| Base, Bedrock onward | **Conditional pass** | Base uses the OP Stack execution client and protocol releases.  Therefore it has the same recurrence contract as OP Mainnet, subject to validating Base's deployed fork schedule and source revision at acquisition time. | Same exclusions.  It is a separate network/data experiment, not independent protocol evidence. |

The relevant OP Stack source is deliberately stronger than a compatibility label: [`VerifyEIP1559Header`](https://github.com/ethereum-optimism/op-geth/blob/optimism/consensus/misc/eip1559/eip1559.go) checks equality against [`CalcBaseFee`](https://github.com/ethereum-optimism/op-geth/blob/optimism/consensus/misc/eip1559/eip1559.go).  That implementation exposes every fork input and its integer order.  Its [`ChainConfig`](https://github.com/ethereum-optimism/op-geth/blob/optimism/params/config.go) makes Holocene and Jovian timestamp forks explicit.  The OP Stack protocol specification documents [EIP-1559 parameter updates](https://specs.optimism.io/protocol/holocene/exec-engine.html) and its [L1 fee](https://docs.optimism.io/stack/transactions/fees) as a distinct charge; Base documents the same separation in its [fee model](https://docs.base.org/chain/network-fees).

For Ethereum, the normative source is [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559), particularly `expected_base_fee_per_gas`: it defines the initialization boundary, parent target, ordering of integer arithmetic, one-wei upward floor, and downward floor.  These inputs are standard block-header fields exposed by [`eth_getBlockByNumber`](https://ethereum.org/developers/docs/apis/json-rpc/#eth_getblockbynumber).

## Rejected as strict equivalents

| Chain | Why it fails this gate |
|---|---|
| Polygon PoS, Lisovo onward | Bor v2.6 validates a producer-selected fee within a bounded parent-relative range rather than one computed child value.  Parent fields plus one fixed recurrence cannot determine the child fee.  Giugliano's header fields improve retrospective reconstruction, not proof that a submitter sees them before selection.  Sources: [PIP-79](https://forum.polygon.technology/t/pip-79-bounded-range-validation-for-configurable-eip-1559-parameters/21711), [Bor verifier](https://github.com/0xPolygon/bor/blob/v2.6.0/consensus/misc/eip1559/eip1559.go). |
| Avalanche C-Chain, ACP-176 / Granite | Coreth advances dynamic fee state from parent `extra` state and elapsed child time; Granite uses millisecond time.  The forming timestamp is not a closed-parent public fact before the producer chooses it, and ordinary headers/corpus fields omit required state.  Sources: [ACP-176](https://build.avax.network/docs/acps/176-dynamic-evm-gas-limit-and-price-discovery-updates), [ACP-226](https://build.avax.network/docs/acps/226-dynamic-minimum-block-times), [Coreth state code](https://github.com/ava-labs/coreth/blob/v0.16.0/plugin/evm/customheader/dynamic_fee_state.go). |
| Arbitrum One | Nitro's L2 price is stateful: it stores base fee, gas backlog, inertia, tolerance, and a per-second speed limit in ArbOS state.  The resulting price evolution depends on time and system state rather than a standard closed parent-header recurrence; the sequencer controls forming-block time/order.  It may support a separate stateful estimator study, but fails this exact pre-selection parent-header-equivalence shortlist.  Source: [Nitro `l2pricing`](https://github.com/OffchainLabs/nitro/blob/master/arbos/l2pricing/l2pricing.go). |

Earlier Polygon fixed-parameter eras can pass a *fork-scoped* recurrence replay when the correct target and denominator are supplied, but are not an eligible current production candidate because the deployed Lisovo regime changed the premise.  See the detailed local [protocol audit](issue-1/temporal-chain-fee-protocol-audit.md).

## Broad funnel: not advanced

| Chain | Disposition before shortlist | Reason |
|---|---|---|
| zkSync Era | Reject | Its L1 gas price and fair gas price are operator/batch parameters, not a parent-header consensus recurrence ([fee structure](https://docs.zksync.io/zksync-protocol/era-vm/transactions/fee-model/fee-structure)). |
| BNB Smart Chain | Hold out | A bounded official-RPC check returned a zero execution base fee at the sampled height.  It needs the pre-registered variation/activity gate before it can be called a meaningful fee-timing signal; no claim follows from EVM transaction compatibility ([official RPC guide](https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoints/)). |
| Gnosis Chain | Hold out | Its official history records EIP-1559 adoption, but that is insufficient evidence of sustained base-fee variation and two-provider archive quality ([hard-fork history](https://docs.gnosischain.com/about/specs/hard-forks/eip-1559)). |

This funnel deliberately does not rank chains after inspecting model outcomes.  It removes a candidate only for an ex-ante protocol or data gate.

## Thesis-grade admission checks

Apply these pre-registered thresholds to every shortlisted network; failure rejects it rather than selecting a favorable window:

1. At least 180 contiguous days and 1,000,000 consecutive canonical blocks after the last fee-rule boundary, with raw parent headers sufficient to replay every sampled child fee exactly.  This supplies multiple demand regimes and enough block-level observations without claiming cross-regime stationarity.
2. At least 99.99% retrievable contiguous headers over that fixed range from two independent archive-capable RPC providers; reconcile hash/fee/gas fields and document gaps.  A provider that cannot reproduce the fields is not thesis-grade evidence.
3. Non-sparse activity and signal: pre-register exclusion if more than 25% of blocks are empty, if fewer than 100,000 blocks contain transactions, or if fewer than 1% of child fees differ from their parent fee.  These are conservative practical minima: enough effective fee transitions for temporal experiments, while avoiding a chain chosen for random/sparse noise.
4. Separate columns and claims for execution base fee, blob base fee, L1 data fee, operator fee, and priority fee.  The model's target is only the first unless the experiment explicitly expands it.

Ethereum clearly has the protocol support.  OP Mainnet and Base are candidates, not automatic additions: run the above fixed-window RPC/header and activity checks first.  L2 exactness also does not establish public same-block actionability; record sequencer submission endpoint, decision time, and first eligible block separately.

## Bounded data-access check

On 2026-07-11, read-only calls to the official public [OP Mainnet endpoint](https://docs.optimism.io/chain/networks), [Base endpoint](https://docs.base.org/base-chain/network-information), and [Avalanche C-Chain endpoint](https://build.avax.network/docs/api-reference/c-chain/api) returned a current block, a block 100,000 heights earlier, and `eth_feeHistory`.  OP's sampled blocks had 26 and 27 transactions with base fees 342 and 304 wei; Base's had 153 and 119 transactions with base fee 5,000,000 wei; Avalanche's had 39 and 62 transactions.  This establishes only that ordinary public RPC can serve a small recent and historic sample.  It does **not** establish the two-provider, million-block, 180-day, activity, variation, or actionability gates above.

Base launched with EIP-1559 base fee at its 2023-06-14 genesis in the same probe.  Its and OP Mainnet's multi-year production history make the proposed 180-day/one-million-block check plausible, but plausibility is not qualification.  The fixed acceptance window must be selected by protocol boundary and acquisition date before inspecting any model result.

## Minimal acquisition contract

For Ethereum retain parent `baseFeePerGas`, `gasUsed`, `gasLimit`, block number, and fork metadata.  For OP Stack additionally retain raw parent `extraData`, `blobGasUsed` when present, parent timestamp, and the resolved chain/fork configuration.  Replay with the client code's exact integer ordering; test boundary blocks on both sides of every activation.  Do not infer an OP Stack fee from `eth_feeHistory` alone, and do not use an L1-data-fee oracle as the execution base fee.
