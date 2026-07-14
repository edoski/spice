# Issue 26 training-host decision contract

Status: owner-approved final contract, 2026-07-14. Planning/prototype only. The earlier direct
PyTorch, projected plain-weight, custom-parser, and post-fit-resave recommendations are withdrawn.
Closed Issue 78's single-operator, direct-rename, native-package-trust contract is binding.

## Decision and seam

Choose Lightning 2.6.5 automatic optimization as the sole Train/Tune fit host. Direct PyTorch is
not materially leaner across the complete lifecycle after Lightning also owns best selection,
continuation, strict restoration, and the canonical checkpoint. Its remaining advantages are local
loop transparency and one fewer dependency, not lower total project machinery.

Keep one concrete private fit implementation behind the two operations that actually exist:

```python
def train(
    request: TrainRequest,
    prepared: PreparedTraining,
    storage_root: Path,
    runtime: TrainRuntime,
) -> TrainSuccess: ...

def _run_candidate(
    request: TuneRequest,
    candidate: Method,
    prepared: PreparedTraining,
    candidate_scratch: Path,
    runtime: TrainRuntime,
) -> CandidateSuccess: ...
```

Both call one private `_fit(...) -> _FitOutcome` implemented directly with one
`LightningModule`, one `Trainer`, and stock callbacks. `_FitOutcome` is module-private and carries
only the selected `best_model_path`, finite best total loss, earliest best epoch, completed epochs,
and stop reason. No `Trainer`, module, callback, optimizer, state dict, or checkpoint parser crosses
the module boundary.

`train` publishes the selected checkpoint. `_run_candidate` projects only the successful HPO facts
and publishes no model. This replaces the earlier nullable artifact mode and the false claim that
Train and HPO should expose an identical public fit result. There is no framework-neutral adapter,
parallel host, host selector, migration shim, or provisional implementation.

`TrainRuntime` contains only ephemeral device and DataLoader arguments. It contains no storage,
private-work, precision, model, study, or artifact field. Device and precision are runtime host
facts, never Method, study, checkpoint, request, or artifact identity. Evaluate placement is
outside Issue 26.

## Storage and native artifact

Train derives exactly two paths from its one supplied storage root:

```text
artifacts/.<artifact_id>/       Lightning fit scratch
artifacts/<artifact_id>.ckpt   canonical selected checkpoint
```

The leading dot is the whole private-work convention. The hidden directory is disposable owner
scratch, not security state, a configured root, a lifecycle, or a domain object. Add no `.work`
suffix, suffix parser, work-kind enum, status, cleanup API, or global scratch configuration. Keep
the same hidden directory across resume so Lightning can restore callback state against the same
`dirpath`. After verified success the operator may remove the remaining hidden directory manually.

Issue 29 supplies its own study-local candidate scratch. Issue 26 accepts that exact path; it does
not create a second storage convention. Evaluate needs only its separately owned hidden temporary
file and no fit work directory.

The fit-module constructor accepts one JSON-safe strict domain record. For Train it contains only
facts Lightning cannot know:

- the exact pre-minted-ID `TrainRequest` association;
- the fitted feature, target, and classification-loss states;
- the effective approved model/task definition and thesis-specific loss mathematics needed to
  reconstruct the selected concrete family.

Do not store device, precision, paths, validation history, optimizer facts, checkpoint inventory,
tensor keys/shapes/dtypes, SHA-256, byte lengths, payload inventory, corruption evidence, or a
sidecar. Do not duplicate fields derivable from the exact request and fitted states.

The constructor strictly hydrates that domain record, exhaustively constructs the selected family,
and calls `save_hyperparameters({"artifact": record.model_dump(mode="json")}, logger=False)`.
Lightning therefore writes only plain record values inside both weights-only and broad native
checkpoints and can replay the constructor when loading.
The record is complete before fitting because the artifact UUID and fitted preparation/loss states
already exist. No post-fit record injection or checkpoint rewrite is needed.

The final file is the stock monitored weights-only best checkpoint, unchanged. Its native
`epoch`, `global_step`, loop wrapper, Lightning version, hyperparameters, and state dict are
acceptable framework bytes. SPICE defines no envelope schema and does not inspect them.

## Frozen lifecycle

Before any stochastic construction, validate the request, prepared role datasets, fitted states,
method, runtime, and exact hidden path. The module hook validates any existing private continuation
association during Lightning's native restore, before training continues. Hard-require the
process-visible university NVIDIA L40 route, subject to Issue 76. Set
`CUBLAS_WORKSPACE_CONFIG=:4096:8`, deterministic algorithms, cuDNN deterministic/no benchmark,
float32 matmul precision `high`, and CUDA-matmul/cuDNN TF32 enabled. Then call
`pl.seed_everything(2026, workers=True)` and seed the dedicated CPU training-loader generator before
constructing the model, optimizer, DataLoaders, or any other stochastic object.

Exhaustively match the three approved families: LSTM, Transformer, and Transformer-LSTM. Construct
the concrete model in the LightningModule and AdamW in `configure_optimizers`. Add no registry,
family adapter, generic model protocol, or alternate builder path.

Construct ordinary map-style training and validation DataLoaders with default collation and
`drop_last=False`. Training alone shuffles with the dedicated generator; validation is sequential.
The task transfer seam moves only `inputs`, `label`, and `target`; origin/provenance values remain on
CPU. Preserve the completed representation/DataLoader contract. Add no DataModule, custom sampler,
collator, batch object, or generic device-transfer layer.

Configure one stock `Trainer` with one GPU, `precision="32-true"`, `max_epochs=36`,
`accumulate_grad_batches=1`, gradient norm clipping `1.0`, `deterministic=True`, zero sanity
validation steps, `logger=False`, and no framework progress/model-summary noise beyond an approved
operator-edge line. Add no autocast, scaler, scheduler, compile, distributed, or multi-device
branch.

Lightning owns automatic zeroing, backward, clipping dispatch, optimizer step, epoch and loop
mechanics, the epoch cap, callbacks, checkpoint writing/loading, best selection, and resume. The
single clipping hook exists only because Lightning 2.6.5 does not expose PyTorch's required
nonfinite flag: at Lightning's automatic clipping point it calls
`clip_grad_norm_(..., max_norm=1.0, error_if_nonfinite=True)` once. It adds no gradient scan or
second norm decision.

Unsupported hardware or operations, failed determinism, OOM, nonfinite behavior, or unacceptable
evidence fails the fit. There is no silent strict-FP32, mixed-precision, CPU, other-GPU, or direct
host fallback.

## Objective and numerical boundaries

The task owns loss mathematics. For training it returns one differentiable scalar batch-mean total
loss. For validation it returns one detached per-origin total-loss vector of shape `[B]`; the host
never reads classification or regression components.

Use one TorchMetrics 1.9.0 accumulator:

```python
MeanMetric(nan_strategy="disable", sync_on_compute=False).set_dtype(torch.float64)
```

Each validation step upcasts the task-owned `[B]` vector and updates that metric without supplied
weights. At the completed validation boundary, require `metric.weight` to equal the exact frozen
validation cardinality, call `compute()` once, require that scalar to be finite once, and log the
Metric object once as `validation_total_loss` with `on_step=False`, `on_epoch=True`,
`logger=False`, and `sync_dist=False`. Lightning exposes it to callbacks and resets the metric.

This is one float64 additive objective accumulator, not defensive machinery. Issue 21 established
that averaging batch means makes selection depend on the full/tail partition. Per-origin updates
produce the exact complete-map mean and the metric's unit weight is the sole sample counter.

Keep exactly three distinct numerical boundaries:

1. reject a nonfinite scalar training loss before backward;
2. let the one native `clip_grad_norm_(error_if_nonfinite=True)` fail on a nonfinite global gradient
   norm while clipping;
3. require the exact complete-validation sample count and one finite final MeanMetric result.

The first is needed because finite task inputs/outputs can still overflow in composition. The
second is needed because a finite loss does not imply finite derivatives. The third owns the
selection/HPO objective across the complete validation map. Add no per-validation-batch finite
check, component check, parameter scan, post-step scan, post-clip check, callback finite check, or
post-fit duplicate validation.

## Stopping, best, and continuation

Instantiate stock `EarlyStopping` on `validation_total_loss` with `mode="min"`,
`min_delta=0.0`, patience `8`, `strict=True`, `check_finite=False`, and validation-end checking.
The first completed value is best; only strict decrease improves; equality keeps the earliest best.
Eight consecutive non-improving completed validations stop the fit. Reaching 36 completed epochs
is successful.

Instantiate stock monitored `ModelCheckpoint` with the same monitor/mode, `save_top_k=1`,
`save_weights_only=True`, and validation-end cadence. It alone owns strict best selection. Use a
controlled best filename containing Lightning's epoch token so the private HPO projection can
recover the required one-based earliest-best epoch from `best_model_path`; add no general filename
or suffix abstraction. Best is weights-only because its only downstream role is the inference
artifact: module state plus saved constructor facts are sufficient. Broad continuation state has
one owner, the separate last checkpoint.

Instantiate a second stock unmonitored `ModelCheckpoint` at the same hidden `dirpath`, with a fixed
`last.ckpt`, `save_top_k=1`, `save_weights_only=False`, validation-end cadence, and versioning
disabled. It overwrites only after a completed validation. Do not use monitored `save_last=True`:
the locked probe showed it need not advance when a new value does not enter top-k.

The broad last checkpoint is private continuation state. Lightning may store optimizer, callback,
scheduler, precision, loop, epoch, step, version, and model state. Resume passes that exact path to
`Trainer.fit(ckpt_path=last, weights_only=True)`. Lightning owns deserialization and restoration.
A narrow module hook may compare only the saved strict domain record with the current request,
fitted states, and Method before continuation; it must not parse framework state or validate
weights. Missing last starts fresh. A mismatched association fails.

Continuation starts at the latest completed-validation boundary. A partial epoch is discarded,
ordinary DataLoaders are reconstructed and reseeded, and no uninterrupted ordering, RNG, bitwise,
or cross-device equivalence is claimed. Keep the hidden `dirpath` stable; add no resume format,
repair, retry, force, alternate path, or framework-neutral checkpoint layer.

## Publication and loading

After successful Trainer completion, consume the monitored callback's exact `best_model_path`.
Do not restore it into the live module, run `Trainer.validate`, extract a state dict, move tensors,
resave, parse, inventory, or compare it. Train requires `artifacts/<artifact_id>.ckpt` to be absent,
then calls `best_model_path.rename(canonical_path)` directly. It does not reopen or reload the
canonical file. Interruption before rename leaves hidden best/last work; rename failure stops for
manual inspection. Add no publication helper, kernel, lock, receipt, or recovery layer.

`load_artifact` is a thin domain facade over Lightning:

```python
module = FitModule.load_from_checkpoint(
    artifact_path(storage_root, artifact_id),
    map_location="cpu",
    weights_only=True,
    strict=True,
)
module.eval()
return LoadedArtifact(record=module.artifact, model=module.model)
```

The constructor validates only the strict domain record and its requested artifact association.
Lightning parses the checkpoint, reconstructs the module, and strictly restores weights. SPICE
does not call `torch.load` directly, inspect wrapper keys, strip prefixes, inventory state keys,
check tensor shapes/dtypes, implement corruption checks, or duplicate strict loading. It exposes
neither the training wrapper nor Lightning parsing to Evaluate.

An existing canonical destination is not compared, replaced, repaired, or treated as a byte/domain
no-op; stop for operator inspection. The accepted residual risk is explicit: a structurally
loadable same-shape weight corruption or substitution may go undetected. The thesis relies on its
owned filesystem/rsync route, restricted native load, strict domain association, and Lightning's
strict restoration, not a project integrity format.

## Private HPO result

`_run_candidate` uses the same module, host, task objective, three failure boundaries, stopping,
best selection, and native last-checkpoint continuation. Its private resume record binds the exact
TuneRequest and complete candidate Method. On success it returns exactly the binding Issue 29
facts: complete Method, finite best `total_loss`, one-based earliest best epoch, and completed
epochs. These project stock callback/Trainer outputs; they do not reimplement selection.

HPO publishes no artifact, weights, checkpoint, epoch history, logger output, pruning/report hook,
test score, failure record, or candidate identity. Failure/interruption yields no successful
candidate result. Its private best/last files remain only study-local continuation work.

## Evidence and implementation order

The bounded local prototype may use only the frozen synthetic full/tail task. It must cover all
three families, seed-before-construction, an actual update, the float64 MeanMetric objective, strict
36/8 behavior, the three failure gates, weights-only best, broad last resume, direct best rename,
and native strict CPU loading. It adds no custom-parser, tensor-inventory, corruption, callback
ordering, framework-internal, logger, compatibility, migration, or transition tests. It uses no
real corpus and produces no scientific result.

The local CPU strict-FP32 probe is lifecycle evidence only. After integration, Issue 76 must run
synthetic full and tail batches for all three families on Edo's university NVIDIA L40. It owns
native-TF32 FP32 capability, operation coverage, determinism, finite behavior, real update,
checkpoint CPU loading, strict-FP32 deltas, timing, and memory. Any unsupported operation, failed
determinism, nonfinite behavior, or unacceptable evidence stops and returns to Edo with no host or
precision fallback.

This decision changes no production, configuration, test, dependency, corpus, storage, acquisition,
evaluation, Slurm, archive, sibling issue, map, or GitHub state. Preserve the binding full-code-first
order: owner approves one complete specification; only then are review-sized implementation tickets
created; implementation and independent review follow; integration precedes the separate Issue 76
hardware gate. No phase is skipped.
