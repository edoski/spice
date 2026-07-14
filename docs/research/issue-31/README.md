# Issue 31 historical/live preparation prototype

Status: final complete contract explicitly approved by Edo on 2026-07-14. This is
planning/prototype work only. It changes no production code, configuration, tests, corpus, artifact,
training, evaluation, acquisition, serving process, job, or archive.

Run every probe:

```bash
uv run python docs/research/issue-31/prototype.py --all
```

Run the small interactive view:

```bash
uv run python docs/research/issue-31/prototype.py
```

## Question and bound

Can one direct historical requested-origin-window preparer and one distinct live right-edge preparer
share the approved feature transformation and action arithmetic while preserving exact requested
coverage, no-future inputs, artifact facts, the architecture-neutral two-head task output, and an
actionable target for every `k`?

The cheapest discriminating observation was one synthetic CPU frame with `C=200`, `K=5`, one
Ethereum exact-forming-fee artifact, and one parent-only artifact. The budget was under two minutes,
32 MiB, and zero model fit, training, real corpus, RPC, or outcome-bearing execution. The stop
condition was exact origins, offline/live input identity, depth-two actionability, full-output
validation, and representative fail-closed mismatches. The probes reached it in one local run.

## Observations

- One canonical frame prepared exactly origins `1208..1210`, not an expanded or shortened result.
  Its minimal support was exactly `1009..1215 = first-C+1 .. last+K`. Removing block `1009` failed;
  nothing padded, clipped, sorted, deduplicated, or repaired the frame.
- The final historical item and live input at frozen parent `h=1210` were bit-identical
  `[200,3] float32` values. Historical preparation separately retained its label, standardized
  auxiliary target, raw five-fee outcome window, and origin block. Live accepted exactly the final
  200 closed rows through `h` and emitted `[1,200,3]`; it received no future row, outcome, label,
  target, mask, or fabricated current row.
- All 206 synthetic modern-Ethereum transitions matched the parent-only integer EIP-1559 recurrence.
  The same two preparers also matched on a Polygon Lisovo `[1,200,2]` parent-only artifact. Polygon
  had no forming-fee placeholder; Avalanche has the same structural parent-only route.
- With `latest_rpc_head=L=1210` and depth two, the old finalized-context clock gives
  `last_finalized_context=1208` and stale `k=0` target `1209`, already closed. The selected clock
  freezes `h=L`, so `first_actionable_target=1211` and every target `h+1+k` is later than `L`.
  No magic `+depth` correction exists.
- The injected architecture-neutral output remained exactly
  `MinBlockFeeOutput(action_logits [1,5], minimum_fee_z [1])`. It decoded `k=2`, trigger `1212`,
  and target `1213`. Changing only `minimum_fee_z` from `0.375` to `-8.0` changed neither action nor
  schedule. The scalar survived validation unchanged; the prototype did not expose it as a quote.
- Missing historical support, a stale live right edge, a non-scalar auxiliary head, and malformed
  auxiliary output all failed closed.

## Approved final contract

Edo approved these clauses as one complete contract on 2026-07-14.

1. **Historical interface.** Keep one direct
   `prepare_historical_window(frame, artifact, RequestedOriginWindow(first_origin_block,
   last_origin_block))`. The requested endpoints are inclusive origin blocks. The function consumes
   one already canonical, content-bound, chain/regime-labelled frame; requires exact support
   `first-C+1 .. last+K`; returns every requested origin once in order; and fails if any support,
   context, or outcome row is missing. It may slice minimal support from a larger frame, but never
   changes the requested origin window.
2. **Historical result.** Reuse Issue 28's one concrete lazy `HistoricalDataset` and five CPU tensor
   fields: `inputs [C,F] float32`, scalar `label int64`, scalar `target float32`,
   `base_fees [K] int64`, and scalar `origin_block int64`. Context ends at `h`; raw outcomes are
   `h+1..h+K`; deterministic earliest raw-integer minimum supplies the label and Issue 58 target.
   Preparation applies frozen feature/target states and fits neither.
3. **Live interface.** Keep a separate `prepare_live(closed_rows, artifact, frozen_parent)`.
   `closed_rows` is exactly the final `C` consecutive closed rows ending at frozen `(h, hash(h))`.
   It returns only `[1,C,F] float32`. It has no historical/live mode flag, optional outcome fields,
   dataset, target, action mask, virtual row, repair, or fitted state.
4. **Actionable head.** The decision parent `h` is the selected artifact's decision-time
   `latest_rpc_head`, not `latest_rpc_head-confirmation_depth`. An older
   `last_finalized_context` may be observed to explain or audit transport finality, but it is not a
   preparation input, model anchor, or action clock and does not survive as a serving-preparation
   interface field. `first_actionable_target=h+1`; `broadcast_after_block=h+k`; and
   `target_block=h+1+k`. A later head/hash change, missing row, reorg, stale snapshot, or passed
   trigger fails closed under the serving owner.
5. **No virtual current row.** The approved closed-parent contract needs no fabricated row.
   Historical and live inputs end at physical closed parent `h`. Ethereum adds its one exact
   parent-derived forming-fee feature on each physical parent row; Polygon and Avalanche omit the
   dimension. No placeholder, estimate, generic chain adapter, target-row timestamp, or future fact
   enters the live input.
6. **Artifact and output parity.** Before either preparation path, validate direct chain/regime,
   `C`, `K`, ordered feature formulas/state/provenance, target state/provenance, input width,
   `K`-wide action head, scalar auxiliary head, concrete model facts, and exact state-dict
   compatibility. Live inference then validates the complete finite
   `MinBlockFeeOutput(action_logits [1,K], minimum_fee_z [1])` before first-index argmax decode.
   Scheduling receives only decoded `k` and frozen parent facts, so `minimum_fee_z` cannot override,
   repair, or reinterpret the action.
7. **Auxiliary ownership.** Historical training/scoring retains the exact standardized Issue 58
   target and raw outcomes. Live inference preserves and validates the scalar task output, but this
   ticket chooses no public API field, durable record field, native inverse, displayed fee quote, or
   serving claim for it. Issues 34 and 43 retain those record/schema decisions. Absence from the
   scheduler is not permission to delete the head.
8. **Seam placement.** Historical and live preparation are two real modules because their right-edge
   algorithms differ. Within preparation they share only direct feature construction/transformation;
   action arithmetic remains the separate tiny temporal owner, and factual artifact validation
   remains artifact-owned. Add no `mode`, request union, preparer registry, Adapter, compiled
   callable bag, generic batch, compatibility reader, alias, or transition path.
9. **Issue-body supersession.** Closed Issues 23, 24, 28, 45, 46, 47, 48, and 58 supersede Issue
   31's earlier requests to preserve action masks or let confirmation depth anchor the model. Every
   exact-`K` action is valid. The historical and live paths prove input/action parity without a mask
   or stale finalized-context clock.

This is the smallest architecture-neutral seam found. Deleting the historical module would spread
exact-window support, label/target alignment, and dataset construction across training and
evaluation. Deleting the live module would spread frozen-head, exact-right-edge, no-future, and
input-shape checks across serving. Merging them creates illegal optional fields and hides two
algorithms. The shared task output already covers all three approved concrete architectures, so no
new model seam is needed.

The [dependent completeness audit](dependent-completeness-audit.md) found no additional
consequential Issue 31 choice. The approval authorizes only this ticket-scoped evidence publication,
Resolution/closure, map pointer, and verification described by the delegation contract. It does not
authorize implementation or real execution.
