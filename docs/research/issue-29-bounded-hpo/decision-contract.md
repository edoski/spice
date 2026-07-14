# Bounded HPO and immutable study contract

Status: owner-approved final contract on 2026-07-14. This is planning evidence only. It authorizes
no production change or real model fit.

This contract resolves [Choose the bounded HPO, trial-budget, and study-lifecycle
policy](https://github.com/edoski/spice/issues/29) for the amended three-family protocol in
[Approve the temporal baseline and ablation protocol](https://github.com/edoski/spice/issues/49#issuecomment-4966379354).

## Domain terms

- **TuneRequest**: the sole durable definition and identity of one study. It pre-mints `study_id`
  and binds one corpus, one complete `ExperimentSemantics`, and one family-specific `MethodSpace`.
- **ExperimentSemantics**: complete experiment-owned facts: role windows, `C`, `K`, ordered
  features, loss, and every other legitimate semantic fact not selected by HPO.
- **MethodSpace**: the finite typed set of methods accepted by one study. It contains no candidate
  order, generator, candidate-construction/sampler seed, tier, count, or completion rule.
- **Method**: one complete typed family/method value: model capacity and dropout, AdamW learning
  rate and weight decay, semantic training batch, seed, stopping, and fixed fit facts.
- **Retained result**: one structurally valid successful result in the current private snapshot or
  immutable published study. It is not an attempt, status, or proof of execution history.
- **Published Study**: the original TuneRequest plus the current nonempty ordered retained-result
  snapshot, immutably published. It stores no winner.

## Direct engine and frozen method spaces

Use one SPICE-owned direct module. Remove Optuna completely: dependency, sampler, pruner, RDB or
Journal storage, configuration, adapters, trial states, summaries, callbacks, and Optuna-specific
tests and documentation. The dependent audit found no separate approved consumer. Keep no fallback
or dormant path. SQLAlchemy has separate consumers and is not removed by this decision.

The module supports any number of independent TuneRequests and has no chain count. The amended
baseline happens to create exactly three studies—one per chain—after one global family wins the
fixed three-family validation comparison. Family is fixed before each study and is never a mixed
study parameter. All three family MethodSpaces freeze before outcomes.

There is no candidate table, deterministic or random table construction, sampler, PRNG,
exploration seed, capacity-tier field, row number, mandatory control candidate, runtime trial
count, budget, cap, exhaustive-completion gate, or candidate-list provenance. Model-training seed
`2026` is the only HPO seed.

The exact capacity choices are:

| Family | Allowed model capacities |
| --- | --- |
| LSTM | `(projection=128, hidden=256, layers=1, head_hidden=128)`; `(256,256,2,256)`; `(256,384,2,256)` |
| Transformer | `(model_width=192, heads=4, layers=3, feedforward=384, head_hidden=192)`; `(256,4,4,512,256)`; `(384,8,4,768,256)` |
| Transformer–LSTM | `(model_width=192, heads=4, transformer_layers=3, feedforward=384, lstm_hidden=192, lstm_layers=1, head_hidden=192)`; `(256,4,4,512,256,1,256)`; `(384,8,4,768,384,1,256)` |

Every family allows dropout `{0.1, 0.2, 0.3}`, AdamW weight decay `{0, 1e-4, 1e-3}`, and physical
training batch `{32, 64}`. LSTM learning rate is `{1e-4, 3e-4, 1e-3}`. Transformer and
Transformer–LSTM learning rate is `{3e-5, 1e-4, 3e-4}`. Fixed method facts are accumulation `1`,
global-norm clipping `1.0`, no scheduler, seed `2026`, `max_epochs=36`, validation every completed
epoch, patience `8`, semantic `min_delta=0`, strict-lower improvement, earliest-best restoration,
and no minimum-epoch floor. A Method is valid only when complete, from the request's family, within
these leaves, and valid under the concrete model's cross-field invariants.

Optional human candidate suggestions may exist only as research prose. Runtime never reads or
enforces them.

## Typed composition, never patches

The request seam carries complete typed values. `SelectedStudySource` carries `corpus_id`,
`study_id`, and the complete `ExperimentSemantics` for the downstream fit. Strict JSON or YAML may
author a complete semantics document. No arbitrary parameter/value patch, dotted path, registry,
reflection, matrix framework, generic override engine, or partial tuned-parameter overlay crosses
the seam.

One pure materializer loads the immutable study, derives its selected retained-result position by
`(validation_total_loss, current_order)`, composes that complete Method with the supplied complete
semantics, validates the full `TrainingDefinition`, and derives study/result provenance. It verifies
the explicit corpus ID against the study. Fixed-control context work may reuse the same semantics
type without a selected study.

## Request-only private persistence

HPO owns exactly this public interface:

```python
persist_tune_request(work_root, request)
run_candidate(work_root, study_id, candidate)
publish_study(work_root, study_id)
```

Request loading is private implementation. Runtime supplies one shared private Tune work root. A
canonical `study_id` derives one contained private study-work directory containing:

```text
request.json   immutable TuneRequest authority
progress.json  current successful-result snapshot, only when at least one success exists
<lock anchor>  stable empty kernel advisory-lock file
```

This directory is private work, not a canonical study, domain identity, plan, or transferable
record. Persist no work root, path, host, target, job, status, or lifecycle fact.
The selected mount must satisfy the already-approved advisory-lock and atomic-replacement
capability gates and be reachable by every candidate-continuation job.

Before any candidate submission, `persist_tune_request` publishes exact
`WORKFLOW_REQUEST_ADAPTER.dump_json(request) + b"\n"` bytes through the approved contained
hidden-sibling file sync and no-replace primitive. A valid byte-identical existing request is a
no-op. Malformed or different content conflicts. Persistence failure starts no work. The private
loader validates containment, file kind, schema, canonical embedded IDs, and exact request bytes.
Persistence also creates or validates the stable empty lock anchor. An absent `progress.json`
means no retained result; it never means a completed study.

The three ready TuneRequests from the baseline/runner contracts call this owner. They are not
atomic execution plans. After study publication, `request.json` and the lock anchor remain private
operator-owned files. The operator may later remove the whole private directory outside the
application. There is no application deletion or retention interface.

## Candidate execution and successful-result evidence

The operator supplies one complete strict typed candidate at a time. `run_candidate` acquires the
stable whole-study lock without waiting, loads the persisted request, checks canonical-study
absence under that lock, loads and validates the current private snapshot, validates the candidate
against MethodSpace, and runs one fit on the request's frozen training/validation semantics. Every
engine-run candidate in one study therefore uses the same validation origins and complete additive
validation `total_loss`. Sealed test origins and metrics remain unavailable.

There is no HPO pruning. Ordinary per-fit 36/8 early stopping remains. Each new fit resets model
seed `2026` before model construction, stochastic objects, and shuffled training loader.

A valid success records only:

- the complete typed Method;
- finite complete-validation `total_loss`;
- `1 <= earliest_best_epoch <= completed_epochs <= 36`.

The module atomically replaces `progress.json` with the current validated list plus that result.
Every valid success appends, including an exact duplicate Method. Failure, interruption, invalid
candidate, nonfinite objective, or failed append creates no HPO result.

Add no outcome/failure tag, attempt, slot, candidate ID/root/request, status, retry count, legal-next
rule, skipped/substituted record, timestamp, duration, host, path, resource, checkpoint, test metric,
predictive/economic metric, selected field, or duplicated best summary.

## Current snapshot and manual curation

The private file keeps the approved exact outer shape:

```json
{"study_id":"<uuidv4>","trials":["<ordered retained successful-result records>"]}
```

`trials` is the current operator-trusted snapshot, not an append-only prefix or execution history.
Before every candidate run and publication, the module validates the current bytes from scratch:
matching study ID, exact schema, every complete Method within MethodSpace, finite loss, and valid
epoch facts. It does not compare a previous version or enforce historical continuity.

After proving there is no live or queued writer/candidate job, and before publication, Edo may
manually curate `progress.json` through the filesystem. This is outside the module's interface and
guarantees. The approved use includes deleting entries; because no history exists, software can
only validate the resulting current snapshot, not authenticate its prior order or provenance.
Malformed or semantically invalid edits fail closed and preserve bytes. The module never repairs,
or records invalid edits or curation. It exposes no curation, retained-result delete/replace,
tombstone, audit, or history interface. Duplicates are valid separate results.

## Slurm submission, locking, and fit continuation

Candidate fits are Tune-private executions outside the atomic-plan attempt contract. A thin
operator command loads the persisted TuneRequest plus one candidate and uses the approved direct
remote/Slurm functions with an ephemeral per-call payload. The payload is private execution input,
not a WorkflowRequest or durable identity. Add no plan, attempt ledger, scheduler, coordinator,
queue, service, or whole-study worker.

Every `run_candidate` and `publish_study` invocation acquires the same shared stable lock
nonblocking for its whole mutation/publication operation. A second overlapping writer fails before
work. The lock protects study bytes, not Slurm submission uniqueness.

A lost `sbatch` acknowledgement is ambiguous and blocks all new candidate work and publication.
Never immediately resubmit. The operator must inspect controller/accounting and private work,
identify or cancel every possibly accepted job, and continue only after one accepted job reaches a
safe outcome or absence is proved. Otherwise the study remains stopped; there is no force path.
Cancel queued duplicates. An overlapping duplicate fails on the lock; sequential duplicates need
manual clearance.

One logical candidate fit may continue across jobs through the selected host's native private
checkpoint at the latest valid completed-epoch/validation boundary. A mid-epoch termination loses
only the partial epoch; a later job restores the same candidate/run and the framework-owned model,
optimizer, completed epoch, best state/loss/epoch, patience, and available loop state. The checkpoint
must live on storage accessible to the next job. It is private fit work, never HPO progress or a
retained result. If no valid checkpoint exists, the operator may restart from seed `2026`, remove
the failed private fit work, or choose another candidate. Add no framework-neutral resume layer,
exact mid-batch/mid-epoch continuation, or uninterrupted-bitwise claim.

## Publication and deterministic selection

`publish_study(work_root, study_id)` is only validate-and-seal:

1. acquire the existing stable study lock nonblocking;
2. load the exact persisted TuneRequest and current `progress.json`;
3. validate matching study ID, a nonempty ordered result list, every complete Method within the
   declared MethodSpace, finite loss, and valid epoch facts;
4. build the completed Study from the original request plus that current ordered list;
5. validate, sync, and no-replace publish the immutable canonical study through the approved
   publication primitive;
6. reload and verify the canonical study;
7. remove only private `progress.json` after verified publication;
8. return the published Study.

It does not decide when enough runs exist, choose candidates, run training, manage checkpoints,
deduplicate, retain/delete/replace results, track attempts/failures/status/manual edits, or store a
winner. After canonical publication, every late candidate invocation fails before fit and no edit or
append is allowed.

Consumers derive selection from the immutable current order: lowest finite complete-validation
`total_loss`; exact equality keeps the earlier current entry. A single result is sufficient. The
derived result position is snapshot position, not candidate identity, attempt number, or execution
chronology.

Canonical evidence contains the original request and current ordered successes only. It contains no
failure, deleted entry, edit history, candidate guidance, checkpoint, scheduler fact, operator-stop
reason, or HPO weights. Separately approved minimal software/runtime provenance remains owned by
[Freeze durable ML, evaluation, weight-ABI, and provenance
contracts](https://github.com/edoski/spice/issues/34).

## Batch semantics

Physical training batch `{32,64}` is an HPO axis; accumulation is fixed at `1`. Training,
validation, and evaluation rely on ordinary PyTorch `DataLoader` behavior with default
`drop_last=False`; omit the argument and add no project field or provenance fact. The final short
training batch performs one optimizer update. Validation/evaluation include every origin through
exact additive, partition-invariant totals. Validation/evaluation batch size is runtime-only.

Add no custom tail, padding, mask, omission, or static-shape machinery. The selected per-chain
training batch freezes across all final-K fits. Fixed-control context uses batch `64`.

## Promotion and downstream artifacts

Promote only the selected complete Method. Never publish or transfer HPO weights or checkpoints.
Retained HPO runs have no `artifact_id`; add no special post-outcome artifact route and no HPO
finalist refit.

After all three studies publish, construct all 30 ordinary pre-persisted final-K TrainRequests,
including `K=5`. Every artifact trains fresh with the selected per-chain Method, seed `2026`, and
the approved stopping/batch semantics. It cannot reopen or confirm HPO selection. The artifact
freezes its effective TrainingDefinition plus derived study ID and immutable result position.
Downstream `K=5` training is an ordinary artifact fit, not an HPO refit. Context remains the fixed
family control.

## Exact claim boundary

“Bounded HPO” now means a frozen finite MethodSpace, bounded 36/8 individual fits, and one finite
immutable snapshot when the operator publishes. It does not mean a predeclared trial, attempt,
runtime, compute, money, or equal-exposure budget.

The exact selection claim is: the selected result is the earliest current entry with minimum finite
complete-validation `total_loss` among the nonempty structurally valid results present at
publication. The published study cannot prove every attempt, success, failure, original order,
engine-authenticated history, or why a result is absent. Structural validity is checked in software;
pre-publication history and curation rely on the trusted operator.

Duplicate Methods are separate selection opportunities, not independent-seed replications. They
support no variance or seed-robustness estimate and may capitalize on allowed runtime/resume/device
nondeterminism. Operator-chosen candidates, repetitions, curation, and publication timing create
unequal exposure, optional stopping, repeat luck, and validation-selection bias. Independent chain
studies may differ in candidates, repetitions, retained counts, and effort.

Claim no exhaustive search, MethodSpace optimum, best attempted run, complete history, equal search
effort, cross-chain HPO comparability, unbiased selection, failure/success rate, compute bound, or
seed robustness. Candidate absence proves nothing. “Common validation origins” means the same
frozen origins across candidates within one chain, not identical origins across chains.

This discretion increases validation overfitting and researcher degrees of freedom, not test
leakage. HPO and curation use validation only; no HPO checkpoint/weight or test metric publishes;
selected Methods freeze before fresh final-K fits; sealed testing cannot reopen selection.

## Narrow dependent amendments

- [Choose configuration identities and the schema-owned workflow
  algebra](https://github.com/edoski/spice/issues/10#issuecomment-4957991242):
  `SelectedStudySource` gains complete typed `ExperimentSemantics`; TuneRequest persistence moves
  from a plan into the direct request-only private seam. Candidates remain ephemeral and are never
  WorkflowRequests.
- [Prototype the direct-discovery and lifecycle
  seam](https://github.com/edoski/spice/issues/13#issuecomment-4958431106) and
  [Choose publication, study mutability, deletion, transfer, and cutover
  primitives](https://github.com/edoski/spice/issues/15#issuecomment-4958096197): `trials` is a
  current operator-curated successful-result snapshot, not a budget-counting exact prefix. Remove
  order/budget/legal-next/history validation and partial-completion rules. Keep exact current-file
  validation, stable locking, immutable no-replace publication/load/transfer, and post-publication
  immutability.
- [Choose selection, reproducibility, best-state, nonfinite, and resume
  semantics](https://github.com/edoski/spice/issues/16#issuecomment-4952933150): candidate
  construction no longer exists; model seed `2026` and native completed-epoch fit continuation
  remain; HPO equality uses current published order.
- [Prototype the lean benchmark-runner
  boundary](https://github.com/edoski/spice/issues/18#issuecomment-4958432445) and
  [Choose the minimum surviving benchmark scheduling and data
  flow](https://github.com/edoski/spice/issues/36#issuecomment-4958746060): retain the canonical
  three TuneRequests, but persist them through HPO and do not submit each as one whole-study plan.
  Downstream provenance uses finalized snapshot position rather than Optuna chronology.
- [Choose the remote execution control
  architecture](https://github.com/edoski/spice/issues/19): direct transport accepts the Tune-private
  ephemeral call payload without gaining a scheduler or lifecycle.
- [Specify atomic plans and resumable
  submissions](https://github.com/edoski/spice/issues/30#issuecomment-4959576176): plan/attempt and
  completed-output rules apply to Train/Evaluate, not Tune-private candidate work or study
  publication.
- [Approve the temporal baseline and ablation
  protocol](https://github.com/edoski/spice/issues/49#issuecomment-4966379354): preserve exactly
  three selected-family studies, frozen per-chain origins, all three ex-ante MethodSpaces, seed
  `2026`, and fit rules; remove candidate/sampler seed, finite/equal trial budget, exhaustive
  completion, and fair-coverage implications.
- [Compare mature bounded-HPO frameworks for the final training
  host](https://github.com/edoski/spice/issues/61#issuecomment-4952919136): adopt its direct-engine
  route, but not its candidate-search seed because generation and sampling do not exist.

These are contract supersessions only. This ticket does not mutate sibling issues or their graphs.

## Clean-break implementation handoff

Replace, do not adapt, the current Optuna-shaped path. The later implementation should remove at
least the direct Optuna dependency; `modeling/tuned_config.py`; Optuna sampling/registry code;
partial overlay logic in `modeling/tuning.py`; count-driven `modeling/tuning_execution.py`;
`storage/study_optuna.py`; failure/count/timestamp/best-summary study schemas; sampler/pruner/budget
configuration; Optuna storage and CLI/reporting paths; and their tests. The exact code-review-sized
split remains owned by the later complete specification and implementation DAG.

Keep one deep HPO module behind the three approved functions, private request/progress loaders and
atomic writers, direct family-specific MethodSpace validation, pure deterministic selection, and
the typed downstream materializer. Add no engine class, registry, adapter hierarchy, generic
lifecycle module, compatibility reader, migration, transition test, or old/new dual path.

Lean implementation verification should cover:

1. exact request persistence/equality/conflict and private loading;
2. strict complete candidate membership and rejection before fit;
3. atomic valid success append, duplicate Methods, and failure byte equality;
4. valid current manual snapshot acceptance and malformed/nonfinite/out-of-space failure without
   rewrite;
5. one/many result selection, current-order ties, and empty publication rejection;
6. lock contention, immutable no-replace publication/reload, progress-only removal, and late-run
   rejection;
7. mocked lost-acknowledgement/manual-block behavior and no candidate plan/identity;
8. native epoch-boundary continuation without HPO checkpoint publication;
9. full-plus-tail DataLoader interface behavior;
10. pure selected-Method composition and fresh final-K provenance without weight transfer.

Use synthetic objectives and temporary roots only. Add no transition, architecture-deletion,
compatibility, framework-internal, exhaustive-space, or PyTorch-default tests. At implementation
time run the focused suite, Ruff, type checking, and `uv run vulture`; manually inspect every
Vulture finding before deletion.
