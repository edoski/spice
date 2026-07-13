# Issue 47 regime-anchor and suffix-routing red team

Status: bounded read-only evidence. This note makes no owner decision, changes no
corpus, and authorizes no acquisition.

## Anchor verdict

The original BPO2/Giugliano/Granite package is over-conservative in two places.
Decisions 9–23 retain closed-row execution-fee, utilization, optional
capacity/activity and UTC-hour facts; they omit blob and priority-fee inputs,
cadence, elapsed time, lags, and rolling summaries.

| Chain | Corrected lean anchor | Why |
|---|---|---|
| Ethereum | **Fusaka/Osaka activation**, local block `23,935,694`, `2025-12-03T21:49:11Z` | Reject BPO2 as the anchor. The official [Fusaka schedule](https://blog.ethereum.org/2025/11/06/fusaka-mainnet-announcement) says BPO1/BPO2 change only blob target/max and blob-fee parameters. Issue 47 retains no blob input or claim. Fusaka itself is the earlier material retained-feature boundary: it raises the default execution gas limit to 60M and adds execution constraints, while the EIP-1559 execution-base-fee recurrence remains unchanged. That can change `gas_limit`, `gas_utilization`, transaction activity, and their target distribution. Starting at the corpus's Pectra row would cross this retained-feature capacity boundary. |
| Polygon | **Lisovo**, block `83,756,500`, `2026-03-04T14:03:51Z` | Reject Giugliano as the anchor. [PIP-79](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/c65ce300229593bea17ff21f569c259121b4dd11/PIPs/PIP-79.md) changes child-base-fee validity from one fixed recurrence to a bounded producer choice, directly changing the process that generates the mandatory base-fee sequence and targets. [PIP-83](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/9a7feed01afdf6923bfac3dd10bbb4631ed50099/PIPs/PIP-83.md) later adds child-header gas-parameter metadata; Issue 47 neither reads those fields nor makes an early-header/prefetch claim. Giugliano therefore adds no retained-feature semantic boundary. |
| Avalanche | **Keep Granite**, block `72,240,649`, `2025-11-19T16:00:00Z` | [ACP-226](https://build.avax.network/docs/acps/226-dynamic-minimum-block-times) changes more than an omitted cadence input: it adds millisecond protocol time, replaces block-rate control, and changes ACP-176 gas-capacity accumulation from seconds to milliseconds. [ACP-176](https://build.avax.network/docs/acps/176-dynamic-evm-gas-limit-and-price-discovery-updates) makes elapsed-time gas capacity part of the fee process. The change therefore affects the process behind mandatory base fee/utilization and future fee outcomes, plus the optional gas-limit feature. Crossing Granite would violate Decision 3 even with block-count `C` and no cadence column. |

Distribution drift alone does not create endless regimes. These three anchors are
the latest material protocol boundaries inside the current corpora that change the
approved/admitted execution-fee or retained-feature process. Later boundaries must
be checked when a suffix is sealed.

## Suffix routing

Read-only `dataset_manifest` JSON confirms the current sealed endpoints:

- Ethereum `cor_7bea5a071afaf090c05a`: block `25,355,071`,
  `2026-06-19T23:59:59Z`.
- Polygon `cor_61fb33e47c948a9cebd0`: block `87,024,566`,
  `2026-05-17T15:44:59Z`.
- Avalanche `cor_3ef359c91addcab77e9f`: block `85,676,147`,
  `2026-05-17T15:44:59Z`.

A later Ethereum/Polygon suffix is reasonable, but acquisition now would be
premature. Freeze these inputs first:

1. the selected anchors and chronological training/validation boundaries;
2. Issue 48's pending bounded-testing-range amendment and exact range need;
3. Issue 60's decision on whether any priority-fee fields are required; and
4. final schema, units, continuity/finality evidence, and provider requirements.

Then acquire once under a new content-bound identity, preserving the existing
corpora. Do not extend or republish old content under the same ID. Issue 48 should
own the temporal range requirement, Issue 60 any enrichment requirement, and
Issue 27 the acquisition/sealing mechanics. The orchestrator can create or route
one execution ticket only after those inputs freeze.

Avalanche needs no suffix by symmetry: its approved post-Granite corpus is already
large and Decision 21 caps primary training at two million origins. Revisit only
if the eventual testing range or a new field requirement supplies concrete need.
No acquisition size or endpoint is chosen here.

Local cross-checks: [protocol audit](../issue-1/temporal-chain-fee-protocol-audit.md),
[Issue 54 coverage](../modern-regime-coverage-and-evidence-periods.md), and
[Decision ledger](issue-47-owner-decisions.md).
