# Issue 47 Polygon regime-anchor red team

**Verdict:** withdraw Giugliano as the Polygon anchor. Use **Lisovo block
`83,756,500`** (local timestamp `2026-03-04T14:03:51Z`) as the earliest
defensible modern fee/retained-feature regime in the current corpus. Giugliano
does not change the base-fee validity rule or any selected Issue 47 input. It
adds operational block-announcement behavior and completed-child metadata that
SPICE neither consumes nor needs for its closed-parent claim.

## Contract check

Issue 47 now uses closed rows only: common `log_base_fee_per_gas` and
`gas_utilization`; admitted pairs `log_gas_limit + log1p_tx_count` and UTC-hour
encoding; no Polygon forming-fee column, cadence input, priority-fee input, or
child-header parameter. Every value is available at `close(j)`, with `H=0`.

Lisovo is material to that contract because it changes the **outcome-generating
fee rule**. [PIP-79](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/c65ce300229593bea17ff21f569c259121b4dd11/PIPs/PIP-79.md#L50-L58)
replaces one required parent-derived fee with a producer-selected child fee
inside a bounded range. The pinned [Bor v2.6 verifier](https://github.com/0xPolygon/bor/blob/v2.6.0/consensus/misc/eip1559/eip1559.go#L38-L108)
branches exactly there: pre-Lisovo requires equality with `CalcBaseFee`, while
post-Lisovo checks only the parent-relative bound. This is a real semantic
boundary even though Polygon has no exact forming-fee model input.

Giugliano is not material to the retained contract:

- [PIP-83](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/9a7feed01afdf6923bfac3dd10bbb4631ed50099/PIPs/PIP-83.md#L28-L44)
  writes producer-reported gas target and denominator into the completed
  child's extra data. Verification requires presence, not correctness; the PIP
  calls the values informational rather than consensus constraints. Issue 47
  neither acquires nor models them, and reading them before child close would be
  forward leakage.
- [PIP-84](https://forum.polygon.technology/t/pip-84-giugliano-hardfork/21808)
  reintroduces [PIP-66 early block announcements](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/main/PIPs/PIP-66.md).
  This changes when an already-built block propagates, not the finalized
  `baseFee`, `gasUsed`, `gasLimit`, `tx_count`, or timestamp units. SPICE makes
  no transaction-inclusion guarantee, and approved block-count context excludes
  cadence as an input. Actual receipt-backed inclusion would be a different
  claim and should re-evaluate this boundary then.

Thus Giugliano may change distributions and realized wall-clock spans, but not
the current feature formulas, availability, units, base-fee consensus regime,
or offline/live parity statement.

## Earlier-fork challenge

| Fork | Mainnet block | Relevance to the approved/admitted contract | Why it is not the selected start |
|---|---:|---|---|
| [Bhilai](https://forum.polygon.technology/t/pip-63-bhilai-hardfork/20872) | 73,440,256 | Changes gas limit to 45M and fee-change denominator to 64. | It is the corpus start, but later Dandeli and Lisovo change fee semantics. |
| [Rio](https://forum.polygon.technology/t/pip-73-rio-hardfork/21268) | 77,414,656 | Changes block-production/validation architecture; no retained formula or unit changes. Priority fees are omitted. | Later material changes remain. |
| [Madhugiri](https://forum.polygon.technology/t/pip-76-madhugiri-hardfork/21377) | 80,084,800 | [PIP-74](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/main/PIPs/PIP-74.md) canonically adds a zero-gas StateSync transaction to affected block bodies, so raw `tx_count` representation can change; base fee and gas used remain unaffected. | Later Dandeli and Lisovo remain; Lisovo safely follows this representation change. |
| [Dandeli](https://forum.polygon.technology/t/bor-v2-5-6-and-erigon-v3-3-6/21547) | 81,424,000 | Changes the gas-target calculation used by the deterministic fee recurrence; Bor documents the post-Dandeli percentage target in [`CalcBaseFee`](https://github.com/0xPolygon/bor/blob/v2.6.0/consensus/misc/eip1559/eip1559.go#L110-L199). | It is a fee boundary, but its exact recurrence is superseded by Lisovo's bounded producer choice. |
| [Lisovo](https://forum.polygon.technology/t/pip-81-lisovo-hardfork/21713) | 83,756,500 | Changes consensus from one exact child fee to bounded producer choice. | **Earliest start whose fee-rule semantics continue through the local suffix.** |
| [Giugliano](https://forum.polygon.technology/t/bor-v2-7-0-and-erigon-v3-5-0-for-mainnet/21830) | 85,268,500 | Adds early announcement and completed-child parameter observability. | No selected feature, fee-validity rule, or current offline/live claim needs it. |

Post-Lisovo producer parameters may vary without creating a new protocol regime:
that variation is the approved rule itself. Gas-limit changes also remain an
observed closed-row fact; `gas_utilization` preserves its ratio semantics and
the optional `log_gas_limit` exposes capacity directly. A later fork that
changes a retained field's meaning, availability, or fee-validity rule would
create a new boundary.

## Bounded count consequence

Using the already-sealed contiguous end block `87,024,566`, arithmetic alone is
sufficient; no corpus rescan is needed. With approved `H=0`, primary `C=200`,
and a contiguous `N`-row regime, eligible origins are `N-C-K+1`.

| Candidate start | Rows through local end | Maximum `K=5` origins | Maximum origins with common `K_max=200` support |
|---|---:|---:|---:|
| Lisovo 83,756,500 | 3,268,067 | 3,267,863 | 3,267,668 |
| Giugliano 85,268,500 | 1,756,067 | 1,755,863 | 1,755,668 |

Lisovo recovers exactly **1,512,000** rows and eligible origins—about 35 days
of already-sealed history—without mixing fee-validity regimes. These are
regime-level maxima, not training, validation, or testing allocations.

## Owner recommendation

Ask the owner to approve Polygon Lisovo block `83,756,500` as the selected
modern regime start and reject Giugliano as an unnecessary anchor for the
current Issue 47 contract. Keep Giugliano recorded as operational metadata, not
a sample-containment boundary. This choice does not select role ranges, testing
size, acquisition range, or any Issue 60 priority-fee semantics.

Local facts and the already-frozen empirical recurrence evidence come from
[the protocol audit](../issue-1/temporal-chain-fee-protocol-audit.md),
[the modern coverage report](../modern-regime-coverage-and-evidence-periods.md),
and [the focused Polygon forming-fee audit](../issue-45/polygon-modern-forming-block-fee.md).
