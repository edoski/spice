# Issue 26 lean training-host prototype

Status: owner-approved final contract, 2026-07-14. This research changes no production,
configuration, test, data, job, or sibling-issue state. The earlier direct-PyTorch, broad-best,
plain-state projection, custom-parser, and post-fit-resave recommendations are withdrawn.

Closed Issue 78 is binding: one operator, UUID instances, owner-local hidden scratch, direct
absent-destination `pathlib` rename, native package behavior, and no production digest, inventory,
application lock, publication machinery, or automatic recovery.

Choose Lightning 2.6.5 automatic optimization as the sole Train and Tune-private fit host. After
the corrected comparison, direct PyTorch is not materially leaner across the complete lifecycle.
It retains a narrow transparency/dependency preference, but SPICE would have to own the optimizer
loop, clipping timing, stopping, best selection, continuation serialization, and restoration.

The corrected Train layout is literal:

```text
artifacts/.<artifact_id>/       weights-only best plus broad last during fit
artifacts/<artifact_id>.ckpt   selected best after direct pathlib rename
```

The leading dot is the only scratch convention. There is no `.work` suffix, configured private
root, suffix parser, work-kind abstraction, lifecycle record, or cleanup API. The operator may
remove the hidden directory after success.

The monitored best uses stock `ModelCheckpoint(save_weights_only=True)` because its only consumer
is the canonical inference artifact. Lightning weights-only mode still stores native wrapper state,
the module state dict, and saved constructor hyperparameters. The separate broad `last.ckpt` owns
optimizer, callback, precision, and loop continuation through stock `Trainer.fit(ckpt_path=...)`.

One strict JSON-safe domain record is saved through Lightning hyperparameters before fit. It contains
only the exact pre-minted-ID TrainRequest association, fitted feature/target/classification-loss
states, and the effective model/task mathematics. Lightning writes, selects, loads, and strictly
restores the checkpoint. SPICE adds no final save, parser, state-key/shape/dtype inventory, digest,
payload inventory, byte length, corruption checker, sidecar, best revalidation, or publication-time
reload.

The public load seam is only a facade over the native API:

```python
module = FitModule.load_from_checkpoint(
    path,
    map_location="cpu",
    weights_only=True,
    strict=True,
)
```

The constructor validates the domain record and builds the concrete family; Lightning owns strict
weight restoration. A private resume hook may compare only that domain record with the current fit
association. Same-shape, structurally loadable corruption or substitution may remain undetected;
that residual risk is explicitly accepted.

Validation uses one loss-agnostic TorchMetrics 1.9.0 reducer:

```python
MeanMetric(nan_strategy="disable", sync_on_compute=False).set_dtype(torch.float64)
```

The task supplies detached per-origin total losses. The host updates the metric without explicit
weights, checks its exact final unit weight against the frozen validation cardinality, computes one
finite complete mean, and logs the Metric object once for stock callbacks. This is the exact
fit/HPO selection objective: Issue 21 showed that averaging batch means changes with the full/tail
partition.

Keep only three numerical boundaries: finite scalar training loss before backward; one native
`clip_grad_norm_(error_if_nonfinite=True)` at Lightning's automatic clipping point; and exact
complete-validation count plus one finite final mean. Add no batch-local validation checks,
component reducer, gradient rescan, parameter scan, or post-fit duplicate validation.

The disposable corrected probe runs seed `2026`, all three approved families, one actual update,
validation batches `[2, 1]`, strict-lower patience, a two-epoch broad-last continuation, direct best
rename, and native strict CPU loading:

```bash
uv run python docs/research/issue-26/single_artifact_prototype.py
```

The earlier `prototype.py`, `direct_candidate.py`, and `lightning_candidate.py` remain historical
comparison evidence only. Their custom payload inspection, repeat-hash, broad-best, and plain-state
mechanics are rejected, non-normative observations—not the corrected artifact contract.

Tune candidate fits use the same private Lightning implementation and return only complete Method,
finite best `total_loss`, one-based earliest best epoch, and completed epochs. They publish no
weights or artifact and add no per-epoch report/prune hook.

The real route is Edo's university NVIDIA L40 with native-TF32-enabled FP32. Device and precision
remain runtime host facts, not artifact or study identity. The local CPU run is lifecycle evidence,
not L40/CUDA evidence. Issue 76 must gate synthetic full/tail behavior for all three families after
integration; any unsupported operation, determinism failure, nonfinite behavior, or unacceptable
evidence stops without a silent device, precision, or host fallback.

The complete approved interface and lifecycle are in
[`decision-contract.md`](decision-contract.md). Primary-source checkpoint, loading, reducer, and
comparison evidence is consolidated in
[`lightning-native-checkpoint-artifact-audit.md`](lightning-native-checkpoint-artifact-audit.md).
This approval authorizes only Issue-26 research publication, Resolution/closure, and one map
pointer. Production implementation remains gated by the map's full-code-first order.
