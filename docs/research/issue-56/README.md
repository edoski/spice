# Issue 56 compact-source CUDA placement prototype

Status: disposable evidence candidate awaiting final complete-contract approval. Edo authorized
only the compact-source challenger for Issue 40's bounded fake-data NVIDIA L40 gate. Expanded
five-tensor residency is rejected. Ordinary lazy CPU placement remains the approved implementation
contract until Issue 57 chooses otherwise.

This directory changes no production, configuration, test, dependency, corpus, storage,
acquisition, training, tuning, evaluation, Slurm, serving, archive, sibling-issue, or native-graph
state.

## Question and bound

Can one fit-scoped compact CUDA source preserve the approved five-field Lightning batch contract
while removing repeated CPU window construction and host-to-device batch transfer? The cheapest
local observation is exact full/tail mapping and same-weight one-update parity on synthetic tensors,
plus direct storage arithmetic and fail-loud behavior. CUDA speed, peak memory, and materiality stay
with Issue 40.

Run the disposable prototype:

```bash
uv run python docs/research/issue-56/prototype.py --all
```

The scientific workload is independent authority:

- primary, default, headline, and serving context: `C=200`;
- descriptive context grid: `C={50,100,200,400}` at `K=5`;
- primary and headline horizon: `K=5`;
- final horizon grid: `K={2,3,4,5,10,15,30,50,100,200}` at `C=200`;
- physical batch `64`, gradient accumulation `1`, and full tail batches.

The axes are not Cartesian. The actual boundary cells are `C=400,K=5` and `C=200,K=200`.
Placement consumes these choices and selects none. The local `C=400,K=200` data-only fixture is a
maximum-axis indexing envelope, not an approved scientific cell.

## Authorized Issue 40 challenger

One fit-scoped source owns exactly one CUDA `float32 features[R,F]`, `int64 base_fees[R]`, and
`int64 block_numbers[R]` store shared by training and validation. Each role owns only CUDA `int64
origins[N]`, `int64 labels[N]`, and `float32 targets[N]`. `Tensor.unfold` creates zero-storage
history and future views.

An ordinary index `DataLoader` binds one `role.gather` collator. With `num_workers=0`, each batch
moves only its small CPU position list, maps positions to origins, and uses device `index_select` to
produce exactly `inputs`, `label`, `target`, `base_fees`, and `origin_block`. The candidate omits
`pin_memory` and `drop_last`; the latter remains the ordinary `False` default. Lightning 2.6.5
native recursive transfer stays enabled and is a same-device no-op for the produced tensors.

The only intended private production seam, if later selected and authorized, is:

```python
_resident_fit_loaders(prepared, device) -> (training_loader, validation_loader)
```

It reads `C` and `K` from the exact prepared request and consumes the fixed host batch/accumulation
contract. It chooses no scientific value. The loaders remain outside `FitModule`, so the native
Lightning checkpoint contains no source, role, view, loader, or placement state.

OOM or another source, gather, model, optimizer, or transfer failure propagates. There is no
`empty_cache` recovery, retry, fallback to ordinary placement, reduced batch/context/horizon/family,
sequential role swapping, capacity planner, selector, toggle, placement field, transfer hook,
wrapper, registry, custom stream, second fit path, or execution-only branch.

Compared with ordinary placement, this adds one shared source owner, two lightweight role owners,
zero-storage sliding views, an index-only loader, and one device gather concept. The estimated clean
production delta remains 40–55 lines and one focused five-field full/tail mapping fixture. It is
less conventional than lazy CPU loading, but uses standard PyTorch tensors, views, `DataLoader`, and
Lightning transfer behavior. The stale `codex/fast-ab-training` branch remains read-only historical
evidence; its expanded arrays, staging, masks, unused estimate, and OOM fallback do not advance.

## Disposable evidence

The updated local CPU run passes:

- One truly shared source feeds both fake fit roles through the exact private seam. At
  `C=200,F=6,K=5,B=64`, training and validation each preserve full/tail sizes `[64,1]`; all five
  fields match ordinary loading exactly.
- The micro semantic fixture is `C=4,F=3,K=3,B=4`, accumulation `1`. For LSTM, Transformer, and
  Transformer-LSTM, ordinary and compact placement have the same shuffled origin order, full/tail
  sizes `[4,1]`, tensors, raw outputs, loss, decoded actions, and final weights after two Lightning
  automatic-optimization updates. Observed maximum deltas are `0.0`; the compact repeat is exact.
- The `N=4,097,C=400,F=6,K=200,B=64` maximum-axis data fixture has exact five-field and tail-one
  parity. Its local CPU traversal shows only that compact indexing is plausible. It is not CUDA,
  model-throughput, or material-speed evidence.
- Simulated source allocation failure raises `torch.OutOfMemoryError`; it does not select another
  route.
- Ordinary file transfer followed by strict native Lightning Mac loading remains placement
  independent. The `[2,1]` artifact-consumer batches are a bounded smoke fixture, not training
  batch authority. Issue 26 already supplies the accepted native consumer evidence for all three
  families.

For the current Polygon planning week, shared compact storage is:

```text
compact bytes = R*(4F + 16) + 20*(N_train + N_validation)
expanded bytes = (N_train + N_validation)*(4CF + 8K + 20)
```

`R=3,576,915`, `F=6`, and validation cardinality remains acquisition-dependent. Each extra
validation row adds only 60 compact bytes.

| Actual workload cell | Train/validation tails | Compact source + roles | One B64 batch | Rejected expanded roles |
| --- | --- | ---: | ---: | ---: |
| Primary `C200,K5` | `20 / 40` | 214,602,920 B = 204.661 MiB | 311,040 B = 0.297 MiB | 17,380,895,760 B = 16.187 GiB |
| Descriptive max `C400,K5` | `15 / 43` | 214,606,720 B = 204.665 MiB | 618,240 B = 0.590 MiB | 34,549,047,960 B = 32.176 GiB |
| Final-horizon max `C200,K200` | `20 / 40` | 214,602,920 B = 204.661 MiB | 410,880 B = 0.392 MiB | 22,959,948,720 B = 21.383 GiB |

These compact values exclude gathered batches, parameters, gradients, AdamW state, activations,
CUDA/framework workspaces, allocator reserve, and fragmentation. They establish only that source
capacity is no longer the contradiction. Actual L40 free and peak memory remain unmeasured.

Expanded `N×C×F`/`N×K` residency is rejected. Its earlier `C400,K200` 37.368 GiB calculation was a
non-scientific maximum-axis envelope; it must not become the Issue 40 workload.

## Issue 40 handoff

Issue 40 compares ordinary placement with compact-source placement only, using fake/synthetic data
on the actual L40 under the frozen TF32-enabled FP32 Lightning automatic-optimization policy. It
must use physical batch 64 and accumulation 1. Placement may not change a row, origin, C, K, family,
batch, or accumulation choice.

The bounded shape set is the three actual cells above. Exercise LSTM, Transformer, and
Transformer-LSTM at each cell because any family may later win. Use one shared Polygon-sized source
and simultaneous training/validation role metadata for each run. A small Ethereum `F=7` mapping
probe may confirm the only wider feature shape; Polygon remains the source-cardinality case. Do not
add the unapproved `C400,K200` Cartesian cell.

For identical source facts, role state, initialized weights, seed, shuffle order, and full/tail
batches, record direct:

- shape, dtype, value, origin-order, and membership equality for all five fields;
- raw outputs, loss, decoded actions, finite gradients, and one optimizer update/final weights;
- deterministic same-host repeats under the approved numerical tolerance;
- setup cost, synchronized steady end-to-end timing, and ordinary versus compact throughput;
- host RSS, CUDA allocated/reserved/free memory, source/batch bytes, and peak through the first
  AdamW step and validation;
- ordinary transfer plus strict native Lightning checkpoint loading/inference on the Mac.

Any field/order/full-tail mismatch, decoded-action mismatch, out-of-tolerance numerical delta,
nonfinite value, OOM, repeat failure, artifact-load failure, duplicated shared source, hidden
expanded window storage, fallback, or selector machinery rejects the candidate. OOM may not be
made to pass by reducing science or swapping roles. Timing and memory are reported as evidence;
Issue 57 alone decides whether the benefit merits one lean main-path integration. Zero or immaterial
benefit means discard. Issue 76 later verifies only the integrated winner and is not a placement
benchmark.

## Completion boundary

No consequential Issue 56 owner choice remains after Option B. Exact future role counts and Issue
40's numerical/timing protocol do not change this candidate and remain with their owning work.

The remaining authority is explicit final complete-contract approval. That approval authorizes
only publication of this ticket-scoped research/prototype, one Issue 56 Resolution, closing Issue
56, one map pointer or explicitly approved fog correction, and verification. It does not authorize
Issue 40 execution, production/config/test mutation, candidate integration, Issue 57 placement,
real data or thesis execution, or any further scientific choice.
