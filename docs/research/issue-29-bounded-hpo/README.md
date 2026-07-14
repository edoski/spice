# Issue 29 retained-success HPO prototype

Status: owner-approved disposable prototype evidence. It is not production implementation.

Question: can the direct HPO module select from any nonempty collection of retained successful runs
without a failure record, candidate-prefix rule, trial cap, retry state, or completion gate?

The generic logic receives retained successes only. Each success carries its exact typed candidate,
finite complete-validation `total_loss`, earliest best epoch, and completed epochs. Selection is the
lowest loss; exact equality retains the earlier retained run. One success is enough to publish.

There is no candidate table, table construction, sampler, exploration seed, tier, or candidate
count. Model-training seed `2026` is the only seed. The operator supplies one complete strict typed
candidate at a time and chooses what to run next and when to publish. Interruption or any failure
creates no retained or canonical record. After inspection, the operator may delete the failed run's
disposable private work.

The generic module supports arbitrary independent Tune requests and has no chain count. Issue 49
happens to create three requests because its current protocol has three chains. Each request
pre-mints one study ID and binds its corpus, complete `ExperimentSemantics`, and typed `MethodSpace`.
One thin operator-edge loader constructs a typed candidate, validates it against that space, and
passes it directly to `run_candidate(tune_request, candidate)`. Retained successes accumulate in the
same study until the operator explicitly publishes it. Any remote per-call payload is private
execution input, not a durable workflow request or domain identity.

This requires a narrow amendment to Issues 13/15: private `progress.json` keeps its exact outer
shape, but `trials` is the current ordered collection of retained successful runs rather than a
prefix of an authoritative candidate list. Each entry carries its complete typed candidate. The
module validates the whole current file before every append or publication and atomically appends
every valid success, including an exact duplicate method. It does not enforce historical continuity
or expose deletion, replacement, tombstone, audit, or retention operations.

After proving no live or queued writer exists, the operator may manually edit the unpublished file
outside the module's interface and guarantees. A later run validates the edited study ID, exact
schema, MethodSpace membership, finite loss, best epoch, and completed epochs. Invalid edits fail
closed and preserve the bytes; the module never repairs them. Duplicates remain separate results
and rank by loss then current order. Final immutable publication freezes the current nonempty valid
list; `load_study` still sees only immutable finalized studies, and no post-publication edit or
append is allowed. This explicitly accepts operator curation, repeat luck, and optional-stopping
effects as protocol responsibility.

One logical candidate run may span Slurm jobs through Issue 16's selected host-native private fit
checkpoint at the latest valid completed-validation boundary. A termination during an epoch drops
that partial epoch. A later job may restore the same candidate/run identity and the framework-owned
model, optimizer, completed epoch, best state/loss/epoch, patience, and available loop state from
the boundary. The checkpoint must live on storage visible to the later job. It is private fit work,
not a retained HPO result or HPO progress event. If no valid checkpoint exists, the operator may
restart with model seed `2026`, delete the failed private work, or choose another candidate. There
is no exact mid-batch/mid-epoch continuation, uninterrupted-bitwise claim, or framework-neutral
resume layer.

Candidate fits are Tune-private executions outside Issue 30's plan and attempt semantics. The
pre-persisted `TuneRequest` is the only durable study authority. A thin operator command loads it
with one strict typed candidate and uses Issue 19's direct remote/Slurm functions with an ephemeral
per-call payload. Add no candidate workflow request, ID, root, plan, attempt ledger, scheduler,
coordinator, queue, or service. Issues 18 and 36 retain their canonical Tune requests but do not
submit each as one whole-study plan.

Every `run_candidate` and `publish_study` invocation acquires the same stable shared whole-study
advisory lock without waiting. The lock protects private study bytes and immutable publication, not
Slurm submission uniqueness. A lost `sbatch` acknowledgement blocks all candidate work and
publication. The operator must inspect controller/accounting and private work, identify or cancel
every possibly accepted job, and continue only after one job reaches a safe outcome or absence is
proved. Otherwise the study remains stopped; there is no immediate resubmit or force path. Cancel
queued duplicates. An overlapping duplicate fails on the lock; sequential duplicates require
manual clearance.

## Private request authority

HPO owns one request-only private persistence seam. A runtime-supplied shared Tune work root and the
canonical study ID derive one contained private directory holding immutable `request.json`, mutable
`progress.json` when successes exist, and the empty stable lock anchor. Before any candidate
submission, `persist_tune_request` writes exact `WORKFLOW_REQUEST_ADAPTER.dump_json(request) + b"\n"`
bytes through the approved hidden-sibling sync/no-replace immutable-file primitive. A valid
byte-identical request is a no-op; malformed or different content conflicts; persistence failure
starts no work.

The exact public interface is:

```python
persist_tune_request(work_root, request)
run_candidate(work_root, study_id, candidate)
publish_study(work_root, study_id)
```

Request loading stays private. It validates containment, kind, schema, and embedded identity. No
root, path, host, target, job, status, or lifecycle fact persists. `publish_study` loads the original
request and current progress, validates and no-replace publishes the completed study, verifies the
canonical reload, then removes only `progress.json`. The immutable request and lock remain private
operator-owned files; the operator may later remove the whole directory outside the application.
There is no deletion or retention interface.

## Typed training-definition composition

The request seam uses complete typed values, never patches. `ExperimentSemantics` owns the complete
windows, context `C`, horizon `K`, ordered features, loss, and other legitimate experiment facts.
The finalized study supplies one selected typed method: concrete family/capacity/dropout, optimizer
and LR/WD, semantic training batch, seed, and stopping facts. `SelectedStudySource` carries only its
corpus ID, study ID, and complete `ExperimentSemantics` value.

One pure materializer loads the immutable study, selects its retained success deterministically,
composes its method with the supplied semantics, validates the full `TrainingDefinition`, and
derives study/result provenance. JSON or YAML may author the complete strict semantics document;
no arbitrary parameter/value patch, dotted path, registry, reflection, matrix framework, or generic
override engine crosses the request seam. Fixed-control context work may reuse the same semantics
type without using a selected study.

## Batch semantics

Physical training batch `{32,64}` remains an HPO axis and accumulation is fixed at `1`. The selected
per-chain training batch freezes across every final-K fit; fixed-control context uses batch `64`.
Training, validation, and evaluation use ordinary `DataLoader` behavior with its locked
`drop_last=False` default, so the argument is omitted. The final short training batch performs one
optimizer update; validation and evaluation include every origin through exact additive totals.
Validation/evaluation batch size is runtime-only. Add no project-owned `drop_last` field, custom
tail handling, padding, omission, mask, or static-shape machinery; one lean full-plus-tail interface
test is sufficient.

Run the interactive synthetic model:

```console
uv run python docs/research/issue-29-bounded-hpo/prototype.py
```

Run every bounded probe:

```console
uv run python docs/research/issue-29-bounded-hpo/prototype.py --all
```

The prototype budget is one local CPU run under five minutes. No model is fit. Stop after verifying
selection with one and several successes, exact duplicate methods, deterministic equality, current
manually curated snapshot validation, malformed-edit failure, and zero failure/interruption or
completion state.
