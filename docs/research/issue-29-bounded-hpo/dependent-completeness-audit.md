# Choose the bounded HPO, trial-budget, and study-lifecycle policy — dependent-completeness audit

Status: owner-approved planning evidence for **Choose the bounded HPO, trial-budget, and
study-lifecycle policy**. This audit evaluates the explicitly approved Decisions 1–11. It authorizes no
production, configuration, test, dependency, data, storage, training, evaluation, job, archive,
or sibling-ticket mutation.

## Verdict

The contract is complete. Decision 11 closes the last gap by giving the authoritative
`TuneRequest` a request-only private persistence owner after Tune candidate work was removed from
the atomic-plan contract. No consequential owner choice remains.

The surviving design is one direct SPICE-owned typed engine. It accepts one complete candidate at
a time, retains only the current operator-approved successful-result snapshot, and publishes an
immutable study on an explicit `publish_study` call. It has no Optuna dependency, sampler, pruner,
candidate generator, candidate table, trial count, runtime budget, completion gate, failure record,
attempt ledger, or historical-progress guarantee.

“Bounded HPO” now means a frozen finite family-specific `MethodSpace`, an individually bounded
36/8 fit, and a finite nonempty snapshot at publication. It does **not** mean a predeclared number
of candidates, equal search effort, an exhaustive study, or a compute budget.

## Resolved contract

### Scientific boundary and method spaces

The generic module supports any number of independent `TuneRequest`/study pairs and contains no
chain count. The amended temporal baseline protocol happens to construct exactly three requests—one
per chain—after one family wins the global validation comparison. Each request pre-mints one
`study_id` and binds one `corpus_id`, a complete typed `ExperimentSemantics`, and the selected
family's typed `MethodSpace`. Every engine-run candidate uses the same frozen per-chain validation
origins; sealed testing remains unopened.

The allowed capacity values are complete model definitions. The explanatory names below are not
runtime tiers, tags, or candidate identities.

| Family | Allowed complete capacity values |
| --- | --- |
| LSTM | `(projection, hidden, layers, head)`: `(128,256,1,128)`, `(256,256,2,256)`, `(256,384,2,256)` |
| Transformer | `(width, heads, layers, FF, head)`: `(192,4,3,384,192)`, `(256,4,4,512,256)`, `(384,8,4,768,256)` |
| Transformer–LSTM | `(width, heads, T-layers, FF, LSTM-hidden, LSTM-layers, head)`: `(192,4,3,384,192,1,192)`, `(256,4,4,512,256,1,256)`, `(384,8,4,768,384,1,256)` |

Shared candidate leaves are weight decay `{0, 1e-4, 1e-3}`, physical training batch `{32,64}`,
and dropout `{0.1,0.2,0.3}`. LSTM learning rate is `{1e-4,3e-4,1e-3}`;
Transformer and Transformer–LSTM learning rate is `{3e-5,1e-4,3e-4}`. Candidate validation
accepts only a complete strict typed `Method` in the request's space. It rejects partial overlays,
unknown fields, wrong-family values, and invalid cross-field combinations before fitting.

Every fit uses model-training seed `2026`, accumulation `1`, global-norm clipping `1.0`, no
scheduler, `max_epochs=36`, and patience `8`. There is no candidate/table-construction seed and no
runtime PRNG, sampler, count, tier, or mandatory control position. Optional human guidance may
exist only as research prose; runtime never reads or enforces it.

### Public HPO seam and private storage

The complete public HPO interface is:

```python
persist_tune_request(work_root, request)
run_candidate(work_root, study_id, candidate)
publish_study(work_root, study_id)
```

The runtime-selected private directory for one `study_id` contains:

```text
<work_root>/<study_id>/
  request.json       immutable authoritative TuneRequest
  progress.json      mutable current successful-result snapshot, if any
  <lock anchor>       stable empty advisory-lock file
```

`persist_tune_request` writes exactly `WORKFLOW_REQUEST_ADAPTER.dump_json(request) + b"\n"` by
contained no-replace publication. Equal bytes are a no-op. Malformed or different existing bytes
are a conflict. The request is loaded only inside `run_candidate` and `publish_study`; there is no
public request loader, path/host field, status, plan, or attempt object.

`run_candidate` validates the immutable request, the complete strict candidate, and the current
progress file while holding the stable whole-study lock without waiting. A successful fit appends
one validated result by atomic whole-file replacement. The exact private progress envelope remains:

```json
{"study_id":"<uuidv4>","trials":["<ordered retained successful results>"]}
```

Each result contains its complete typed `Method`, finite complete-validation `total_loss`, earliest
best epoch, and completed epochs. Every valid success is appended, including another result for an
identical Method. Failure or interruption appends nothing and creates no HPO record. Failed fit
work is disposable after operator inspection.

The module treats the current `progress.json` as a snapshot, not an append history. It exposes no
delete, replace, tombstone, audit, retry, repair, or history interface and compares no prior
version. After proving every live and queued writer has stopped, Edo may manually edit unpublished
progress outside the module's interface and guarantees. The next operation validates the entire
current file: exact study ID/schema, complete Method membership, finite loss, and valid epoch facts.
Invalid edits fail closed and preserve the bytes.

`publish_study` takes the same nonblocking lock and requires a nonempty valid current collection.
It stores no winner or selected index. Consumers derive the lowest finite loss; exact equality
retains the earlier current-list entry. Publication uses the approved hidden-stage sync, immutable
no-replace visibility, canonical reload, and equal/no-op versus conflict rules. Canonical presence
forbids later append or publication with different bytes. After verified publication, the operation
removes only `progress.json`; `request.json` and the lock anchor remain. The application never
removes the whole private study directory. Whole-directory disposition is manual and outside the
application.

### Tune-private Slurm execution and fit continuation

Candidate fits are Tune-private operations outside the atomic-plan contract's plan and attempt
semantics. A thin
operator command loads the persisted request, accepts one ephemeral strict candidate payload, and
uses the remote-control contract's concrete OpenSSH/Slurm functions to call `run_candidate`. The
payload is private execution input, not a `WorkflowRequest`, request root, candidate ID, plan,
attempt, scheduler, coordinator, queue, or service. The three canonical `TuneRequest` values remain
scientific requests and study authorities, but none is submitted as one whole-study atomic plan.

The whole-study lock protects private bytes and canonical publication, not Slurm submission
uniqueness. Overlapping jobs fail when they cannot acquire the lock. Queued duplicates must be
cancelled; sequential duplicates require operator clearance and may append separate successes.

A lost `sbatch` acknowledgement blocks all candidate work and study publication. The operator must
inspect controller, accounting, and private work; identify or cancel every possibly accepted job;
and proceed only after one job reaches a safe outcome or absence is proved. Otherwise the study
stays stopped. There is no immediate resubmit, force path, persisted marker, or atomic-plan
reconciliation record.

One logical fit may cross Slurm jobs through the selected host's native private checkpoint at the
latest valid completed-epoch/validation boundary. The next job restores the same private fit's
framework-owned model, optimizer, completed epoch, best state/loss/epoch, patience, and available
loop state. An interrupted partial epoch reruns. The checkpoint must be visible to the next job but
never becomes HPO progress, a retained result, an artifact, or a transferable object. With no valid
checkpoint, the operator may restart from seed `2026`, delete the private fit work, or choose a
different candidate. There is no exact mid-batch/mid-epoch or uninterrupted-bitwise claim and no
framework-neutral resume layer.

### Typed composition, batch behavior, and promotion

`ExperimentSemantics` owns the complete windows, context `C`, horizon `K`, ordered features, loss,
and other legitimate experiment facts. A selected `Method` owns the concrete family/capacity/
dropout, optimizer/LR/weight decay, semantic training batch, seed, and stopping facts.
`SelectedStudySource` carries `corpus_id`, `study_id`, and one complete typed semantics value.

One pure materializer loads the immutable study, derives the selected current-list result, composes
its Method with the supplied semantics, validates the complete `TrainingDefinition`, and derives
study/result provenance. Complete strict YAML or JSON may author semantics. No arbitrary patch,
dotted path, registry, reflection, matrix framework, generic override engine, or partial tuned
parameter set crosses the request seam.

Ordinary PyTorch `DataLoader` behavior supplies full-plus-tail batches. The project omits the
`drop_last` argument and adds no project field for it. The final short training batch performs one
optimizer update; validation and evaluation include every origin through additive totals.
Validation/evaluation batch size is runtime-only. The selected physical training batch freezes
across all ten final-K fits for its chain; context remains fixed-control batch `64`.

Promotion transfers only the selected typed Method, never HPO weights or checkpoints. Retained HPO
runs have no `artifact_id`. All 30 final-K `TrainRequest` values, including `K=5`, are separately
pre-persisted ordinary requests and train fresh with seed `2026` and the frozen Method. This is not
an HPO finalist refit. Each resulting artifact freezes its effective `TrainingDefinition` plus
derived study/result provenance. If the durable field remains named `trial_number`, its meaning is
the selected index in the immutable published current-list order—not a candidate ID, execution
attempt, or chronology.

## Primary evidence

### Closed and dependent decisions

| Primary source | Binding input consumed here |
| --- | --- |
| [Choose configuration identities and the schema-owned workflow algebra](https://github.com/edoski/spice/issues/10#issuecomment-4957991242) | Exact typed request union, once-only IDs, strict schemas, concrete family union, and no patch/registry architecture. |
| [Prototype the direct-discovery and lifecycle seam](https://github.com/edoski/spice/issues/13#issuecomment-4958431106) | Direct completed-study loading, private progress, immutable canonical studies, and no public lifecycle object. |
| [Choose publication, study mutability, deletion, transfer, and cutover primitives](https://github.com/edoski/spice/issues/15#issuecomment-4958096197) | Same-mount durable publication, stable advisory lock, completed-only transfer, no-replace immutability, and no application deletion surface. |
| [Choose selection, reproducibility, best-state, nonfinite, and resume semantics](https://github.com/edoski/spice/issues/16#issuecomment-4952933150) | Finite complete-validation `total_loss`, strict-lower/earliest tie, nonfinite failure, earliest-best restoration, and host-native completed-validation continuation. |
| [Prototype the lean benchmark-runner boundary](https://github.com/edoski/spice/issues/18#issuecomment-4958432445) | HPO remains inside the Tune domain; selected study/result provenance flows to final-K training. |
| [Choose the remote execution control architecture](https://github.com/edoski/spice/issues/19#issuecomment-4958492443) | Concrete OpenSSH/rsync/Slurm functions and runtime-only target/resources; no Session/backend abstraction survives. |
| [Specify atomic plans and resumable submissions](https://github.com/edoski/spice/issues/30#issuecomment-4959576176) | One-request plan and attempt reconciliation remains for Train/Evaluate only after the approved Tune-private exception. |
| [Freeze durable ML, evaluation, weight-ABI, and provenance contracts](https://github.com/edoski/spice/issues/34) | This still-open owner may add only its separately approved minimal software/runtime provenance and final encoding; it may not recreate HPO attempt/history state. |
| [Choose the minimum surviving benchmark scheduling and data flow](https://github.com/edoski/spice/issues/36#issuecomment-4958746060) | Exactly three canonical Tune requests for the thesis ready set and exact selected-study provenance, without benchmark matching or graph state. |
| [Approve the temporal baseline and ablation protocol — three-family amendment](https://github.com/edoski/spice/issues/49#issuecomment-4966379354) | Three frozen family controls, one global validation-selected family, then exactly three winner-family studies; fixed validation roles, seed, stopping, final-K grid, and sealed tests. |
| [Compare mature bounded-HPO frameworks for the final training host](https://github.com/edoski/spice/issues/61#issuecomment-4952919136) | Direct SPICE-owned search is the lean recommendation unless adaptive sampling/pruning earns Optuna. The approved policy found neither need. |

### Current code that the clean break replaces

The repository still implements the pre-decision architecture. This is implementation scope, not
evidence that the old contract survives.

| Current code evidence | Observed old behavior | Contract consequence |
| --- | --- | --- |
| [`pyproject.toml`](../../../pyproject.toml) and [`uv.lock`](../../../uv.lock) | Direct Optuna dependency and transitive lock entries. | Remove Optuna completely; do not retain a fallback or dormant path. |
| [`src/spice/storage/study_optuna.py`](../../../src/spice/storage/study_optuna.py) | Optuna `RDBStorage`, TPE sampler, Median/Nop pruners, mutable load/create, and best-trial reads. | Replace with request-only private files, current successful-result progress, and immutable publication. |
| [`src/spice/modeling/tuning_execution.py`](../../../src/spice/modeling/tuning_execution.py) | Target/remaining trial counts, timeout, Optuna trial states/callbacks, generated candidates, and whole-study `optimize`. | Replace with independent `run_candidate` and explicit `publish_study`; no count, timeout, state, or whole-study runner. |
| [`src/spice/config/models.py`](../../../src/spice/config/models.py) | `TuningConfig` stores `trial_count`, timeout, sampler seed, and pruning; `TunedParameterSet` and search groups are partial overlays. | Replace with complete `ExperimentSemantics`, complete typed `Method`, and typed `MethodSpace`. |
| [`src/spice/config/selections.py`](../../../src/spice/config/selections.py), [`src/spice/cli/options.py`](../../../src/spice/cli/options.py), and [`src/spice/cli/commands/workflows.py`](../../../src/spice/cli/commands/workflows.py) | Tune selection and CLI expose an enforced `trial_count`. | Remove the count option and whole-study Tune command; the later CLI exposes only the approved request persistence, candidate, and publication operations. |
| [`src/spice/modeling/tuned_config.py`](../../../src/spice/modeling/tuned_config.py) and [`src/spice/modeling/families/registry.py`](../../../src/spice/modeling/families/registry.py) | Optuna categorical sampling and registry-dispatched partial family parameters. | Delete sampling and registry paths; validate a supplied complete family-discriminated Method directly. |
| [`src/spice/modeling/tuning.py`](../../../src/spice/modeling/tuning.py) | Applies partial parameter overlays and reloads an Optuna best trial. | Replace with one pure immutable-study Method-plus-semantics materializer. |
| [`src/spice/storage/study_models.py`](../../../src/spice/storage/study_models.py) | RUNNING/WAITING/PRUNED/FAIL vocabulary, counts, timestamps, and duplicated best summary. | Retain only ordered successful results; consumers derive selection during load/materialization, never publication. |
| [`src/spice/storage/ids.py`](../../../src/spice/storage/ids.py) and [`src/spice/storage/workflow_root_materialization.py`](../../../src/spice/storage/workflow_root_materialization.py) | Current study identity is derived from a config hash; approved `TuneRequest`/UUIDv4 symbols do not yet exist in production. | Consume the request/schema implementation owned by the configuration contract; never derive or remint `study_id` during execution. |
| [`src/spice/storage/engine.py`](../../../src/spice/storage/engine.py), [`src/spice/storage/workflow_roots.py`](../../../src/spice/storage/workflow_roots.py), and [`src/spice/storage/transactions.py`](../../../src/spice/storage/transactions.py) | Study roots are mutable `state.sqlite` transactions. No production advisory-lock primitive exists. | Replace the HPO path with immutable request, current progress, stable kernel lock, and canonical no-replace study publication; do not reuse the mutable transaction owner. |
| [`src/spice/workflows/tune.py`](../../../src/spice/workflows/tune.py) | Opens and runs one whole mutable tuning execution. | Replace with the three public HPO operations and thin Tune-private operator edge. |
| [`src/spice/modeling/persisted_training.py`](../../../src/spice/modeling/persisted_training.py) | Current `run_trial_training` has no candidate checkpoint input and builds a summary through validation and sealed-test evaluation. | Candidate fitting must use the approved validation-only native fit path; sealed testing and artifact publication never occur inside HPO. |
| [`src/spice/execution/session.py`](../../../src/spice/execution/session.py), [`src/spice/execution/remote_runner.py`](../../../src/spice/execution/remote_runner.py), and [`src/spice/execution/submission.py`](../../../src/spice/execution/submission.py) | Snapshot/config-based whole-workflow Tune submission and generic execution lifecycle. | Reuse only the eventual concrete transport/Slurm primitives for ephemeral candidate calls; the atomic-plan contract excludes Tune. |
| [`src/spice/benchmarks/plan_materialization/_models.py`](../../../src/spice/benchmarks/plan_materialization/_models.py) and [`src/spice/benchmarks/submission.py`](../../../src/spice/benchmarks/submission.py) | Benchmark entries persist trial counts and submit every Tune entry as one job. | The benchmark owner deletes this machinery; the surviving thesis ready set only constructs three canonical Tune requests for private persistence. |
| [`src/spice/conf/tuning/`](../../../src/spice/conf/tuning/) and [`src/spice/conf/tuning_space/`](../../../src/spice/conf/tuning_space/) | Runtime trial budgets, sampler seed, and historical spaces. | Delete these runtime HPO configs. Optional candidate guidance is research prose only. |
| [`tests/modeling/test_tuning_execution.py`](../../../tests/modeling/test_tuning_execution.py) and [`tests/modeling/test_tuned_config.py`](../../../tests/modeling/test_tuned_config.py) | Tests Optuna lifecycle, sampling, counts, and overlays. | Replace with the focused behavior matrix below; add no transition tests. |

An import audit found production Optuna imports only in
`modeling/families/registry.py`, `modeling/tuned_config.py`, `modeling/tuning_execution.py`,
`storage/study_models.py`, and `storage/study_optuna.py`; all are HPO-owned paths. No separately
approved Optuna consumer exists. Optuna-only Alembic and Colorlog lock entries leave with it.
SQLAlchemy has separate current consumers, and `tqdm` remains reachable through Lightning, so
neither is deleted as collateral damage; package/dependency ownership remains with its dedicated
owner.

The current production tree contains none of the approved `TuneRequest`,
`WORKFLOW_REQUEST_ADAPTER`, `ExperimentSemantics`, `MethodSpace`, `SelectedStudySource`,
`persist_tune_request`, `run_candidate`, or `publish_study` symbols. Their absence is expected:
closed configuration/storage contracts specify the clean replacement, while later implementation
tickets must add it in dependency order. It does not justify a shim around the resolved-config or
Optuna path.

## Exact narrow supersessions

These are approved amendments, not compatibility modes. The old clauses disappear.

| Prior contract | Exact surviving amendment |
| --- | --- |
| **Configuration algebra:** selected-study source held only corpus/study IDs; every request became durable through a benchmark/direct plan. | `SelectedStudySource` also carries complete typed semantics. Tune uses `persist_tune_request` in its private study directory, not an atomic plan. Candidate payloads are private inputs, not requests or identities. |
| **Direct discovery:** progress was an immutable exact prefix of budget-counting trials and publication required study completion. | Progress is the current ordered successful-result snapshot. Any nonempty valid current snapshot may publish. No budget, legal-next, prefix, completion, or historical-continuity check remains. |
| **Publication/lifecycle:** prior entries never changed; changed prefixes failed; private work held progress plus a lock; progress removal completed cleanup. | Edo may manually edit unpublished progress only after all writers are proven stopped. Private work also owns immutable `request.json`; verified publication removes only progress and leaves request plus lock. Whole-directory disposition is manual. Canonical studies remain immutable. |
| **Selection/reproducibility:** seed applied to candidate construction; equality used predeclared evaluation order; pruning remained conditional. | Candidate construction does not exist. Model seed `2026` remains. Equality uses current published order. Pruning and all report/prune machinery are deleted. |
| **Runner boundary:** all exact requests were persisted and submitted through the plan owner; HPO trials stayed inside one Tune submission. | The three Tune requests remain canonical scientific requests, but candidate fits and publication are Tune-private and outside the atomic-plan contract. Train/Evaluate plan semantics are unchanged. |
| **Remote control:** batch stdin contained only one exact `WorkflowRequest`; ambiguous submission reconciliation belonged to the plan owner. | Tune-private calls use one ephemeral strict candidate payload with the persisted request through the concrete remote-control primitives. Lost acknowledgement invokes the approved manual stop/inspect/cancel/prove-absence rule and no durable reconciliation state. |
| **Atomic plans:** the generic `WorkflowRequest` plan seam included Tune. | Plan/attempt/restart semantics cover Train/Evaluate only. Tune has no plan, attempt ordinal, marker, job record, or force path. |
| **Durable records:** historical study snapshot/provenance was still open. | The durable-record owner may encode only the immutable current successful-result snapshot and separately approved minimal software/runtime facts. Consumers derive selection; downstream artifacts may record the selected snapshot position with their effective definition. It cannot add a study winner, failure, edit, attempt, job, checkpoint, path, or history evidence. |
| **Benchmark flow:** the Tune ready set handed three requests to the atomic-plan owner and `trial_number` implied an execution trial. | The ready set constructs the same three requests for request-only private persistence. Selected provenance points to current published result order; it does not identify execution history. |
| **Three-family protocol:** the temporal baseline delegated a candidate seed and finite trial scope and older coordination requested equal validation-only budgets. | There is no construction seed, trial count, equal budget, exhaustive gate, or coverage claim. Exactly three studies, frozen per-chain validation origins, frozen MethodSpaces, seed `2026`, and 36/8 fits survive. |
| **Framework comparison:** direct *seeded* search was recommended while Optuna remained conditional. | Direct typed operator-supplied candidates win. The generator/sampler seed and Optuna condition are removed because there is no adaptive sampler or pruning consumer. |

## Claim boundary

The published study supports only these statements:

- it is an immutable publication of the current nonempty structurally valid operator-approved
  result snapshot;
- selection is deterministic: minimum finite complete-validation `total_loss`, with exact ties
  resolved by earlier current-list order;
- engine-run candidates use the frozen per-chain validation origins, MethodSpace, model seed
  `2026`, and 36/8 fit semantics;
- the selected Method—not HPO weights—is the downstream method provenance; and
- sealed testing did not select candidates or alter the study.

It does not support claims of a complete attempt or success history, original execution order,
engine-authenticated provenance after manual editing, best attempted candidate, exhaustive search,
MethodSpace optimum, equal search effort, cross-chain search parity, unbiased selection, compute
budget, failure rate, optional-stopping control, or seed robustness. Candidate absence proves
nothing about whether it ran or failed. Repeated identical Methods are separate selection
opportunities, not independent replication evidence.

Because manual unpublished editing is explicitly allowed and no prior snapshot is compared, the
software validates current structure and values only. It cannot distinguish an engine-appended
entry from a manually authored or altered structurally valid entry. Canonical publication therefore
records operator-asserted current evidence, not an audit trail. This consequence is approved and
creates no missing owner choice.

## Deletion and ownership

The later implementation is a clean replacement. It removes Optuna dependency/lock entries,
Optuna RDB storage, sampler/pruner construction, trial status/count/timestamp/best-summary models,
budget/timeout/seed/pruning config and CLI/benchmark fields, generated-candidate and partial-overlay
machinery, whole-study Tune execution/submission, historical tuning YAML, and their Optuna-specific
tests. It retains no fallback, dormant adapter, old reader, migration, alias, version marker,
transition test, or compatibility path.

| Owner | Surviving responsibility |
| --- | --- |
| This bounded-HPO policy | Typed MethodSpaces, direct candidate validation/run, successful-result snapshot, deterministic selection, request-only private persistence, three public HPO functions, and Tune-private operator semantics. |
| [Choose configuration identities and the schema-owned workflow algebra](https://github.com/edoski/spice/issues/10) | Final strict request/source/Method/MethodSpace/TrainingDefinition schemas and concrete family union. |
| [Prototype the direct-discovery and lifecycle seam](https://github.com/edoski/spice/issues/13) and [Choose publication, study mutability, deletion, transfer, and cutover primitives](https://github.com/edoski/spice/issues/15) | Canonical direct study loader and immutable no-replace publication/transfer rules. This ticket's approved private request/progress/lock seam is their narrow Tune exception. |
| [Choose selection, reproducibility, best-state, nonfinite, and resume semantics](https://github.com/edoski/spice/issues/16) and [Prototype and choose the lean training host](https://github.com/edoski/spice/issues/26) | Finite-loss/best-state behavior and selected-host native completed-validation checkpoint continuation. |
| [Prototype the lean benchmark-runner boundary](https://github.com/edoski/spice/issues/18), [Choose the minimum surviving benchmark scheduling and data flow](https://github.com/edoski/spice/issues/36), and [Approve the temporal baseline and ablation protocol](https://github.com/edoski/spice/issues/49) | Exact thesis ready sets, three-study scientific topology, fixed family controls, validation origins, gates, and final-K inventory. |
| [Choose the remote execution control architecture](https://github.com/edoski/spice/issues/19) | Concrete OpenSSH/Slurm transport, target/resource validation, and scheduler inspection primitives. |
| [Specify atomic plans and resumable submissions](https://github.com/edoski/spice/issues/30) | Train/Evaluate request plans and attempt reconciliation only. |
| [Freeze durable ML, evaluation, weight-ABI, and provenance contracts](https://github.com/edoski/spice/issues/34) | Final minimal immutable study/artifact encoding and separately approved software/runtime provenance. |
| Package/dependency, documentation/ADR, and CLI owners | Dependency/lock mechanics, stale documentation cleanup, and the final operator CLI respectively. |

No HPO weights, failed-run evidence, private checkpoints, scheduler facts, host/path/resource values,
candidate tables, or operator edit history cross into canonical study or artifact state. No sibling
issue needs graph or body mutation to make this contract implementable; the listed supersessions
must be carried into their owning implementation/specification work.

## Lean verification matrix

| Seam | Required behavior evidence |
| --- | --- |
| Request persistence | Exact adapter JSON plus one LF; contained `<work_root>/<study_id>` address; no-replace publish; equal no-op; malformed/different conflict; internal load only. |
| Candidate validation | Complete valid Method accepted; wrong family, missing/extra field, out-of-space value, invalid capacity combination, or fixed-fact mismatch rejected before fit. |
| Successful append | Atomic whole-file replacement; finite loss/epoch facts enforced; exact duplicate Method retained as a separate ordered result. |
| Failure/interruption | Progress bytes remain unchanged and no HPO record appears. Disposable fit work does not become canonical evidence. |
| Manual curation | Valid current reorder/removal/addition/duplication is accepted after writer clearance; malformed JSON, wrong study ID, invalid Method, nonfinite loss, or bad epoch facts fail closed without rewrite. No history comparison occurs. |
| Selection/publication | Empty rejects; one result publishes; minimum loss wins; ties use current order; immutable no-replace publication/reload succeeds; request+lock remain; progress is removed; later append conflicts. |
| Locking | `run_candidate` and `publish_study` contend on the same stable nonblocking anchor; progress replacement does not change lock identity; process death releases the kernel lock. |
| Slurm edge | Persisted request plus ephemeral candidate only; no candidate request/ID/plan/attempt; overlapping job fails lock; lost acknowledgement blocks until manual safe clearance; no automatic retry. |
| Fit continuation | Restore only a valid host-native completed-validation checkpoint; rerun partial epoch; never copy checkpoint state into HPO progress or artifact promotion. |
| Typed materialization | Load canonical study only; derive selected result; compose Method with complete semantics; validate full `TrainingDefinition`; derive study/result provenance; never transfer HPO weights. |
| Batch boundary | Selected physical batch 32 or 64, accumulation 1, ordinary full-plus-tail loader behavior, final short training update, and partition-invariant validation/evaluation totals. One interface test; do not test PyTorch itself. |
| Static cleanup | Focused tests plus Ruff/Pyright; implementation-time `rg` confirms no Optuna or removed lifecycle/config names; `uv run vulture` findings are manually checked before deletion. No architecture-transition or compatibility tests. |

The disposable synthetic probe
`uv run python docs/research/issue-29-bounded-hpo/prototype.py --all` passes selection with one and
multiple successes, duplicate Methods, current manually curated snapshot validation, malformed-edit
failure, and zero failure/completion/outcome state. It fits no model and reads no scientific data.

Final audit result: **complete; zero remaining consequential owner choices**.
