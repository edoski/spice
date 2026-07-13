# Clean-break framework semantics: modeling and tuning

Date: 2026-07-10

Scope: candidate phases 3–4, plus conversion constraints they create. This note separates observed repository behavior, verified framework behavior, and recommendations. It does not treat existing ADRs as binding approval for the new route.

## Bottom line

The fixed-context, automatic-Lightning, Journal Optuna, TorchMetrics, and NumPy-scaler direction is viable. Four candidate claims need correction before implementation:

1. Stock Lightning `ModelCheckpoint` is not finite-gated. A first nonfinite monitored value can still write both `best.ckpt` and `last.ckpt`.
2. Native Lightning resume restores model, optimizer, callback, loop, epoch, and step state, but not a newly constructed `DataLoader` generator's advanced shuffle state.
3. `ModelCheckpoint` tracks the raw optimum; `EarlyStopping(min_delta=...)` tracks qualified improvement. This differs from SPICE's current min-delta-qualified best state.
4. A sample-count-weighted reducer does not produce the full-split weighted cross-entropy when class weights are active. The candidate preserves the current batch-partition-dependent reporting semantics unless this is deliberately changed.

Two dependencies must become direct dependencies when their APIs are imported: `torchmetrics>=1.9,<2` and `optuna-integration>=4.8,<5`.

## Lightning fit, checkpoints, and resume

### Repository evidence

- `src/spice/modeling/pipeline.py:228-271` prepares the dataset and constructs the model before entering `run_training_fit`.
- `src/spice/modeling/runtime_planning.py:73-82` seeds inside runtime planning; `_runtime.py:60-63` manually seeds Python, NumPy, and Torch. Model initialization therefore happens before the configured seed.
- `src/spice/modeling/lightning_module.py:28-104` uses one AdamW optimizer but manually performs zero-grad, backward, clipping, and step.
- `src/spice/modeling/_fit_policy.py:199-210` promotes a best state only when `current < best - min_delta`.
- `src/spice/modeling/training_runner.py:76-117` manually loads model/policy/optimizer state, converts total epochs to remaining epochs, disables Lightning checkpointing, and restores an in-memory CPU best state.
- `src/spice/modeling/persisted_training.py:93-145` already recomputes final validation and test metrics and rejects nonfinite maps. `results.py:143-151,230-248` persists only validation/test total losses, not complete maps.

### Verified framework behavior

Lightning recommends automatic optimization for ordinary single-optimizer training and owns zero-grad, backward, step, accumulation, and Trainer-configured clipping in that mode ([Lightning optimization](https://lightning.ai/docs/pytorch/stable/common/optimization.html)). `seed_everything(seed, workers=True)` seeds Python, NumPy, and Torch and configures Trainer worker initialization ([Lightning seed source](https://lightning.ai/docs/fabric/stable/_modules/lightning/fabric/utilities/seed.html)). It must run before dataset preparation and model construction.

A full Lightning checkpoint contains epoch, global step, module state, optimizer state, callback state, and loop state. `trainer.fit(..., ckpt_path=...)` is the supported resume path ([Lightning checkpoint contents and resume](https://lightning.ai/docs/pytorch/stable/common/checkpointing_basic.html)). Multiple `ModelCheckpoint` callbacks are supported, `save_weights_only` controls optimizer/loop inclusion, and changing `dirpath` on resume prevents most callback state from being restored ([ModelCheckpoint](https://lightning.ai/docs/pytorch/stable/api/lightning.pytorch.callbacks.ModelCheckpoint.html)). The hidden stage path must therefore remain stable across retries.

`EarlyStopping(check_finite=True)` stops only when its monitored metric is nonfinite. Its `patience` counts validation checks, and `min_delta` controls qualified improvement ([EarlyStopping source](https://lightning.ai/docs/pytorch/stable/_modules/lightning/pytorch/callbacks/early_stopping.html)). It does not replace SPICE's current all-training/all-validation-metric finite policy.

`ModelCheckpoint` has no finite-check argument. In Lightning 2.6.5, `check_monitor_top_k` returns true while fewer than `k` files exist, before checking the value; its later NaN handling replaces the score with infinity but still writes the file ([tagged 2.6.5 source](https://github.com/Lightning-AI/pytorch-lightning/blob/2.6.5/src/lightning/pytorch/callbacks/model_checkpoint.py#L700-L727)). Thus “two stock finite-gated callbacks” is not an available framework contract.

Local diagnostics used the locked environment: Lightning 2.6.5, Torch 2.11.0, TorchMetrics 1.9.0. A one-epoch validation-NaN run produced `trainer.should_stop == True` while still writing both a weights-only `best.ckpt` and a full `last.ckpt`; the stored best score was `inf`. This matches the tagged source.

Native resume was also exercised on CPU. Training epochs 0–1, saving a full checkpoint, then resuming with total `max_epochs=4` correctly started at epoch 2 and restored `global_step`. Reconstructing a standard shuffled `DataLoader` with a generator seeded to the original seed repeated the exact epoch-0 and epoch-1 permutations at epochs 2 and 3. PyTorch documents that this generator drives `RandomSampler` and worker base seeds, but it is an external DataLoader object ([DataLoader](https://docs.pytorch.org/docs/2.13/data.html)).

### Recommendation

- Seed once at the workflow boundary with `pl.seed_everything(seed, workers=True)` before preparation and model construction. Delete the later duplicate seed helper.
- Use automatic optimization, return the loss from `training_step`, keep `configure_optimizers`, and configure norm clipping on `Trainer`.
- Keep a complete-map finite check in the scorer/epoch boundary. Native EarlyStopping alone is weaker.
- Use a minimal finite-gating callback or fail before checkpoint callbacks run. Do not describe the result as two stock finite-gated callbacks.
- Use a weights-only best checkpoint and full latest-finite checkpoint at stable hidden-stage paths. Resume with total `max_epochs` and `ckpt_path=last.ckpt`.
- Define the artifact weight ABI as the exact `model.` subset of `checkpoint["state_dict"]`. Require an exact expected key set and strict load. A weights-only Lightning checkpoint still contains wrapper-prefixed state plus epoch/step metadata.
- For checkpoint-free tuning, use a tiny in-memory validation tracker. Lightning exposes best score/path on `ModelCheckpoint`, but EarlyStopping does not expose the epoch of its best score.
- Store externally visible epochs as one-based. Convert Lightning's zero-based `current_epoch` and checkpoint `epoch` once at the boundary.

### Human approval gates

Best-state semantics must be chosen explicitly:

- Recommended idiomatic contract: `best.ckpt` is the raw finite minimum; `min_delta` affects stopping only.
- Behavior-preserving alternative: best state is min-delta-qualified. This needs custom tracking/checkpoint glue and is not a stock ModelCheckpoint contract.

Nonfinite behavior must also be chosen: fail immediately on any nonfinite train/validation metric, or stop and retain the previous finite best when one exists. The current implementation does the latter after a best and fails before the first best.

Finally, approve either state-correct/non-bitwise resume with restarted shuffle permutations, or persist the dedicated generator state through a stateful DataModule/checkpoint hook. Native `ckpt_path` alone does not provide uninterrupted ordering.

## Optuna Journal, pruning, and study snapshots

### Repository evidence

- `src/spice/storage/study_optuna.py:31-35` uses SQLAlchemy-backed `RDBStorage`.
- Fresh studies explicitly receive seeded TPE and Median/Nop pruning at `study_optuna.py:71-85`; resumed studies at lines 91 and 68 omit both.
- `src/spice/modeling/tuning_execution.py:73-112` counts every trial, including `RUNNING`, toward the requested total.
- `tuning_execution.py:165-178` applies an application timeout.
- `tuning_execution.py:201-228` creates a trial training summary including test evaluation, then reports once at the final best epoch. This cannot prune training early.

### Verified framework behavior

Journal storage appends every operation and rebuilds in-memory state by replaying the log ([JournalStorage](https://optuna.readthedocs.io/en/latest/reference/generated/optuna.storages.JournalStorage.html)). The file backend supplies append-level locking and NFS-oriented lock options but does not support high write concurrency ([JournalFileBackend 4.8](https://optuna.readthedocs.io/en/v4.8.0/reference/generated/optuna.storages.journal.JournalFileBackend.html)). A SPICE one-writer policy is reasonable, but it is application policy and needs a lock spanning the whole optimize/recovery operation.

`optuna.load_study(..., sampler=None, pruner=None)` constructs TPE and MedianPruner defaults ([load_study](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.study.load_study.html)). Resumed no-pruning studies must therefore pass `NopPruner` explicitly. A fresh seeded TPE is reproducible; a new TPE with the same seed on resume restarts its RNG. Unseeded resumed TPE is a reasonable non-bitwise policy, not a proof that duplicates are impossible. Optuna notes that failed trials are ignored by built-in samplers ([TPESampler](https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.TPESampler.html)).

Optuna documents that SIGTERM or parallel interruption can leave a trial state not properly updated. Public `Study.tell(..., state=FAIL)` can close it ([Study](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.study.Study.html)). Recovery is safe only while the application holds the exclusive writer lock; otherwise it can fail a live trial.

The official Lightning pruning callback lives in the separate `optuna-integration` distribution and reports at validation end ([PyTorchLightningPruningCallback 4.8](https://optuna-integration.readthedocs.io/en/v4.8.0/reference/generated/optuna_integration.PyTorchLightningPruningCallback.html)). Single-device training avoids its DDP/RDB restrictions. With `NopPruner`, the callback still reports intermediate values and never prunes.

### Recommendation

- Persist the exact immutable study definition in one namespaced, JSON-serializable `study.user_attrs` value. Exclude invocation controls such as requested total and timeout.
- Always construct sampler and pruner explicitly on both create and load: seeded TPE only on creation; unseeded TPE on explicit resume; Median or Nop from the stored definition.
- Under the exclusive writer lock, mark abandoned `RUNNING` trials `FAIL`, count terminal `COMPLETE`, `PRUNED`, and `FAIL` trials, and optimize only the remaining requested total. Do not count `WAITING` as terminal.
- Define the study-creation crash window. If the study exists without its definition attribute and has zero trials, setting the requested definition is recoverable; if any trial exists, fail as corrupt. Atomic temporary-journal promotion is the stricter alternative.
- Remove trial artifacts and test scoring. The objective returns validation best only; record the one-based best epoch as a trial user attribute.
- Add the official pruning callback for every trial. Nop remains explicit so intermediate values are still recorded.
- Hold a read lock across one coherent tuned-training snapshot: definition, chosen best trial, exact `best_trial.params`, terminal counts, and fully applied config. Do not read these through separate unlocked calls.

### Human approval gate

The requested trial budget must define whether failed, pruned, and recovered-abandoned attempts consume the total. Counting all terminal attempts is bounded and matches the candidate. Counting only completed trials retries interruptions but can exceed the requested work and needs a separate retry ceiling.

## Fixed contexts, DataLoader, and models

### Repository evidence

`src/spice/modeling/dataset_builders/fixed_sequence_temporal.py:121-155` rewrites every retained context start as `anchor - context_length + 1`. Training applies this at lines 244–322 and inference at lines 325–376. Variable context exists before fixed-context filtering and sequence calibration, not at the model boundary.

Despite that invariant, `representations/sequence_inputs.py:19-105,200-221` allocates zero padding, an input mask, per-batch lengths, and loop-filled slices. `batch_plan.py:39-179,237-338` groups by batch signature and owns a custom epoch sampler plus nested runtime/plan contracts. The simplification premise is therefore supported.

The candidate should go one step further on batch ownership. The action mask is materialized in both `SequenceInputBatch` (`sequence_inputs.py:19-54`) and `MinBlockFeeTargetBatch` (`prediction/families/min_block_fee_multitask/batch.py:38-65`). Training uses the target copy; inference decoding uses the input copy. A clean concrete design can store it once per batch rather than preserving this duplication.

PyTorch `DataLoader(shuffle=True)` reshuffles every epoch; its generator drives both `RandomSampler` and worker base seeds. It supports normal batch sizing, collation, pinning, persistence, and prefetch directly ([DataLoader](https://docs.pytorch.org/docs/2.13/data.html)). A custom batch must implement `pin_memory()` for pinning, and Lightning needs either standard tensor collections, an object implementing `.to(...)`, or a transfer hook ([Lightning data transfer](https://lightning.ai/docs/pytorch/stable/api/lightning.pytorch.core.hooks.DataHooks.html)).

For a unidirectional stacked LSTM, `h_n` contains the final state for each layer; `h_n[-1]` is the last layer's final state ([LSTM](https://docs.pytorch.org/docs/2.13/generated/torch.nn.LSTM.html)). Current SPICE LSTMs are unidirectional, so this replacement is valid after uniform full contexts are enforced. `TransformerEncoder` accepts an optional padding mask, so omitting an all-false mask is valid ([TransformerEncoder](https://docs.pytorch.org/docs/2.13/generated/torch.nn.TransformerEncoder.html)). Removing it can select different CUDA kernels, which is why the same-weight gate remains mandatory.

`families/_transformer_shared.py:14-28` hardcodes positional capacity 4096 and slices silently. The configured default maximum is also 4096, but a direct readable capacity check should guard the actual tensor length.

### Recommendation

- Assert uniform context length against the runtime sequence length before workers start.
- Keep fixed tensorization as a focused directly called module; delete the generic registry and persisted representation identity. Existing ADR 0003 is a prior decision to challenge, not evidence that the route must preserve it.
- Use `np.empty` only where every element is overwritten by an exact fixed-length contiguous slice. Assert the slice shape before assignment.
- Use standard `DataLoader(range(n), batch_size=..., shuffle=..., generator=..., collate_fn=...)` and retain worker/pin/persistence/prefetch values only where benchmark evidence supports them.
- Prefer separate shallow training and inference batch records: training need not carry sample positions after collation; inference must keep CPU sample positions for ordered writes. Own one action mask per record. This avoids moving inference positions to CUDA and removes the current duplicate mask.
- LSTM and Transformer-LSTM use `h_n[-1]`; Transformer uses `encoded[:, -1]`. Add the positional-capacity check before slicing.

The current ADR offers a credible alternative: retain a narrow representation function/interface but delete the registry and persistence identity. Keeping the full current seam is a third option. Human approval should select the seam before code is reshaped.

### CUDA equivalence gate

This workstation has no CUDA device, so the required gate remains external. Run old and new paths in eval mode on the same CUDA host, with identical loaded weights and fixed samples, for LSTM, Transformer-LSTM, and Transformer. Include a full and tail batch. Require:

- exact sample positions and action masks;
- every raw output head close via `torch.testing.assert_close(atol=1e-5, rtol=1e-4, equal_nan=False)` ([PyTorch testing](https://docs.pytorch.org/docs/2.13/testing.html));
- zero decoded-action mismatches;
- recorded GPU, CUDA, cuDNN, Torch, dtype, model config, sequence length, and sample hashes.

Use at least one representative real artifact per family if available, plus a deterministic fixture. Remove the temporary dual-path harness after retaining its evidence.

## TorchMetrics scorer semantics

### Repository evidence

`prediction/families/min_block_fee_multitask/metrics.py:15-105` implements classification counts manually. Its macro F1 skips every class with no target support, even when predictions activate that class. This is the old target-supported metric.

Lines 168–207 and 235–278 multiply scalar batch losses by sample count, sum them, and divide by total samples. `loss.py:24-28` uses class-weighted `F.cross_entropy` with its default mean reduction. That mean divides by the sum of target weights, not batch size. Multiplying it by batch size therefore yields a metric that depends on batch partition and class composition.

### Verified framework behavior

Use `MulticlassAccuracy(..., average="micro")`; micro reduction sums label statistics ([Accuracy](https://lightning.ai/docs/torchmetrics/stable/classification/accuracy.html)). Use `MulticlassF1Score(..., average="macro", zero_division=0)` for the candidate's union-active definition ([F1](https://lightning.ai/docs/torchmetrics/stable/classification/f1_score.html)). TorchMetrics 1.9 excludes only classes where `tp + fp + fn == 0` from macro averaging ([tagged reduction source](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/utilities/compute.py#L82-L93)). Predicted-only classes remain active with score zero.

Diagnostic: for targets `[0, 0]`, predictions `[0, 1]`, and any `num_classes >= 2`, per-class F1 starts `[2/3, 0, ...]` and stock macro F1 is `1/3`. This is the union-active average over classes 0 and 1. Current SPICE returns `2/3` because it excludes predicted-only class 1. An inactive third or fourth class does not change TorchMetrics' result.

TorchMetrics modular state belongs to one loader/phase; separate train, validation, and test instances are required. Lightning can reset logged Metric objects, while manual computation requires explicit reset ([TorchMetrics with Lightning](https://lightning.ai/docs/torchmetrics/stable/pages/lightning.html)). Metric dtype conversion must use `Metric.set_dtype(torch.float64)`; `.double()` is intentionally prevented ([Metric API](https://lightning.ai/docs/torchmetrics/stable/references/metric.html)). Apply it to MAE and MSE state.

### Recommendation

- Build one scorer factory/code path, but fresh state per phase and per standalone scoring call.
- Use micro accuracy, union-active macro F1 with zero division zero, and float64 MAE/MSE states.
- Implement loss aggregation as a small float64 TorchMetrics Metric or equivalent state object with explicit NaN propagation. Do not use `MeanMetric`, whose NaN policy is not the desired fail-closed contract.
- Compute and validate the complete metric map before checkpoint promotion, pruning observation, and summary serialization.
- Add `torchmetrics` directly to project dependencies.

### Human approval gate: loss formula

The candidate's sample-count reducer preserves current behavior but is not an exact full-split weighted CE. Choose one contract and name it:

- Behavior-preserving: average scalar batch losses by batch sample count. Results can change with batch partition.
- Recommended mathematical contract: expose reducible loss numerators and their true denominators. Weighted CE divides by summed target weights; sample-mean regression divides by sample count. Define how these components combine into total loss before using it for selection.

This decision needs an uneven-class, uneven-tail-batch fixture. It is separate from the macro-F1 audit.

## NumPy scaler

`temporal/input_normalization/scaling.py:11-70` is the sole production scikit-learn use. It fits over unique covered rows, not context multiplicity. The store already rejects nonfinite features at `problem_store.py:43-65`.

`StandardScaler` uses population standard deviation (`ddof=0`) and assigns scale 1 to constant columns ([StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)). NumPy documents the same population formula and supports explicit float64 accumulation ([NumPy std](https://numpy.org/doc/stable/reference/generated/numpy.std.html), [NumPy mean](https://numpy.org/doc/stable/reference/generated/numpy.mean.html)).

Local parity checks found identical means/scales on representative and extreme finite matrices; transformed values differed by at most `7.5e-8` before final float32 casting. The replacement is straightforward:

- `mean(..., axis=0, dtype=float64)`;
- `std(..., axis=0, dtype=float64, ddof=0)`;
- exact-zero scales become 1;
- strict model validation requires nonempty equal widths, finite means, and finite positive scales;
- transform validates feature width and finite float32 output.

Current `tests/temporal/test_input_normalization.py:58-65` expects zero and negative persisted scales to be silently replaced with 1. Clean-break strictness should intentionally replace that test with rejection. Remove the scikit-learn dependency after parity tests pass.

## Strict conversion consequences

Current `model.pt` is suitable for strict best-weight conversion: `training_runner.py:113-117` loads the selected best state into the returned model, and `persisted_training.py:169-174` persists that model. Conversion can wrap those exact tensors under the new checkpoint `state_dict` prefix and prove equality by key set, dtype, shape, and tensor hash.

Current training summaries cannot be copied into the new complete-map summary: `results.py:143-151` stores only best-validation and test total loss. A strict importer must reconstruct the accepted artifact and corpus, run the new shared scorer on validation and test, require all values finite, and label them as recomputed under the new metric semantics. It must not invent historical F1/accuracy/MAE/MSE values. If provenance, splits, weights, or scoring inputs cannot be proven, classify the root as static archive.

Define one final artifact loader contract for both native and imported `best.ckpt`: extract the exact expected `model.` key subset and strict-load the raw model. This avoids a permanent legacy branch even if converted checkpoints omit irrelevant optimizer/loop fields.

The candidate also says new IDs are UUID4 while preserving imported study/artifact IDs. Those statements are compatible only if UUID4 is a generation rule, not a universal validation rule. Validate IDs as one canonical safe opaque root segment, or explicitly remap/archive non-UUID legacy IDs. This is a persistence-level human decision.

## Ticket-ready investigations

### Define Lightning best-state and nonfinite semantics

Type: `wayfinder:grilling` (HITL)

Question: Should best mean the raw finite validation minimum or a min-delta-qualified improvement, and should any nonfinite train/validation metric fail immediately or stop while retaining a prior finite best? Fix the one-based external epoch convention and behavior before/after the first valid best.

Blockers: none.

### Choose interruption semantics for shuffled training

Type: `wayfinder:grilling` (HITL)

Question: Is replaying initial seeded shuffle permutations after native resume acceptable under “state-correct but non-bitwise,” or must SPICE checkpoint the dedicated DataLoader generator state to match uninterrupted sample ordering?

Blockers: none.

### Prototype the minimal Lightning checkpoint contract

Type: `wayfinder:prototype` (HITL)

Question: What is the smallest automatic-optimization LightningModule/callback design that enforces the approved complete-map finite policy, writes latest-finite full state and strict best weights, resumes from a stable hidden stage with total max epochs, and exposes best value/one-based epoch without restoring custom fit policy?

Blockers: **Define Lightning best-state and nonfinite semantics**, **Choose interruption semantics for shuffled training**, and the phase-2 staged-root lifecycle decision.

### Define Optuna terminal-budget and abandonment semantics

Type: `wayfinder:grilling` (HITL)

Question: Which trial states consume requested total work, when may an abandoned RUNNING trial be changed to FAIL, and what corruption rule applies to a journal containing a study/trials without the namespaced immutable definition?

Blockers: none.

### Prototype Journal lifecycle and coherent locking

Type: `wayfinder:prototype` (HITL)

Question: Does one application writer lock plus a tuned-training read lock produce correct create, crash recovery, resume, extension, best-trial freeze, and partial-definition behavior on the actual local and university filesystems?

Blockers: **Define Optuna terminal-budget and abandonment semantics** and the phase-2 file-lock contract.

### Validate per-epoch pruning without trial artifacts

Type: `wayfinder:prototype` (HITL)

Question: Can the official Optuna Lightning callback report every validation epoch, prune Median trials, record Nop intermediates, retain best value/epoch in memory, and return no test score, manifest, checkpoint, or artifact stage?

Blockers: **Prototype the minimal Lightning checkpoint contract**, **Prototype Journal lifecycle and coherent locking**, and **Define shared metric scorer semantics**.

### Choose fixed-sequence batch ownership

Type: `wayfinder:grilling` (HITL)

Question: Should the generic Representation seam be removed in favor of one directly called fixed tensorizer, narrowed to a function-level seam, or retained? Also choose a flat training/inference batch ownership that stores action masks once and keeps inference positions on CPU. Treat ADR 0003 as an alternative to reassess, not a veto.

Blockers: none.

### Prototype the standard fixed-context DataLoader contract

Type: `wayfinder:prototype` (HITL)

Question: Does a standard seeded DataLoader with fixed contiguous tensorization preserve rows, positions, action masks, full/tail batch behavior, worker/pin settings, and the approved resume-order semantics while deleting BatchPlan, signatures, padding, masks, and the custom sampler?

Blockers: **Choose fixed-sequence batch ownership** and **Choose interruption semantics for shuffled training**.

### Run the 648-window macro-F1 impact audit

Type: `wayfinder:task` (AFK)

Question: Produce the frozen per-window target-supported versus TorchMetrics union-active macro-F1 evidence with the candidate's row-count, hash, version, finiteness, and formula checks so the semantic change can be approved from measured impact.

Blockers: frozen historical inputs and the old-code export environment.

### Define shared metric scorer semantics

Type: `wayfinder:grilling` (HITL)

Question: Approve the exact metric IDs/formulas, phase isolation, finite behavior, and especially sample-weighted batch-loss versus true numerator/denominator aggregation for the one scorer used by Lightning, standalone final scoring, and conversion recomputation.

Blockers: **Run the 648-window macro-F1 impact audit**.

### Run the same-weight CUDA model gate

Type: `wayfinder:task` (AFK)

Question: Run and retain the specified same-weight old/new CUDA evidence for all three model families, including full/tail batches, raw heads, decoded actions, positions, masks, environment, and sample/artifact hashes.

Blockers: **Prototype the standard fixed-context DataLoader contract** and an available supported CUDA worker.

### Prototype strict best-checkpoint and summary conversion

Type: `wayfinder:prototype` (HITL)

Question: On representative accepted legacy roots, can conversion produce the single new `best.ckpt` state-dict ABI with identical tensor hashes and recompute complete finite validation/test maps without inventing unavailable history?

Blockers: **Define Lightning best-state and nonfinite semantics**, **Define shared metric scorer semantics**, the neutral old-state export, and the phase-2 artifact manifest contract.

## Fog and scope boundaries

Not yet specified until adjacent work resolves:

- exact hidden-stage and lock filenames, because phase 2 owns the storage layout;
- final Slurm worker/prefetch values, because they depend on retained benchmark evidence and target hardware;
- import coverage, because the neutral conversion inventory determines which roots have provable manifests, splits, and corpora.

Out of scope for this clean-break route unless the destination changes:

- DDP or multiwriter tuning; the candidate explicitly assumes one device and one writer;
- Transformer reinitialization. PyTorch warns cloned encoder layers start with identical parameters, but changing initialization is a model-quality redesign, not necessary simplification ([TransformerEncoder warning](https://docs.pytorch.org/docs/2.13/generated/torch.nn.TransformerEncoder.html));
- permanent dual readers, compatibility checkpoint formats, or a generic representation plugin system.
