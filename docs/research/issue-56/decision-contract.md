# Issue 56 complete decision contract

Status: final approval candidate. This is planning/prototype authority only.

## 1. Owner decision

Edo authorizes only the fresh compact source-resident CUDA candidate to enter Issue 40's bounded
fake-data NVIDIA L40 evidence gate. Expanded five-tensor `N×C×F`/`N×K` residency is rejected.
The stale `codex/fast-ab-training` branch, its staging/masks/fallback, and any execution-only branch
route remain rejected evidence.

Issue 55's ordinary lazy CPU `HistoricalDataset`, pinned ordinary `DataLoader`, and Lightning native
whole-batch transfer remain the approved future implementation contract until Issue 57 reviews the
target evidence and Edo chooses either discard or one lean main-path integration.

This decision authorizes evidence only. It authorizes no implementation, production path,
configuration, test, dependency, corpus, storage, acquisition, training, tuning, evaluation,
Slurm, serving, archive, branch, integration, final placement, or real thesis outcome.

## 2. Independent scientific workload

Placement consumes and never selects the approved workload:

- primary/default/headline/serving `C=200`;
- descriptive `C={50,100,200,400}` at `K=5`;
- primary/headline `K=5`;
- final `K={2,3,4,5,10,15,30,50,100,200}` at `C=200`;
- physical batch `64`, gradient accumulation `1`, and complete tail batches.

The C and K axes are not Cartesian. Issue 40 uses the actual primary `C200,K5`, descriptive maximum
`C400,K5`, and final-horizon maximum `C200,K200` cells. It does not add `C400,K200`. A later explicit
scientific amendment would replace these consumed facts; placement can never motivate or perform
that amendment.

## 3. Exact candidate

One fit-scoped CUDA source owns one shared `float32 features[R,F]`, `int64 base_fees[R]`, and
`int64 block_numbers[R]` store spanning the contiguous training/validation source union. Training
and validation each own only `int64 origins[N]`, `int64 labels[N]`, and `float32 targets[N]`.
History and future `Tensor.unfold` views share the source's existing storage; no sample-expanded
window or fee tensor is retained.

The private construction seam is exactly:

```python
_resident_fit_loaders(prepared, device) -> (training_loader, validation_loader)
```

It reads C and K from the exact prepared request and consumes batch 64/accumulation 1 from the fit
host. It creates the shared source once, then binds one role owner to each loader.

Each ordinary index `DataLoader` uses training shuffle or sequential validation, `num_workers=0`,
and a bound `role.gather` collator. The candidate omits `pin_memory` and `drop_last`; ordinary
`drop_last=False` behavior therefore survives. The collator moves only the small CPU position list,
maps positions to CUDA origins, and uses device `index_select` to emit exactly:

1. `inputs`;
2. `label`;
3. `target`;
4. `base_fees`;
5. `origin_block`.

Lightning 2.6.5 native recursive transfer remains enabled and is a same-device no-op. There is no
custom sampler, batch wrapper, transfer hook, placement configuration, selector, registry, planner,
fallback, custom stream, alternate fit path, or checkpoint field.

Source, role, view, and loader lifetime remains outside `FitModule`. The durable artifact is the
unchanged native Lightning weights-only best checkpoint. Portability remains ordinary transfer
followed by strict native Mac loading and inference. Placement creates no source, runtime, branch,
or artifact fact.

Any source, view, gather, transfer, model, optimizer, or memory failure propagates. There is no
`empty_cache` recovery, retry, ordinary-path fallback, batch/C/K/N/family reduction, sequential role
swapping, rematerialization, or partial success.

## 4. Preliminary bounded evidence

The disposable local CPU prototype establishes only candidate plausibility:

- The exact private seam gives fake training and validation roles one shared source. At
  `C200,F6,K5,B64`, both preserve exact five-field full/tail batches `[64,1]`.
- At the micro semantic shape `C4,F3,K3,B4`, accumulation 1, LSTM, Transformer, and
  Transformer-LSTM preserve shuffled origin order, all five fields, raw outputs, loss, decoded
  actions, and final weights after two Lightning automatic-optimization updates. Observed deltas are
  zero and the compact repeat is exact.
- A data-only `N4097,C400,F6,K200,B64` maximum-axis envelope preserves all five fields and tail one.
  It is not an approved science cell or a CUDA/model speed result.
- Simulated compact-source allocation OOM propagates without route change.
- The accepted Issue 26 native artifact probe remains placement-independent.

For the estimated Polygon role week, each actual request is about 204.66 MiB of compact shared
source plus role state. The largest actual B64 mapping is 0.590 MiB at `C400,K5`. These are tensor
inventory calculations, not actual free or peak L40 memory. Expanded residency remains rejected:
it is 16.187 GiB at primary `C200,K5`, 32.176 GiB at descriptive `C400,K5`, and 21.383 GiB at
final-horizon `C200,K200`, before model/runtime state.

The clean candidate adds an estimated 40–55 production lines and one focused five-field full/tail
mapping fixture over ordinary placement. Its extra concepts are one shared resident source, two
role metadata owners, zero-storage sliding views, one index loader, device gather, and one fail-loud
allocation lifetime.

## 5. Issue 40 evidence handoff

Issue 40 compares only ordinary versus compact placement on fake/synthetic data on the actual L40
under the frozen TF32-enabled FP32 Lightning automatic-optimization policy. Use physical batch 64,
accumulation 1, full and tail batches, and the three actual workload cells from section 2. Exercise
LSTM, Transformer, and Transformer-LSTM at each cell because any family may later win. Use the
Polygon-sized shared source and simultaneous fit-role metadata; one small Ethereum `F=7` mapping
probe may cover its wider input without a second full source allocation.

For identical source facts, role state, initialized weights, seed, batch order, and prepared
batches, record direct:

- five-field shape/dtype/value/order/membership equality;
- outputs, loss, decoded actions, finite gradients, and one update/final weights;
- deterministic repeats within the Issue 40-approved numerical tolerance;
- setup and synchronized steady end-to-end timing;
- host RSS and CUDA allocated/reserved/free/peak memory through source placement, gather, forward,
  backward, first AdamW step, and validation;
- source/batch tensor bytes and native Mac artifact load/inference.

Any mapping/order/tail mismatch, decoded-action mismatch, out-of-tolerance delta, nonfinite value,
OOM, repeat failure, artifact-load failure, duplicated source, hidden expanded storage, fallback, or
selector machinery rejects the candidate. Passing may not require reducing the scientific workload
or swapping roles. Timing and memory are evidence, not a placement decision. Temporary comparison
code is removed after the report.

Issue 57 alone judges materiality and chooses discard or one main integration. Zero, slower, or
immaterial benefit supports discard. Issue 76 verifies only the integrated winner after full-system
integration; it does not replace Issue 40.

## 6. Closure authority

No consequential Issue 56 owner choice remains. Exact future validation counts, numerical
tolerance, repetitions, and synchronized timing protocol remain with Issue 40 and do not alter this
candidate contract.

Explicit final approval of this complete contract authorizes only:

- publication of the ticket-scoped Issue 56 research/prototype;
- one Resolution on Issue 56;
- closing only Issue 56;
- one map decision pointer or explicitly approved fog correction;
- verification of those bounded mutations.

It does not authorize Issue 40 execution, production/config/test mutation, candidate integration,
Issue 57 placement, scientific amendment, real data, or outcome-bearing execution.
