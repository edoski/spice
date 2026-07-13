# Current-block action cross-layer parity prototype

Status: owner-approved decision evidence for [Prototype the current-block action and cross-layer parity](https://github.com/edoski/spice/issues/45). On 2026-07-11, Edo selected the closed-parent contract plus one exact Ethereum forming-fee feature. This document does not authorize production implementation.

Run the disposable fixture:

```sh
uv run python docs/research/current_block_action_cross_layer_fixture.py
```

Question: for one decision, do feature availability, label, decoded offset,
replay realization, and serving response refer to the same target block?

The fixture fixes latest closed block `L=100`, confirmation depth `d=2`, stale
confirmed context `c=L-d=98`, decision parent `h=L=100`, and decoded offset
`k=1`. It prints full state for four materially distinct regimes and asserts
the selected `k=0 -> 101`, `k=1 -> 102` mapping. Confirmation/finality policy
must not move the forming-block decision clock backward.

| Route | Decision/context | Target for class `k` | Offline label/replay | Serving target | Result |
| --- | --- | --- | --- | --- | --- |
| Forming block | Before selection for `t`; closed parent `t-1` plus only causal virtual-row facts | `t+k` | `t+k` | `t+k` | Parity only where current fee is available before selection. |
| Forming block, parent-only inputs | Before selection for `t`; inputs end at closed parent `h=t-1`; `base_fee[t]` is an outcome to predict, not an input | `t+k` | `t+k` | `t+k` | Preserves physical `k=0=t` without a virtual current-fee constructor. |
| **Selected: closed parent plus exact Ethereum forming fee** | Before selection for `t`; ordinary context ends at `h=t-1`; Ethereum additionally computes `base_fee[t]` exactly from `h` | `t+k` | `t+k` | `t+k` | One shared decision geometry. Polygon/Avalanche use the parent-only feature set; Ethereum retains one proved protocol fact. |
| Immediate action, closed parent | After closed `h`; submit now / wait `k` openings | `h+1+k` | `h+1+k` | `h+1+k` | Parity for all regimes; it does not claim inclusion. |
| Paper-next-block comparator | After closed `h`; next eligible block semantics | `h+1+k` | `h+1+k` | `h+1+k` | Same block arithmetic as closed-parent. Any remaining difference must be stated as a different estimand, not an offset. |
| Current implementation (failed comparator) | Offline anchor `h`; serving confirmed `h=L-2` | offline `h+k`; serving `h+1+k` | `h+k` | `h+1+k` | Fails parity. For depth two, `k=0 -> L-1`, `k=1 -> L`; neither is a future target. |

## Evidence exercised

Current offline geometry permits `candidate_start_rows >= anchor_rows`, and the
strict policy derives labels, baseline, and realization from the candidate
start row ([problem store](../../src/spice/temporal/problem_store.py),
[execution policy](../../src/spice/temporal/execution_policy/strict_deadline_miss.py)).
Thus the existing current-row construction maps class `k` to row `h+k`.

Current serving fetches stale confirmed context `c=L-d`, then returns
`broadcast_after_block=c+k` and `target_block=c+k+1`
([live window](../../src/spice/serving/live_blocks.py),
[inference](../../src/spice/serving/inference.py)). With `d=2`, its `k=0`
target is `L-1` and its `k=1` target is `L`: both have already closed. The
fixture’s selected mapping uses decision parent `h=L` and repairs the arithmetic
without a magic constant: `target=h+1+k`. It also shifts offline labels and
replay together; changing serving alone would retain a different task.

The fixture also prints the remaining actionability failure: offline actions are
block offsets while serving reports `round(k * slot_spacing_seconds)`. Realized
timestamp-bounded windows, missed blocks, and Avalanche's dynamic delay mean
this is an estimate, not a block-equivalent deadline. The replay maps arrivals
to a prior sample then discards the arrival time; it has no builder cut-off,
propagation, nonce, capacity, or first-eligible-block rule. Every route remains
an eligibility/forecast claim until those facts are named. Ties use current
earliest-`argmin` behavior; this is material on Polygon and needs an explicit
target-policy statement.

The routes define one small pure module interface:
`(decision_clock, context_end, offset) -> target_block`. It has depth because
callers do not separately learn label, replay, and serving offsets. The
selected Ethereum enhancement is a concrete pure parent-to-fee function, not a
generic chain adapter. Polygon and Avalanche retain the same closed-parent
geometry without a dummy or estimated value.

## Selected closed-parent forming-block contract

The selected contract preserves Edo's stated physical meaning exactly: `k=0`
remains an immediate attempt to enter the forming block `t`, where `h=t-1` is
the latest closed parent. Ordinary feature inputs end at `h`, while candidate
row zero begins at `t`. Ethereum adds one exact forming-fee feature computed
from the closed parent's base fee, gas used, gas limit, and active EIP-1559
parameters. It must never read the finalized child row.

This makes the uniform parent-only route the common cross-chain baseline and
adds only a fact Ethereum genuinely exposes. Post-Lisovo Polygon and modern
Avalanche do not receive a placeholder, estimate, availability flag, or virtual
header. The selected route satisfies the input side of the local Phi criterion
once every other retained feature is proved available by decision time `tau`:
target-row timestamp/cadence/calendar values must be removed or reconstructed
from the parent, current slot, or decision clock. It does **not** prove a public
transaction reaches `t`. Its honest serving claim is “attempt immediately;
eligible only if submission precedes the effective cut-off and normal
fee/nonce/balance/propagation/capacity conditions hold.” Same-block inclusion
must remain unclaimed unless a chain-specific cut-off proof is obtained.

| Route | Inputs at decision time | Forming fee role | Decision status | What it can honestly claim |
| --- | --- | --- | --- | --- |
| Uniform parent-only baseline | Closed-parent and decision-time facts | Outcome only | Retained as the primary cross-chain comparator | Immediate same-block attempt / conditional eligibility. |
| **Selected Ethereum enhancement** | Same facts plus exact `base_fee[t]` derived from `h` | One causal input and the realized fee of candidate zero | Selected for Ethereum; absent elsewhere | Same claim; exact base fee does not imply inclusion. |
| Native estimates / enriched headers | Chain-specific RPC estimates or retrospective child state | Exact or estimated depending on regime | Rejected for the selected bounded route | No stronger actionability claim without a cut-off proof. |

Giugliano's child-header parameters and finalized Avalanche raw-header state
improve retrospective reconstruction, but do not by themselves qualify as
inputs to a public same-block action: a child header is already built. They are
therefore not a reason to reject parent-only inputs, nor evidence that a
forming-block fee was observable in time.

### Worked mapping and result status

Let closed parent `h=100`, forming child `t=101`, and decoded `k=0`.

| Layer | Current current-row path | Selected path |
| --- | --- | --- |
| Model inputs | End at row `101`, including finalized current fee and target-row time-derived values | Ordinary context ends at row `100`; Ethereum computes exact forming fee `101` from row `100`; other chains retain only parent/decision-time values |
| Class label | `argmin` can select row `101` for `k=0` | Same physical row `101` for `k=0` |
| Baseline / realized replay row | `101` | `101` |
| Live action | Currently uses a confirmed old row and reports `h+k+1`; not parity-safe | Attempt broadcast immediately for forming `101`; eligibility is conditional, inclusion is not promised |

The action meaning, label outcome rows, tie rule, and economics stay the same
after the one-row input/candidate seam is moved: closed-parent context ends at
`h`, while candidate row zero begins at `h+1=t`. Current code instead makes the
anchor both the context end and `candidate_start_rows`
([compiler](../../src/spice/temporal/compilers/observed_time_window.py)); its
current fee features read `base_fee_per_gas` from that row and its time features
read that row's timestamp. The selected route standardizes the design by
separating **what is known** (through `h`) from **what is acted on** (from `t`),
then names Ethereum's exact fee as a derived exception. It removes, rather than
multiplies, chain-specific virtual-current-row adapters.

One replay semantic cannot stay unchanged: the replay sample timestamp must be
the parent/decision instant, not the forming outcome timestamp. The current
Poisson adapter maps an arrival to the preceding sample and then discards the
arrival time; it therefore cannot prove a cut-off or first-eligible block. A
parent-only replay may retain the same fee outcome rows and accounting formula,
but must carry the request time through an explicit immediate-attempt/eligibility
mapping before it can make an actionability claim.

Existing artifacts and numerical results are not corrupt: their checksums,
offline loss, labels, and replay results remain valid evidence for the exact
historical current-row contract they ran. They are not reusable for the
selected clean contract: its feature matrix, input sequence end,
scaler/artifact compatibility, and physical sample geometry differ even though
the derived Ethereum fee is numerically identical. New training and replay are
required; old and new scores are not directly comparable as one policy. Their
claim validity is narrower than their artifact validity: past results cannot
support a deployable cross-chain forming-block claim because current inputs and
serving do not share one proven decision-time information set.

## Regime matrix

| Regime | Exact forming fee from closed parent | Selected feature contract | Why |
| --- | --- | --- | --- |
| Ethereum EIP-1559 | Yes | Closed-parent features plus exact forming fee | Parent-state recurrence derives child base fee before child execution. |
| Polygon corpus, including fixed and configurable eras | Not retained as one corpus-wide feature | Uniform closed-parent features | A pre-Lisovo fork-specific recurrence exists, but the corpus crosses post-Lisovo producer configurability; the selected bounded route avoids regime-specific feature machinery. |
| Avalanche C-Chain Octane/Granite | No | Uniform closed-parent features | Exact transition needs dynamic header state and child time; Granite adds millisecond time absent from the corpus. |

These are availability claims, not inclusion guarantees. A fee cap, propagation,
nonce, capacity, and builder/proposer policy still determine whether an
otherwise eligible transaction enters its target block.

Primary sources: [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) defines
Ethereum's parent-derived base-fee transition. Polygon Bor
[v2.6.0 validation](https://github.com/0xPolygon/bor/blob/v2.6.0/consensus/misc/eip1559/eip1559.go)
implements the Lisovo bounded configurable rule. Avalanche
[ACP-176](https://build.avax.network/docs/acps/176-dynamic-evm-gas-limit-and-price-discovery-updates)
defines the dynamic-fee state transition; [ACP-226](https://build.avax.network/docs/acps/226-dynamic-minimum-block-times)
adds the relevant dynamic timing regime. The read-only corpus reproduction and
full source-to-claim reasoning remain in [the chain protocol audit](issue-1/temporal-chain-fee-protocol-audit.md);
this prototype reuses them rather than re-running historical evidence.

## Owner decision

Edo selected the closed-parent context plus one exact Ethereum forming-fee
feature on 2026-07-11. `k=0` remains the physical forming block. The uniform
parent-only contract remains the cross-chain baseline; the Ethereum-enhanced
result must be reported separately because it uses an additional proved fact.
Native estimates, generic chain-fee adapters, retrospective child headers, and
the paper-next-block comparator are not part of the selected clean-break route.

The implementation contract is exact:

- `h` is the decision-time latest closed parent, not `L-confirmation_depth`;
  `t=h+1`, context ends at `h`, candidates begin at `t`, and every
  label/replay/serving target is `h+1+k`.
- Ethereum receives one logical scalar computed by one pure EIP-1559 function
  shared by offline and live preparation and exact relative to the recorded
  parent hash. The physical fee at `t` remains the candidate-zero outcome and
  baseline.
- Polygon and Avalanche omit that scalar. They receive no zero/NaN placeholder,
  native estimate, virtual child, fork adapter, or generic `ChainFeeAdapter`.
  Pre-Lisovo Polygon does not gain a separate selected branch.
- Realized target-row timestamp, cadence, and calendar facts are not inputs.
  Genuine historical lags and trailing rolls may remain; only availability
  shifts that impersonate row `t` are removed. Any extra `t`-derived delta,
  trend, or rolling feature requires separate feature-ablation approval.
- Raw corpora and physical outcomes remain reusable, but the new feature
  geometry, scaler, model, and evaluation artifacts receive a clean semantic
  identity and require retraining. Historical artifacts remain archival; no
  compatibility shim is allowed.

This decision fixes information and target semantics. It does not yet choose
the final action-width/deadline geometry, tie policy, evaluation estimand,
feature-ablation survivors, submission cut-off, or inclusion claim. Those
remain separate map decisions and must not be smuggled into implementation.
Serving may claim only an immediate attempt with conditional eligibility, never
guaranteed inclusion.
