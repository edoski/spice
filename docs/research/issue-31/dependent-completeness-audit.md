# Issue 31 dependent completeness audit

Status: complete read-only/code-and-contract audit for the approved final contract. No production,
configuration, test, corpus, artifact, acquisition, training, evaluation, serving, job, or archive
state changed.

## Verdict

The contract is dependency-safe and leaves no hidden consequential Issue 31 choice. It introduces
two direct preparation interfaces because historical and live right edges are materially different,
then consumes existing owners for everything else. The prototype adds no production abstraction and
does not choose open durable-record, serving-schema, host-placement, or lifecycle work.

The issue body's action-mask and finalized-context wording is stale. Issue 24 explicitly removes
action masks and the confirmation-depth clock; Issues 45/46 make the decision parent the latest
closed canonical `h`; Issue 28 makes live input exactly the final `C` closed rows. The corrected
contract records `last_finalized_context` only as comparator/audit information outside the live
preparation interface.

## Consumed closed contracts

- **Issue 23:** one architecture-neutral `MinBlockFeeOutput([B,K], [B])`; the auxiliary scalar
  survives output validation and loss/reporting, while only decoded `k` schedules.
- **Issue 24:** direct origin/outcome/action functions; separate live preparation; no compiler,
  action mask, mode flag, fake store, or combined preparation state.
- **Issue 28:** one lazy `HistoricalDataset`, exact five-tensor CPU mapping, separate feature/target
  states, and bit-identical offline/live feature transformation.
- **Issues 45/46:** freeze latest closed parent `(h, hash(h))`; context ends at `h`; targets are
  `h+1+k`; confirmation depth never moves the action clock backward; no virtual row is required;
  Ethereum alone adds its exact parent-derived forming fee.
- **Issue 47:** canonical fail-closed rows, `C=200`, `H=0`, exact feature order/availability, strict
  training-only feature state, complete outcomes, and no target-row inputs.
- **Issue 48:** exhaustive exact block-origin ranges, fixed `K`, and every eligible requested origin
  once. Timestamp/seconds-derived windows do not survive this seam.
- **Issue 58:** exact positive raw hindsight minimum over `h+1..h+K`, earliest label, natural-log
  training z-score target, and no live action or fee-quote semantics.

## Current caller audit and future disposition

| Current surface | Finding | Contract disposition |
| --- | --- | --- |
| `modeling/artifact_inference.py` | Rebuilds feature/problem/prediction/evaluator contracts, computes seconds support, passes an empty history frame plus an evaluation frame, and permits timestamp windows. | One canonical frame plus one exact inclusive origin window enters historical preparation. Artifact/evaluator owners keep their distinct validation and scoring work. |
| `modeling/dataset_builders/fixed_sequence_temporal.py` | Sorts/deduplicates, derives sequence length and actions from seconds, resplits roles, combines training/inference preparation, and constructs compiled stores. | Deleted by Issue 24's clean break. Direct origin selection, frozen states, and the Issue 28 dataset replace it without a wrapper. |
| `features/core.py` | Sorts rows and silently repairs some warmup/nonpositive fee paths. | Feature owner must emit the approved direct rows and strict transform. Both preparers call that same owner; neither repairs. |
| `serving/live_blocks.py` | Fetches `latest-confirmation_depth`, so depth two ends context at `L-2`. | Fetch/freeze the exact latest closed `(h,hash(h))` after artifact selection, then provide exactly `C` rows through `h`. Finality transport facts cannot anchor the action clock. |
| `serving/inference.py` | Builds a fake problem store, seconds-derived action mask, and target from the stale observed row; public response adds timestamp/wait/TTL facts. | Separate live preparation returns only `[1,C,F]`; direct task output validation/decode and temporal arithmetic follow. Issues 22/33/43 own later request, response, persistence, and mobile lifecycle. |
| `modeling/scoring.py` and current prediction family | Decodes through a generic result buffer and action mask; the auxiliary head is not carried by the decoded result. | Issue 23's direct full output is validated first. Predictive scoring may consume both heads; scheduling consumes only decoded `k`. No generic result ABI survives. |
| artifact manifests/loaders | Persist old selectors, capability metadata, and incomplete direct task facts. | Issue 31 only requires the direct mismatch checks. Issue 34 owns final placement/serialization; no local record choice is inferred. |
| evaluation/replay | Uses decoded-result/evaluator registries and sampled/seconds paths. | Issue 48's exhaustive exact requested origin range consumes the historical dataset and raw outcomes. Scoring/accounting stay separate owners. |

## Fail-closed completeness

Historical preparation must reject wrong chain/regime, malformed canonical order/domain, missing
`first-C+1 .. last+K` support, non-exact requested origins, mismatched `C/K`, feature/target state or
provenance mismatch, nonfinite transforms, and invalid raw outcomes. It never fits state, changes the
window, or repairs rows.

Live preparation must additionally reject any row count other than `C`, a final row other than the
frozen parent, wrong parent hash, stale/reorged snapshot, artifact/input-width mismatch, and
nonfinite model input/output. It has no outcome-dependent checks because future outcomes do not
exist. The serving owner must revalidate the head/hash and exact trigger before response/broadcast;
Issue 31 does not add RPC or scheduler behavior.

The exact output validator checks `[B,K]` finite floating logits and `[B]` finite floating
`minimum_fee_z`. First-index argmax produces `k`. Temporal action functions alone validate
`0 <= k < K`. No mask, fallback, overflow, late broadcast, reinference, reschedule, cancellation,
replacement, seconds estimate, or virtual target is legal.

## Ownership handoffs

- Issue 34 remains open and owns the final durable artifact/evaluation record and serialization.
- Issue 43 remains open and owns the final serving/mobile block-horizon selection and API/client
  schema, including any explicitly approved non-actionable auxiliary display.
- Issue 33 owns the serving store and lifecycle; Issue 22 already fixes its trust and observation
  transitions.
- Issues 26/55 own framework-native host transfer and CUDA loader tuning. Preparation ends at CPU
  mappings/tensors.
- Model/task, predictive scoring, economic accounting, corpus sealing, RPC transport, scheduler,
  and publication remain with their named owners. This ticket absorbs none of them.

These are existing ownership edges, not unresolved Issue 31 choices. No sibling issue mutation is
needed.

## Lean later verification

Production implementation needs one focused behavior fixture, parameterized only by Ethereum versus
parent-only feature width, covering exact requested origin endpoints/support, historical/live input
identity at the same `h`, no future live fields, direct artifact mismatches, full two-head output,
all-`K` actionable mapping, and depth-two stale-clock rejection. Reuse the Issue 28 dataset fixture
for item/default-collation behavior and the temporal action fixture for arithmetic; do not duplicate
their internal tests.

Add no compatibility, migration, old/new parity, mode/registry, architecture-transition, stochastic
replay, real corpus, model-quality, or serving-UI test. The disposable prototype is structural
evidence, not an implementation test suite.
