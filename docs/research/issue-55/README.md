# Issue 55: lean single-GPU batch placement

Issue [#55](https://github.com/edoski/spice/issues/55) asked for evidence for a later placement
decision. Edo approved the lean recommendation on 2026-07-14. This report freezes that future
implementation contract; it makes no production change. The audit used only repository contracts,
source code, official documentation, and analytical fake-tensor sizing. It ran no corpus, training,
remote job, or outcome-bearing benchmark. Target-L40 throughput therefore remains unmeasured.

## Fixed boundary

The comparison starts after these owner decisions:

- The task exposes one architecture-neutral two-head output and exactly three concrete families:
  LSTM, Transformer, and Transformer-LSTM ([Issue 23 resolution](https://github.com/edoski/spice/issues/23#issuecomment-4966690587)).
- Lightning 2.6.5 automatic optimization is the only fit host. The intended route is one university
  NVIDIA L40 with native-TF32-enabled FP32, and unsupported hardware, OOM, or semantic failure may
  not silently select another route ([Issue 26 resolution](https://github.com/edoski/spice/issues/26#issuecomment-4970815196),
  [decision contract](https://github.com/edoski/spice/blob/03655db7ad86212f6e78961024e7c22906610a98/docs/research/issue-26/decision-contract.md#L95-L127)).
- One lazy map-style `HistoricalDataset` returns an ordinary CPU mapping containing
  `inputs [C,F] float32`, `label [] int64`, `target [] float32`, `base_fees [K] int64`, and
  `origin_block [] int64`. Default collation, train-only seeded shuffle, sequential validation, and
  `drop_last=False` are fixed. Worker count, prefetch, persistence, and pinning are ephemeral host
  arguments. No custom sampler, collator, batch object, device adapter, or durable worker policy
  survives ([Issue 28 resolution](https://github.com/edoski/spice/issues/28#issuecomment-4959542215)).
- Strict FP32 is the semantic reference and TF32-enabled FP32 is the L40 route. Placement must not
  recreate precision or host machinery ([Issue 62 resolution](https://github.com/edoski/spice/issues/62#issuecomment-4958350990),
  [Issue 78 amendment](https://github.com/edoski/spice/issues/62#issuecomment-4970489252)).
- Trust Lightning for its lifecycle and PyTorch for batching and transfers. Add no fallback state
  machine, application lock, checksum, or duplicated framework validation
  ([Issue 78 resolution](https://github.com/edoski/spice/issues/78#issuecomment-4970463469)).
- Issue [#76](https://github.com/edoski/spice/issues/76) later verifies exactly one integrated path
  on the actual device. It is a readiness gate, not a placement benchmark.

The approved primary scale is `K=5`, `C=200`. Maximum authored feature widths are seven for
Ethereum and six for Polygon/Avalanche. Primary training-origin counts are 1,418,979, 3,267,668,
and 2,000,000 respectively; the separate context study reaches `C=1000`
([approved plan](https://github.com/edoski/spice/blob/03655db7ad86212f6e78961024e7c22906610a98/docs/research/issue-49-temporal-baseline/decision-contract.md#L69-L103)).

## Framework evidence

PyTorch's ordinary path already owns the required mechanics. `DataLoader` supports map datasets,
automatic batching, default mapping collation, seeded sampling, full tail batches, workers, and
automatic pinning. Its default collator preserves a dictionary and batches its tensor values.
`drop_last=False` retains the smaller tail. PyTorch recommends pinned CPU batches rather than CUDA
tensors from multiprocessing workers; it also warns that worker processes can multiply host-memory
use for parent Python objects ([PyTorch 2.7 data loading](https://docs.pytorch.org/docs/2.7/data.html)).
Pinned host memory improves H2D bandwidth and enables asynchronous copies, but pinning is expensive
and excessive pinning can harm the host, so the actual loader arguments still require target-host
measurement ([PyTorch 2.7 CUDA semantics](https://docs.pytorch.org/docs/2.7/notes/cuda.html#use-pinned-memory-buffers)).

Lightning 2.6.5's single-device strategy moves each batch to its root device. The stock transfer
hook accepts nested tensors, lists, dictionaries, tuples, and objects implementing `.to(...)`, then
delegates to `move_data_to_device`
([strategy](https://github.com/Lightning-AI/pytorch-lightning/blob/2.6.5/src/lightning/pytorch/strategies/strategy.py#L263-L279),
[hook](https://github.com/Lightning-AI/pytorch-lightning/blob/2.6.5/src/lightning/pytorch/core/hooks.py#L565-L612)).
For CUDA tensors, that helper calls `.to(device, non_blocking=True)` recursively
([exact 2.6.5 source](https://github.com/Lightning-AI/pytorch-lightning/blob/2.6.5/src/lightning/fabric/utilities/apply_func.py#L78-L110)).
No project transfer override is needed to move the whole approved mapping. A tensor already on the
requested device is returned unchanged ([PyTorch 2.7 `Tensor.to`](https://docs.pytorch.org/docs/2.7/generated/torch.Tensor.to.html)).

CUDA's general rule is to minimize host-device transfers, batch small transfers, and keep reused
intermediate data on-device. It also says pinned memory is required for true transfer/compute
overlap; overlap additionally needs independent work, concurrent-copy hardware, and separate
non-default streams. A non-blocking call alone proves none of those conditions
([CUDA Best Practices: data transfer](https://docs.nvidia.com/cuda/archive/11.8.0/cuda-c-best-practices-guide/index.html#data-transfer-between-host-and-device),
[asynchronous overlap](https://docs.nvidia.com/cuda/archive/11.8.0/cuda-c-best-practices-guide/index.html#asynchronous-and-overlapping-transfers-with-computation)).
The L40 has 48 GB ECC GDDR6; that nominal capacity must also hold parameters, gradients, AdamW
state, activations, selected batches, CUDA context, and allocator reserves
([official L40 data sheet](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/datasheets/L-40/product-brief-L40.pdf)).

## Small comparison

| Candidate | Data and transfer path | Merits | Costs and failure boundary |
| --- | --- | --- | --- |
| Ordinary Lightning/DataLoader | Approved lazy CPU dataset; default mapping collation; `drop_last=False`; DataLoader pinning; Lightning's stock recursive CUDA transfer | Smallest code surface; bounded device memory per batch; all full/tail, shuffle, collation, and transfer behavior framework-owned | Repeats batch construction and H2D transfer each epoch. Pinning and worker count need L40 measurement. |
| Direct device-resident materialization/indexing | Materialize a role's prepared tensors once on CUDA; transfer indices and gather each batch; `num_workers=0` | Removes repeated payload H2D copies and may remove repeated CPU tensorization | Reserves dataset VRAM beside model state; needs custom residency, indexing, lifetime, and failure code; each `index_select` creates new batch storage ([PyTorch 2.7](https://docs.pytorch.org/docs/2.7/generated/torch.index_select.html)); CUDA tensors preclude multiprocessing workers. No target result shows a net win. |

No third placement architecture is evidence-earned. Manual packing, custom streams, background
prefetch, mapped host memory, or a hybrid cache would add concepts and state without an observed
bottleneck.

### Analytical scale

The stale branch's dense CUDA representation uses, per role,

```text
N * (4*C*F + C + 2*K + 12) bytes
```

for float32 inputs, one boolean input mask, two boolean action masks, int64 offsets, and float32
targets. This excludes gather outputs, model/optimizer state, activations, allocator reserve, and the
separately resident validation role.

| Chain | `N` | max `F` | dense CUDA at `C=200` | dense CUDA at `C=1000` | ordinary CPU training store | ordinary `B=64,C=200` batch |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ethereum | 1,418,979 | 7 | 7.694 GiB | 38.353 GiB | about 86.6 MiB | 0.345 MiB |
| Polygon | 3,267,668 | 6 | 15.283 GiB | 76.148 GiB | about 187.0 MiB | 0.297 MiB |
| Avalanche | 2,000,000 | 6 | 9.354 GiB | 46.607 GiB | about 114.4 MiB | 0.297 MiB |

The CPU-store column sizes one shared float32 row tensor, int64 fee/block vectors, and the
training-role origin/label/target vectors, ignoring the few boundary-support rows. The batch column
includes all five approved mapping tensors at `K=5`. These are deterministic byte counts, not peak
memory or throughput measurements. They show why nominal 48 GB cannot justify dense residency:
Polygon `C=1000` exceeds it before training state, and the other `C=1000` cases leave unsafe or no
headroom. Even `C=200` must count validation residency and the largest of three model families.

## Read-only stale-branch audit

The audit used `git show` against `codex/fast-ab-training@97541165fcec9e09a2c80f1451f4508acf5b8ca1`.
It did not switch branches. Commit `efad41d4fea85b03c31886e0bac7412262f59f3b` adds net 273
production lines across exactly four files:

- `src/spice/modeling/batch_plan.py:61-76,151-179,255-320,323-403`
- `src/spice/modeling/representations/sequence_inputs.py:17,116-211,275-369`
- `src/spice/prediction/contracts.py:45-54`
- `src/spice/prediction/families/min_block_fee_multitask/batch.py:68-109`

The code is useful as a rejected experiment, not an implementation base:

- Device residency is enabled by default through `SPICE_FAST_DEVICE_BATCHES`. It allocates full
  dense input, input-mask, and action-mask CUDA tensors before filling them. A 256 MiB constant
  bounds only the three ordinary NumPy staging arrays for one fill chunk; it does not bound total
  device memory, pin the staging memory, or establish transfer/compute overlap.
- `estimated_storage_bytes` is added to protocols and implementations but never read. There is no
  model/optimizer/activation headroom calculation. Training and validation plans are both built and
  retained (`training_runtime.py:50-68`).
- Each batch copies CPU positions to CUDA and performs six `index_select` allocations: three input
  tensors and three target tensors. It retains full and tail batches through `ceil` plus the final
  short index list, and host/device paths share the same seeded custom sampler. Reconstruction still
  restarts its private epoch counter, matching neither the now-approved ordinary generator nor an
  exact-resume claim.
- The representation predates the fixed-context contract. It materializes an input mask and
  duplicates the action mask in inputs and targets, although the approved dataset/task removed those
  masks.
- Allocation OOM is caught, `torch.cuda.empty_cache()` is called, and execution silently falls back
  to the host loader. This directly conflicts with the selected host's fail-closed rule and makes the
  actual path ambiguous. Later batch/model OOM is not handled by this fallback.
- Its integration context disables Lightning transfer with a no-op hook and manually calls
  `batch.to_device(...)` in each step (`lightning_module.py:69-76,90-100`). Issue 26 selected native
  automatic optimization; Issues 26/28 explicitly remove that duplicate transfer path.
- Residency is runtime-only and does not enter the checkpoint, which is correct. That narrow good
  property does not justify its protocols, environment switches, duplicated masks, or fallback.

## Approved placement contract

The future clean implementation uses the approved lazy CPU dataset, ordinary DataLoaders,
`drop_last=False`, `pin_memory=True` on the L40, and Lightning 2.6.5's native recursive transfer.
Lightning moves the whole five-tensor mapping, including `base_fees` and `origin_block`. This
supersedes only Issue 26's field-selective transfer wording. Add no custom transfer hook, batch
wrapper, device adapter, collator, sampler, residency protocol, OOM fallback, custom stream, or
worker-policy abstraction. Begin with `num_workers=0`; change to a small positive worker count only
if target evidence shows a material loader bottleneck. Keep worker, prefetch, and persistence values
as ephemeral direct arguments.

Direct residency is not part of this decision. The `codex/fast-ab-training` branch remains isolated
experimental evidence and must not be merged or absorbed. A later shape-accurate fake-data L40
measurement may earn a fresh, narrow optimization decision if the ordinary path shows a material
input/transfer bottleneck and the complete train-plus-validation working set leaves safe peak
headroom for all three families. No such optimization is approved here.

If a fresh optimization decision is later commissioned, its bounded L40 probe should use identical
fake origins, initialized weights, seed, full/tail batches, loss, and updates. Record synchronized
end-to-end epoch time, samples/s, transfer time only if it can be isolated without custom runtime
machinery, peak allocated and reserved CUDA memory, host RSS, failure behavior, and exact loader
arguments. CUDA events provide accurate device timing
([PyTorch 2.7 `Event`](https://docs.pytorch.org/docs/2.7/generated/torch.cuda.Event.html));
`reset_peak_memory_stats`, `max_memory_allocated`, and `max_memory_reserved` provide allocator peaks
([PyTorch CUDA memory API](https://docs.pytorch.org/docs/2.7/cuda.html#memory-management)). Issue 76
later verifies the integrated approved path without fallback; it is not reopened as a placement
benchmark.
