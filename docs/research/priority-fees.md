# EVM priority-fee block feature

Research date: 2026-07-21. This note covers EIP-1559-style execution gas. Blob gas has a separate base-fee market and is outside this feature.

## Why block P50

FABLE owns the canonical Corpus schema and historical feature identity in the [Corpus reference](../../FABLE.md#corpus-object) and [causal-feature contract](../../FABLE.md#causal-features). This note records why the chosen block statistic is P50 and how it may be interpreted.

P50 is the gas-used-weighted median effective priority fee paid by transactions included in a block. Acquire it directly with:

```json
{
  "jsonrpc": "2.0",
  "method": "eth_feeHistory",
  "params": ["0x<count>", "0x<newestBlock>", [50]],
  "id": 1
}
```

For returned block `oldestBlock + i`, decode `reward[i][0]` from a hexadecimal quantity to an integer. The Execution API defines `reward` as effective priority fees per gas, sorted by effective tip and weighted by gas consumed. It can return fewer blocks than requested, so preprocessing must map through `oldestBlock` and reject gaps, missing `reward`, wrong row widths, or incomplete requested coverage rather than silently shortening a Corpus. [Ethereum Execution API: `eth_feeHistory`](https://github.com/ethereum/execution-apis/blob/baa4c9a11736c729ef3f172633df995a84a310b2/src/eth/fee_market.yaml#L57-L133)

The API returns zeroes for an empty block. Zero is also a valid result for a nonempty block whose percentile lands on zero-tip gas. Preserve zero as data; `tx_count` already distinguishes an empty block. Do not use null or imputation. Geth implements the percentile by sorting effective tips, weighting each transaction by its receipt `gasUsed`, and selecting the first tip whose cumulative gas reaches the requested threshold. [Execution API empty-block rule](https://github.com/ethereum/execution-apis/blob/baa4c9a11736c729ef3f172633df995a84a310b2/src/eth/fee_market.yaml#L122-L133), [Geth implementation](https://github.com/ethereum/go-ethereum/blob/6e49f8e6b3404ee33712d147f561fc28c7974a2f/eth/gasprice/feehistory.go#L125-L153)

Because block P50 may be zero, its historical transform uses `log1p`; an ordinary logarithm would be undefined at zero. Ethereum RPC quantities are unsigned, so acquisition must range-check them before integer casting.

## Chain scope

The statistic is available for FABLE's Ethereum, Polygon PoS, and Avalanche C-Chain corpora. Ethereum defines `eth_feeHistory.reward` as effective-tip percentiles weighted by gas consumed; Polygon Bor and Avalanche Coreth implement the same receipt-gas-weighted calculation. [Ethereum Execution API](https://ethereum.github.io/execution-apis/api/methods/eth_feeHistory/) [Polygon Bor implementation](https://github.com/maticnetwork/bor/blob/4154750b45b50f5cd79f71409a9c90b3040a3dbf/eth/gasprice/feehistory.go#L136-L157) [Avalanche Coreth implementation](https://github.com/ava-labs/coreth/blob/64c271b44104f67c6c5ac2dee343f18b0e648f6e/eth/gasprice/feehistory.go#L66-L115)

The statistic is portable; its interpretation remains chain-local. Polygon documents a 25 gwei minimum priority fee, and Bor assigns zero effective tip to state-sync transactions that remain part of the percentile population. Avalanche burns both base and priority fees and uses a chain-specific base-fee mechanism. These differences forbid pooled fee or inclusion claims. [Polygon Gas Station](https://docs.polygon.technology/tools/gas/polygon-gas-station) [Bor state-sync transaction handling](https://github.com/maticnetwork/bor/blob/4154750b45b50f5cd79f71409a9c90b3040a3dbf/core/types/transaction.go#L373-L418) [Avalanche dynamic-fee transactions](https://build.avax.network/docs/rpcs/other/guides/txn-fees#dynamic-fee-transactions)

Consume only the requested `reward` rows and align them through `oldestBlock`; keep canonical base fees sourced from block headers. Current Coreth does not return Ethereum's extra next-block `baseFeePerGas` entry, so acquisition must not infer reward alignment from that array's length. [Coreth fee-history response construction](https://github.com/ava-labs/coreth/blob/64c271b44104f67c6c5ac2dee343f18b0e648f6e/eth/gasprice/feehistory.go#L203-L248)

## Exact fee semantics

`maxPriorityFeePerGas` is a sender-authored cap, not necessarily the tip paid. For an EIP-1559 transaction included in block `b`:

```text
effective_priority_fee_per_gas
    = min(maxPriorityFeePerGas, maxFeePerGas - baseFeePerGas_b)

effectiveGasPrice
    = baseFeePerGas_b + effective_priority_fee_per_gas
```

The base fee is paid first; a tight `maxFeePerGas` reduces the effective priority fee. EIP-1559 also normalizes legacy and access-list transactions so their `gasPrice` supplies both caps. [EIP-1559 specification](https://github.com/ethereum/EIPs/blob/6ebf991c17db76e6969cc36c3ae69ef8f459141d/EIPS/eip-1559.md#L211-L267)

For any included post-London transaction, the clean reconstruction is therefore:

```text
effective_priority_fee_per_gas_i
    = receipt.effectiveGasPrice_i - block.baseFeePerGas
```

`effectiveGasPrice` is the actual amount deducted per execution gas, and `gasUsed` is the transaction's actual execution gas consumption. [Ethereum receipt schema](https://github.com/ethereum/execution-apis/blob/baa4c9a11736c729ef3f172633df995a84a310b2/src/schemas/receipt.yaml#L82-L120)

Do not use `eth_maxPriorityFeePerGas` for the column. It is a current client recommendation, not a historical observation or protocol inclusion threshold. Its estimation policy is client-configurable. [Execution API method](https://github.com/ethereum/execution-apis/blob/baa4c9a11736c729ef3f172633df995a84a310b2/src/eth/fee_market.yaml#L43-L56), [Geth estimator](https://github.com/ethereum/go-ethereum/blob/6e49f8e6b3404ee33712d147f561fc28c7974a2f/eth/gasprice/gasprice.go#L155-L227)

## What P50 means

P50 is the median of the included-gas distribution. It is not a mean or an upper-quartile statistic. Calling the statistic P50 avoids conflating those definitions.

A mined block's P50 says roughly that half of its included execution gas paid an effective tip at or below that value. It does not establish a 50% probability that a new transaction would have been included. The sample contains only included transactions and omits losing transactions, arrival time, nonce readiness, transaction size, private order flow, bundle constraints, and builder payments. EIP-1559 does not require pure priority-fee transaction ordering; ordering can depend on implementation details. [EIP-1559 transaction-ordering discussion](https://github.com/ethereum/EIPs/blob/6ebf991c17db76e6969cc36c3ae69ef8f459141d/EIPS/eip-1559.md#L310-L318)

Use explicit mined block numbers for historical preprocessing. The `pending` block tag is only a local client's sample next block assembled from its view of the mempool, not the eventual canonical next block. [Execution API block-tag definition](https://github.com/ethereum/execution-apis/blob/baa4c9a11736c729ef3f172633df995a84a310b2/src/schemas/block.yaml#L116-L125)

The primary statistic must include zero and near-zero tips. No protocol threshold makes such transactions MEV. Flashbots bundles may pay through a direct `block.coinbase` transfer, allowing individual bundle transactions to carry zero priority fee, while other MEV transactions can carry positive tips. Filtering near-zero tips would therefore neither identify nor remove MEV reliably. [Flashbots bundle payment documentation](https://github.com/flashbots/ethers-provider-flashbots-bundle/blob/master/README.md#paying-for-your-bundle)

## Percentile choice and quantified inclusion

P25 is the lower-quartile boundary, P50 is the median, and P75 is the boundary into Q4. P50 was chosen as a central retrospective congestion and representative-cost proxy. Choosing a higher percentile would make that proxy more conservative but could not strengthen an inclusion claim. Do not call any percentile an admission threshold or a 25%, 50%, or 75% inclusion probability.

The reason is selection: `eth_feeHistory.reward` contains gas-weighted effective-tip percentiles for transactions that were included in the mined block. It contains no transactions that lost the competition, arrived too late, were nonce-blocked, were too large for the remaining gas, were replaced, or reached a different public or private orderflow path. This conclusion follows directly from the API's returned population. Block construction also need not be a pure tip ranking: EIP-1559 leaves equal-tip ordering to client details, gas capacity constrains the selected set, and private bundles can pay through direct fee-recipient transfers rather than each transaction's priority fee. [Execution API percentile semantics](https://ethereum.github.io/execution-apis/api/methods/eth_feeHistory/) [EIP-1559 ordering and block-gas rules](https://eips.ethereum.org/EIPS/eip-1559#transaction-ordering) [Flashbots bundle payments](https://github.com/flashbots/ethers-provider-flashbots-bundle/blob/master/README.md#paying-for-your-bundle)

`eth_maxPriorityFeePerGas` does not solve this. The RPC returns one current client recommendation and defines no success probability. At the cited Geth revision, the default oracle inspects 20 recent blocks, takes up to three of each block's lowest qualifying non-coinbase effective tips, and returns P60 across those samples. This is neither gas-weighted `eth_feeHistory` P60 nor a protocol rule. Geth describes the result only as giving a "very high chance" over following blocks but assigns no probability. It is a useful live-node baseline, not a historical column or calibrated next-block guarantee. [Execution API method](https://ethereum.github.io/execution-apis/api/methods/eth_maxPriorityFeePerGas/) [Geth defaults](https://github.com/ethereum/go-ethereum/blob/6e49f8e6b3404ee33712d147f561fc28c7974a2f/eth/ethconfig/config.go#L42-L50) [Geth oracle and sampling](https://github.com/ethereum/go-ethereum/blob/6e49f8e6b3404ee33712d147f561fc28c7974a2f/eth/gasprice/gasprice.go#L155-L286)

### Published-evidence boundary

No primary or peer-reviewed result found in this review supports a portable claim such as "bidding the previous block's P50 priority fee raises next-block inclusion from `x%` to `y%`." The closest peer-reviewed Ethereum study used four distributed mempool probes around the 2021 London fork and found shorter waiting times after EIP-1559: the median of block-level median waiting times fell from 16.9 to 10.4 seconds. Its treatment was the fork and EIP-1559 adoption, however, not a P50 bid; it defined no next-block binary outcome and measured waiting time only for transactions eventually mined; and its main post-fork sample was August 16-31, 2021, during proof of work. It therefore supports only the qualitative proposition that fee-mechanism changes affected latency, not a fee-specific next-block probability for current Ethereum or either FABLE sidechain. [Liu et al., CCS 2022](https://doi.org/10.1145/3548606.3559341) [Author manuscript and appendix](https://arxiv.org/abs/2201.05574)

Public-chain observations also miss part of the competing order flow. A peer-reviewed Ethereum measurement covering September 2021 through June 2022 found Flashbots transactions in 52.11% of studied blocks and notes that discarded private bundles are not observable. The authors explicitly argue that contention and prioritization remain opaque after EIP-1559 and the Merge. This prevents a mined-block percentile from serving as a complete admission threshold. [Messias et al., FC 2023: population and private-flow visibility](https://link.springer.com/chapter/10.1007/978-3-031-47751-5_13#Sec6) [Messias et al.: post-EIP-1559 and post-Merge boundary](https://link.springer.com/chapter/10.1007/978-3-031-47751-5_13#Sec12)

There is no transferable official probability for Polygon PoS or Avalanche C-Chain either. Polygon's Gas Station maps the last 15 blocks' P10, P25, and P50 priority fees to `safeLow`, `standard`, and `fast`, but publishes no observed success rates or confidence calibration. Avalanche recommends `eth_maxPriorityFeePerGas` from recent blocks and documents priority-fee ordering, but likewise states no inclusion probability. These are chain-local operational heuristics, not evidence that P50 means 50% inclusion. [Polygon Gas Station methodology](https://docs.polygon.technology/tools/gas/polygon-gas-station) [Avalanche C-Chain fee guidance](https://build.avax.network/docs/rpcs/other/guides/txn-fees#dynamic-fee-transactions)

The thesis may cite these sources to explain why a higher competitive tip can reduce delay, but should not attach an `x% -> y%` inclusion claim to P50. Commercial gas-oracle confidence labels without a disclosed transaction population, cutoff, failure handling, and held-out calibration are not suitable evidence. A cheap mined-block analysis can report how often a fixed training-derived fee met or exceeded the realized P50 of held-out blocks; label that **P50 competitiveness coverage**, not inclusion rate. A genuine inclusion curve still requires timestamped pending transactions, including failures and replacements, observed before a fixed cutoff on each chain.

The minimum defensible quantified fee is empirical, not a fixed block percentile. Choose the probability before analysis, for example `alpha = 0.90`, and collect submission-time observations containing both successes and failures. For each eligible public transaction first seen before a fixed next-block cutoff, record its offered effective tip, lead time, gas limit, nonce readiness, route, and chain-local congestion; label whether it entered the next canonical block. The offered tip for realized next-block base fee `B` is:

```text
tip_offered = min(maxPriorityFeePerGas, maxFeePerGas - B)
```

Transactions with `maxFeePerGas < B` are ineligible rather than low-tip failures. The fee cap matters because EIP-1559 fills the base fee first and clips the effective priority fee. [EIP-1559 fee-cap rule](https://eips.ethereum.org/EIPS/eip-1559#specification)

Estimate a monotone held-out inclusion curve `p(t | context)` using fee bins or isotonic calibration, then define:

```text
t_90(context) = smallest tested tip t
                whose one-sided 95% Wilson lower bound for
                P(next-block inclusion | tip t, context) is at least 0.90
```

If no tested tip satisfies the bound, report no supported threshold. This yields the lowest fee with a stated empirical 90% next-block inclusion rate for the declared transaction population and context. It is an observational conditional probability, not a protocol guarantee or causal effect of raising the tip; randomized controlled fee tiers would be needed for that stronger claim. Calibrate Ethereum, Polygon PoS, and Avalanche C-Chain separately. If the Corpus contains mined blocks only, this calibration is impossible: report P50 as retrospective representative-cost accounting and make no probability claim.

## When receipts are needed

`eth_feeHistory` is the direct path for block P50. It avoids downloading every transaction and receipt and already applies gas weighting.

Use block and receipt acquisition only when the study intentionally requires a statistic the API cannot return, such as an exact upper-tail mean, a custom eligibility rule, or total proposer tip revenue:

1. Fetch `eth_getBlockByNumber(block, false)` for the block header, base fee, and transaction hashes.
2. Fetch `eth_getBlockReceipts(block)` for every transaction's `effectiveGasPrice` and `gasUsed`.
3. Use `eth_getBlockByNumber(block, true)` only if the custom rule genuinely needs hydrated transaction fields. Full transactions are not needed to reconstruct paid tips from receipts.
4. If a provider lacks `eth_getBlockReceipts`, fall back to one `eth_getTransactionReceipt` call per transaction. This is operationally expensive and is not the first-choice contract.

The canonical API defines hydrated block retrieval and whole-block receipts. Historical receipts can be unavailable when a node has pruned them, so the acquisition layer must fail the exact range rather than substitute caps or current estimates. [Ethereum Execution API: block retrieval](https://github.com/ethereum/execution-apis/blob/baa4c9a11736c729ef3f172633df995a84a310b2/src/eth/block.yaml#L63-L99), [Ethereum Execution API: block receipts](https://github.com/ethereum/execution-apis/blob/baa4c9a11736c729ef3f172633df995a84a310b2/src/eth/block.yaml#L173-L191)

If a custom implementation reconstructs P50, freeze one integer order-statistic rule and test it against `eth_feeHistory`. Geth's rule sorts ascending by effective tip and takes the first tip whose cumulative receipt gas reaches `floor(blockGasUsed * 50 / 100)`. Do not compute an unweighted transaction-count percentile under the same column name.

## Cost accounting

For a fixed hypothetical transaction using `g` execution gas in block `b`, let `P50_b` be that block's realized included-gas median. The retrospective representative-cost proxy is:

```text
g * (base_fee_per_gas_b + P50_b)
```

When `g` is unchanged between candidate blocks, it cancels from per-origin savings fractions. Comparing `base fee + P50` is therefore dimensionally correct.

Do not sum per-gas tips across a block. Actual block priority-fee revenue is:

```text
sum_i gasUsed_i * effective_priority_fee_per_gas_i
```

That result is wei per block and measures proposer-side tip revenue, not the fee of the thesis transaction. It cannot be added to a base fee measured in wei per gas.

Realized P50 from the immediate and selected future blocks is valid for retrospective outcome accounting. It is future information at the decision origin, so it cannot be supplied directly to a deployable model. Historical training may use lagged P50 values available at the origin. A high-likelihood inclusion claim still requires the separate success-and-failure calibration study above.
