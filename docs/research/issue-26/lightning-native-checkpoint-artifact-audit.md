# Lightning-native checkpoint, artifact, and reducer audit

Date: 2026-07-14. Status: primary-source evidence for the owner-approved Issue 26 contract.
No production, dependency, configuration, test, GitHub, corpus, model-quality, or scientific state
changed. The locked environment resolves Lightning 2.6.5, TorchMetrics 1.9.0, and PyTorch 2.11.0.
Closed Issue 78's single-operator, direct-rename, native-package-trust contract is binding.

## Finding

The lean coherent design is one Lightning host and one native canonical artifact:

```text
artifacts/.<artifact_id>/best-<epoch>.ckpt  --Issue 15 rename-->
artifacts/<artifact_id>.ckpt

artifacts/.<artifact_id>/last.ckpt         remains private continuation work
```

The selected best is already a weights-only Lightning checkpoint. Put one strict JSON-safe domain
record in Lightning's supported hyperparameter seam before fit, let stock `ModelCheckpoint` write
and select the best, and rename that file unchanged after success. `load_artifact` delegates to
`LightningModule.load_from_checkpoint(..., map_location="cpu", weights_only=True, strict=True)`.

This removes the prior plain-state projection, separate final save, custom checkpoint parser,
state-key/shape/dtype inventory, post-fit validation pass, post-publication reload, sidecar, digest,
payload inventory, and byte-length accounting. Lightning owns checkpoint structure, writing,
loading, strict weight restoration, best selection, full-state resume, and loop mechanics. SPICE
validates only domain facts Lightning cannot know: the exact TrainRequest association, fitted
feature/target/classification-loss states, and approved model/task mathematics.

Use one supplied storage root. `artifacts/.<artifact_id>/` is a literal owner-local hidden directory,
not a configured private root or lifecycle abstraction. Add no `.work` suffix, suffix parser,
work-kind model, cleanup API, or alternate path. The operator may manually remove the remaining
hidden last checkpoint after successful publication.

## Native weights-only artifact evidence

Lightning's checkpoint connector constructs both weights-only and broad checkpoints with native
epoch, global step, framework version, module state, and loop wrapper state. Saved module
hyperparameters and the module checkpoint hook are added outside the broad-only branch. Broad mode
additionally includes callbacks, optimizer states, schedulers, and precision state
([Lightning 2.6.5 source](https://github.com/Lightning-AI/pytorch-lightning/blob/2.6.5/src/lightning/pytorch/trainer/connectors/checkpoint_connector.py#L415-L510)).

Therefore the fit module can accept a plain domain record, validate it in `__init__`, build the
concrete family, and persist it with:

```python
self.save_hyperparameters(
    {"artifact": record.model_dump(mode="json")},
    logger=False,
)
```

The record must use weights-only-safe primitives. It is complete before training because the
artifact UUID is pre-minted and feature, target, and classification-loss fitting precedes the model
fit. Do not defer record construction until after stopping; that would force another checkpoint
write and duplicate native behavior.

`LightningModule.load_from_checkpoint` loads the checkpoint, reconstructs constructor arguments
from `hyper_parameters`, instantiates the module, calls its load hook, and calls native
`load_state_dict` with strict loading. Strict defaults to true unless explicitly changed
([loading source](https://github.com/Lightning-AI/pytorch-lightning/blob/2.6.5/src/lightning/pytorch/core/saving.py#L53-L189),
[public API](https://github.com/Lightning-AI/pytorch-lightning/blob/2.6.5/src/lightning/pytorch/core/module.py#L1701-L1805)).
The final load seam is consequently:

```python
module = FitModule.load_from_checkpoint(
    canonical_path,
    map_location="cpu",
    weights_only=True,
    strict=True,
)
module.eval()
```

`load_artifact` may return the already validated record and concrete `module.model`; it does not
call `torch.load`, inspect the native wrapper, strip `model.` prefixes, or duplicate Lightning's
strict restoration. A private resume hook may compare only the saved domain record with the current
request/preparation/Method association. It must not validate framework-owned state.

The weights-only file still carries inert Lightning wrapper bytes. Accepting epoch, step, loop
state, version, and hyperparameters is smaller than defining a SPICE artifact format. They do not
become scientific identity, runtime configuration, fit history, or an Evaluate placement claim.

## Best, continuation, and rename evidence

Stock monitored `ModelCheckpoint(save_top_k=1, save_weights_only=True)` owns the strict lowest
checkpoint and exposes its selected path as `best_model_path`. Checkpoint writing delegates to
`Trainer.save_checkpoint`
([public callback](https://lightning.ai/docs/pytorch/stable/api/lightning.pytorch.callbacks.ModelCheckpoint.html),
[2.6.5 source](https://github.com/Lightning-AI/pytorch-lightning/blob/2.6.5/src/lightning/pytorch/callbacks/model_checkpoint.py#L50-L56),
[save path](https://github.com/Lightning-AI/pytorch-lightning/blob/2.6.5/src/lightning/pytorch/callbacks/model_checkpoint.py#L593-L600)).
The canonical artifact should be that selected file, not a reconstruction of it.

A separate unmonitored broad `last.ckpt` is still necessary. The monitored best can be older than
the latest completed validation and lacks optimizer/callback continuation state. Full checkpoints
carry the state that `Trainer.fit(ckpt_path=...)` restores natively
([checkpoint restoration](https://github.com/Lightning-AI/pytorch-lightning/blob/2.6.5/src/lightning/pytorch/trainer/connectors/checkpoint_connector.py#L233-L404)).
Use `weights_only=True` on the load call to request restricted PyTorch deserialization; it does not
turn an already broad checkpoint into model-only continuation.

Keep the callback `dirpath` identical across jobs. Lightning intentionally restores only limited
ModelCheckpoint state when the directory changes
([source](https://github.com/Lightning-AI/pytorch-lightning/blob/2.6.5/src/lightning/pytorch/callbacks/model_checkpoint.py#L556-L572)).
Use the monitored callback object's `best_model_path`; do not use symbolic `ckpt_path="best"` with
two checkpoint callbacks because Lightning chooses the first applicable callback
([source](https://github.com/Lightning-AI/pytorch-lightning/blob/2.6.5/src/lightning/pytorch/trainer/connectors/checkpoint_connector.py#L158-L179)).

After Trainer finishes successfully, Train requires the canonical destination to be absent and
calls the selected best path's ordinary `rename` into `artifacts/<artifact_id>.ckpt`. Checkpoint
loading accepts an arbitrary exact path, so this name change has no Lightning semantic effect. Do
not add a publication helper, reopen, rewrite, validate, inventory, or reload the file. Interruption
keeps the hidden files; an existing destination or ambiguous rename stops for manual inspection.

The accepted integrity boundary is deliberate. No project SHA-256, payload inventory, byte length,
tensor ABI inventory, or same-ID equality engine is added. Native loading will reject many malformed
files and key mismatches, but a structurally loadable same-shape weight corruption or substitution
can pass. The thesis accepts that risk under its owner-controlled filesystem/rsync route.

## TorchMetrics MeanMetric evidence

The fit/HPO selection objective is the exact mean of all task-owned per-origin total losses. Issue
21 found that an unweighted mean of batch means changes when the final tail partition changes. One
float64 additive `MeanMetric` expresses the required complete-map reducer directly:

```python
self.validation_objective = MeanMetric(
    nan_strategy="disable",
    sync_on_compute=False,
).set_dtype(torch.float64)

# validation_step
self.validation_objective.update(per_origin_total.detach().to(torch.float64))
```

TorchMetrics 1.9.0 `MeanMetric` owns a sum and weight and computes `mean_value / weight`
([implementation](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/aggregation.py#L512-L570)).
The base Metric's `set_dtype` converts its states and future updates retain that dtype
([dtype source](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/metric.py#L826-L907)).
Each input is therefore upcast before accumulation, and the metric's float64 unit weight is the one
exact sample counter for this bounded dataset.

At validation end:

1. require `validation_objective.weight` to equal the frozen validation cardinality;
2. call `compute()` once;
3. require that one complete scalar to be finite;
4. log the Metric object once as `validation_total_loss`, with `on_step=False`, `on_epoch=True`,
   `logger=False`, and `sync_dist=False`.

`nan_strategy="disable"` is intentional. It lets nonfinite per-origin contributions propagate to
the single complete-objective gate. The locked branch replaces any supplied weights with ones when
checking is disabled, so never feed batch means or explicit batch weights
([source](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/aggregation.py#L75-L107)).

Logging a Metric object lets Lightning expose the computed epoch value to callbacks and reset the
metric automatically
([official integration](https://lightning.ai/docs/torchmetrics/stable/pages/lightning.html)).
The earlier explicit `compute()` is cached, so callback delivery observes that same scalar
([compute wrapper](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/metric.py#L676-L710)).
Metric states are nonpersistent by default and do not become model checkpoint state
([state contract](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/metric.py#L201-L285)).

This route is intentionally single-device. `sync_on_compute=False` and `sync_dist=False` express
the one-process L40 owner. A distributed host would require a new count/reduction contract.

## Numerical ownership

Keep exactly three distinct failure boundaries:

1. require the scalar training loss to be finite before backward;
2. at Lightning's automatic clipping point call PyTorch
   `clip_grad_norm_(..., error_if_nonfinite=True)` once;
3. require the complete MeanMetric sample count and one finite final validation mean.

Finite task values can overflow while composing a scalar loss, so the first gate is meaningful.
Finite loss does not guarantee finite derivatives, so the native gradient-norm gate is distinct.
The last gate owns the whole validation objective; a per-batch check would be duplicate machinery.
PyTorch documents `error_if_nonfinite` as part of the clipping operation
([operation](https://docs.pytorch.org/docs/stable/generated/torch.nn.utils.clip_grad_norm_.html)).

Set `EarlyStopping(check_finite=False)`. The completed-objective owner already fails on a nonfinite
mean; Lightning's option would add a second stop decision instead of the required failure. Add no
component reducer, parameter scan, per-gradient check, post-step check, post-clip check, callback
check, best-checkpoint revalidation, or publication-time validation.

## Bounded evidence and comparison

Locked CPU synthetic probes established lifecycle semantics only:

- full/tail contributions `[1, 2, 3]` and `[10]` produced float64 sum `16`, weight `4`, and mean
  `4`; the incorrect unweighted mean of batch means is `6`;
- the logged Metric reached callback metrics once and reset after the validation epoch;
- `nan_strategy="disable"` preserved NaN/Inf until the final gate;
- saved plain constructor facts survived a weights-only best checkpoint;
- `FitModule.load_from_checkpoint(..., weights_only=True)` reconstructed the module and strictly
  loaded its weights after the file was renamed;
- a separate broad last checkpoint resumed model, optimizer, loop, and callback state;
- all three frozen families exercised full and tail batches.

These runs are not CUDA, L40, TF32, determinism, performance, memory, or scientific evidence.
Issue 76 must separately gate all three families on the actual university NVIDIA L40. Failure
there must return to Edo without a silent device, precision, or host fallback.

Equally simplified direct PyTorch remains attractive for reading the inner loop, but it must own
zero/backward/step, clipping timing, strict stopping, best selection, broad continuation state,
serialization, restoration, and canonical loading. Lightning now removes more total project
behavior than it introduces. The choice is therefore substantive lifecycle delegation, not a
claim that every Lightning code fragment has fewer lines.

Rejected designs are a plain state dict plus sidecar, a second final checkpoint save, a custom
`CheckpointIO`, a custom artifact parser, a framework-neutral host adapter, parallel hosts, and a
post-publication reload ritual. None has a consumer that justifies its extra seam.
