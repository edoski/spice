# SPICE clean-break verification, evidence, and size semantics

Date: 2026-07-10

Scope: verification architecture, baseline evidence, code-size feasibility, conversion evidence, and final approval gates for the proposed clean break. This is a local-evidence note. Framework and filesystem claims are cross-checked against the primary-source links already collected in [clean-break-framework-semantics.md](clean-break-framework-semantics.md) and [clean-break-persistence-semantics.md](clean-break-persistence-semantics.md). Existing ADRs are historical inputs, not automatic approvals.

## Bottom line

The hard cap of 26,100 production Python lines is plausible. The proposed 23,200–24,650 range is only a planning hypothesis. It has no measured subsystem budget yet and must not become a compression target. A central deletion/addition model reaches about 23,600 lines, but storage, benchmark, and modeling replacement interfaces must be designed before that estimate can be trusted.

The current test suite contains valuable domain behavior, but much of its storage, benchmark, training, and serving coverage asserts shallow implementation shapes scheduled for deletion. Keep the behavioral intent and replace those tests at the new module interfaces. Do not layer new tests over catalog, Root Handle, registry, ledger, manual-fit-policy, or result-index tests.

Seven verification decisions remain human gates: finite/best-state behavior, resume ordering, exact loss reduction, persistence durability and conflict semantics, serving durability/backend, conversion eligibility, and the final code-size/evidence budget. The candidate route cannot safely treat any of these as implementation details.

## Reproduced baseline

All measurements below use commit `b9b9a53f42e3e88855ae5488ffff06d3d334fdee` on `main`. The worktree already contained unrelated modified and untracked files, so this note did not alter them.

| Claim | Local result | Judgment |
| --- | --- | --- |
| Production Python LOC | 29,004 lines under `src/spice/**/*.py` | Confirmed exactly using `find` plus `wc -l` |
| Full tests | 427 passed, 1 failed in 6.45 seconds | Confirmed; the sole failure is the stale evaluator-list expectation in [test_config_cli.py](../../../tests/cli/test_config_cli.py#L151) |
| Ruff | `uv run ruff check src tests` passed | Confirmed |
| Pyright | One `reportOptionalSubscript` error at [problem_store.py](../../../src/spice/temporal/problem_store.py#L133) | Confirmed |
| Vulture | `uv run vulture` exited successfully with no output | Confirmed only for the current tree; it says nothing about post-refactor code |
| Mobile typecheck | `npm run typecheck` passed under `apps/mobile` | Confirmed |
| CLI import/help | `uv run spice --help` passed and listed the current commands | Confirmed, but this is not a workflow smoke |
| Benchmark YAML count | 23 files under `src/spice/conf/benchmark` | The candidate's “17 checked-in benchmarks” is false for this revision |
| Test size | 75 test files and 15,585 Python lines | Confirmed; test code is already over half the production-code size |

The production history also warns against assuming gross proposals become net deletion. Production Python was 30,320 lines immediately before ADR commit `b1712278`, 29,377 after the May cleanup through `ce503d6b`, 28,605 at `e804880b`, and 29,004 now. The May cleanup deleted 3,152 production lines but added 2,209, for only 943 net lines removed. The later modeling clean break deleted substantial glue, while serving and new evaluation behavior added code back. Gross deletion and gross addition must therefore be reported separately.

Current subsystem LOC:

| Area | Lines |
| --- | ---: |
| Storage | 5,429 |
| Modeling | 5,171 |
| Benchmarks | 2,891 |
| Config | 2,333 |
| Corpus | 2,295 |
| Temporal | 1,548 |
| CLI | 1,456 |
| Features | 1,424 |
| Evaluation | 1,253 |
| Prediction | 1,025 |
| Serving | 983 |
| Execution | 931 |
| Acquisition | 889 |
| Workflows | 690 |
| Core | 548 |
| Package-level files | 138 |

### Historical 648-window evidence

The local historical run at `outputs/benchmarks/runs/lstm_36s_wall_clock_quartile_eval/20260628T131456Z` has:

- 648 unique plan rows: 216 each for Ethereum, Polygon, and Avalanche;
- 659 submission rows for 648 run IDs, with 11 duplicated run IDs;
- 648 collection records, again 216 per chain;
- one artifact and one evaluation corpus per chain;
- 29,144,083 total scored samples, with per-window counts ranging from 1,190 to 254,167;
- only three training-test `macro_f1` values, one per artifact/chain, proving that the collection is not a 648-window macro-F1 audit.

Frozen source hashes at inspection time:

| File | SHA-256 |
| --- | --- |
| `plan.jsonl` | `2b4bbb722f097ba685a828933b32f34eb6f3046e851bcf6c5127ec936ca2d136` |
| `submission.jsonl` | `f1aaf10fcd40d4d235155dbc9e373fdcea79e2b1bb659cd093e8bc73fac4379e` |
| `collection.json` | `3ac0a12a4fddced7a7c03472f38013c1bc61fe45d3e0cec27b87a7a056694d56` |
| `metadata.json` | `8f335307648302e305edf4ee033f7c59ac64f3f561c139ce2f8decb5995b62ba` |

The duplicated submissions matter. A new submission state machine must specify which attempt is authoritative and must never infer it from last-line-wins without validating job identity and revision.

The candidate's university statement “22 of 179 artifacts on the current manifest generation” is not supported by repository evidence. [CLEAN_BREAK_TRACKER.md](../../../CLEAN_BREAK_TRACKER.md) records a different June inventory: 8 corpora, 41 study roots, 433 artifact roots, 431 old artifact manifests, and 220 migratable artifacts. Those numbers may describe a different cut, but neither set is safe as a current cutover fact. Repeat and freeze the university inventory.

## Verification architecture: replace, do not layer

The new interface is the test surface. Tests should exercise behavior through the deepest owner module that callers use. Real temporary directories should exercise local filesystem behavior. A fake is justified for a true external dependency such as RPC, SSH, Slurm, or a clock; mocking `os.replace`, catalog helpers, or callback internals usually tests past the interface.

Recommended test seams:

- corpus acquisition: exact definition and source fingerprint in, promoted corpus or retained hidden stage out;
- root persistence/discovery: typed root reference in, validated record/path or a typed conflict/corruption result out;
- training execution: prepared fixed-context dataset plus training definition in, promoted artifact or resumable stage out;
- study execution: stored study definition plus trial budget in, coherent study snapshot out;
- benchmark run store: resolved plan in, durable plan/submission/collection state out;
- serving application: configuration in, lifespan-owned application behavior out;
- pure domain modules: feature construction, temporal geometry, action/outcome realization, scoring, and accounting directly.

Do not expose ports only to make tests easy. The filesystem is a real local dependency and should be used through temporary directories. RPC and remote execution already have genuine production/test adapters.

### Current tests that encode real behavior

Keep these behavioral contracts, rewriting imports and fixtures where the clean break changes the interface:

- acquisition request ordering, exact block-range validation, bounded retry/backoff, cancellation cleanup, and completed-prefix resume in [test_pull.py](../../../tests/acquisition/test_pull.py);
- RPC source-column/enrichment mapping and response validation in [test_rpc_client.py](../../../tests/acquisition/test_rpc_client.py);
- corpus null/schema/window/ordering/coverage checks in `tests/corpus/test_contract.py`, `test_validation.py`, and `test_coverage.py`;
- feature finiteness, causal lagging, source prerequisites, and fingerprint ownership in [test_core_fee_dynamics.py](../../../tests/features/test_core_fee_dynamics.py);
- fixed-context cutoff/calibration behavior in [test_dataset_builders.py](../../../tests/modeling/test_dataset_builders.py);
- temporal problem geometry, action availability, strict-deadline outcomes, overflow, and optimum realization in `tests/temporal`;
- prediction target construction, masking, tie behavior, training-state reuse, and decoded-position alignment in `tests/prediction`;
- replay selection and temporal accounting in `tests/evaluation`;
- artifact/corpus semantic compatibility and coverage preflight in [test_artifact_inference.py](../../../tests/modeling/test_artifact_inference.py);
- execution command quoting, provenance, dependency rendering, and primary-error preservation in `tests/execution`;
- exact execution-provenance matching and all-or-nothing collection intent in `tests/benchmarks/test_collection*.py`.

These are domain or externally observable behaviors. Most should survive internal rewrites with smaller fixtures.

### Current tests that should disappear with their interfaces

Delete rather than port tests whose subject is removed:

- catalog SQL schemas, catalog reindex/upsert behavior, remote catalog envelopes, Root Handle constructor shapes, root ledgers/facts, and result-index SQL;
- registry membership, generic owner coercers, representation registry identity, generic batch signatures, and custom sampler object structure;
- exact `Trainer` constructor dictionaries, `TrainingFitPolicy.state_dict`, manual optimizer restoration, and callback invocation order;
- config tests that only enumerate the old command/group surface or snapshot codec internals;
- benchmark tests that require `selection`, `root_facts`, `root_ledger`, JSONL filenames, or the current evaluator/delay matching algorithm;
- serving tests that only assert route registration or a private helper result;
- `core.async_runtime` signal-handler tests if `asyncio.run` owns the interface.

Examples of shallow coverage include [test_training_runner.py](../../../tests/modeling/test_training_runner.py), which replaces both Lightning's module and trainer; [test_staging.py](../../../tests/storage/test_staging.py), where many cases mock the staging context or reindex call; [test_workflow_roots.py](../../../tests/storage/test_workflow_roots.py), which asserts handle projections; and [test_api.py](../../../tests/serving/test_api.py), which does not make a request or enter lifespan. These tests are not evidence for native Lightning resume, crash-safe promotion, direct discovery, or resource cleanup.

## Behavioral invariant ledger

### Finite and best-state behavior

The current contract is explicit in [\_fit_policy.py](../../../src/spice/modeling/_fit_policy.py): a nonfinite metric before any finite best raises; after a finite best it stops and retains that best; every train and validation metric is checked; best state improves only by more than `min_delta`. The candidate's native route changes two of those facts unless approved: Lightning `ModelCheckpoint` tracks the raw optimum, and stock checkpoint callbacks are not finite-gated.

Approve one contract before implementation. Recommended lean contract:

- every complete train/validation metric map must be finite before it is logged as a completed epoch or considered by checkpoint callbacks;
- a nonfinite value fails the current attempt; if a prior finite `last.ckpt` exists, the hidden stage remains resumable and no nonfinite checkpoint is written;
- `best.ckpt` is the raw finite minimum; `min_delta` affects stopping only;
- final validation and test maps are recomputed from a strict reload of `best.ckpt`, checked finite, and persisted in full before promotion;
- failed training never exposes a promoted artifact.

Use two real CPU Lightning tests, not callback mocks: nonfinite on the first validation and nonfinite after one finite epoch. Assert checkpoint contents, stage visibility, best epoch, and error/stop result. A third small test distinguishes raw-minimum checkpointing from `min_delta` stopping.

### Resume behavior

Resume is not one invariant:

- training state: model, optimizer, callback, loop, epoch, and global step resume through `ckpt_path=last.ckpt` with total `max_epochs`;
- sample order: a newly constructed seeded DataLoader generator restarts its permutation sequence; native Lightning resume does not restore that external generator state;
- corpus acquisition: a completed, validated chunk prefix may resume only when exact corpus definition and sanitized source/settings fingerprint match;
- study execution: abandoned `RUNNING` trials may become `FAIL` only while the exclusive application writer lock proves no live writer exists;
- benchmark submission: interruption may occur after `sbatch` succeeds but before local state is replaced, so blindly resubmitting is not safe.

Human approval must choose state-correct/non-bitwise training resume or stateful generator restoration. The simpler state-correct contract is reasonable, but it must be named and tested. Corpus resume needs a real interrupt/reopen test using Parquet chunks; today's fake-sink prefix test is insufficient. Benchmark resume needs an idempotency/reconciliation rule based on a durable submission identity, not merely a mapping file.

### Atomicity, durability, and failure retention

[files.py](../../../src/spice/core/files.py) currently uses temporary files and `os.replace`, while multi-path replacement performs sequential moves with rollback. [lifecycle.py](../../../src/spice/storage/lifecycle.py) pre-checks destination existence before rename. Those implementations do not prove race-free no-replace creation, crash durability, multi-path atomicity, or whole-tree cutover atomicity.

The target contract must separate:

- atomic visibility: readers see old or new complete content;
- crash durability: file data and directory entries survive power/process loss after success is reported;
- immutable conflict: concurrent creation cannot replace an existing different result;
- idempotent equality: an already-existing immutable value may be accepted only after strict equality validation;
- resumable failure: hidden stage remains, promoted destination does not;
- collection preservation: a failed collection leaves the previous `collection.json` byte-for-byte unchanged.

Run failure injection against the real persistence interfaces at: writer exception, partial temporary write, validation failure, destination-created-before-publish race, replace failure, post-rename/pre-directory-sync boundary where testable, collection item N of M, and cleanup failure. Preserve the primary error. Test on the actual local and university filesystem types. Two directory renames are a recoverable cutover protocol, not one atomic switch.

### Provenance and exact-root consumption

Minimum durable provenance:

- corpus: canonical `CorpusDefinition`, stable chain identity, exact requested and resolved range, raw schema version, required source columns/enrichments, sanitized provider alias/reference/fingerprint and settings fingerprint, validation facts, and per-file content inventory;
- study: one immutable namespaced definition attribute plus trial values, params, distributions, states, attributes, and intermediate values;
- artifact: opaque instance ID, effective training definition, source corpus and exact range, feature/problem/prediction semantics, runtime contract, scaler, sequence length, temporal capability, strict weight ABI, optional tuned-trial snapshot, and full validation/test maps;
- evaluation: evaluation ID, parent artifact ID, evaluation corpus ID, chain, evaluator definition, exact window, delay, execution provenance, counts, and results;
- benchmark: plan hash/revision/target, coordinates, exact root references and evaluation IDs, submission attempts, and collected record provenance.

Direct discovery must reject wrong canonical path, kind, ID, chain, parent artifact, manifest mismatch, symlink escape, and malformed content. It must ignore hidden stages. Test same ID on two chains, an evaluation missing its parent artifact address, an equal immutable destination, and a different-content conflict. Dependency-aware deletion must include hidden consumers or require quiescence; a scan followed by deletion is otherwise racy.

### Metric semantics

Current macro-F1 skips classes without target support in [metrics.py](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L76). The proposed TorchMetrics result uses union-active classes, so predicted-only classes contribute zero. This is a deliberate metric change, not a library substitution.

Required metric tests through one scorer interface:

- micro accuracy across uneven batches;
- macro-F1 with one predicted-only class and one entirely inactive class;
- MAE/MSE float64 accumulation on uneven batches;
- separate train, validation, test, and standalone instances with no state leakage;
- NaN/Inf propagation through every metric and loss reducer;
- full-map equality between Lightning epoch scoring and standalone scoring;
- batch-partition invariance if the mathematically exact loss contract is chosen.

The candidate's sample-count-weighted scalar loss preserves today's partition-dependent weighted-cross-entropy reporting. Recommended contract: aggregate true loss numerators and denominators, so weighted cross-entropy divides by target-weight sum and regression by element count. If behavior preservation is preferred, name the metric as batch-partition-dependent and freeze the batch layout.

The 648-window audit must retain raw TP, predicted, and target counts per class. Check both old target-supported and new union-active formulas from those counts. Require 648 unique IDs, 216 per chain, existing sample-count agreement, finite values, exact formula recomputation, frozen input hashes, source/audit revisions, dependency versions, and one dataset-level hash. Do not overwrite the historical collection.

### Serving behavior

Current serving coverage is too shallow. [test_analytics.py](../../../tests/serving/test_analytics.py) exercises one happy path; [test_api.py](../../../tests/serving/test_api.py) only inspects route names; resource construction is lazy and the live client is never closed.

First approve durability, retention, process count, and host count. Then choose the leanest implementation:

- one process, no restart durability: lifespan-owned memory;
- one process, bounded restart durability: strict atomic snapshot, if bounded pending state and rewrite cost are acceptable;
- multiple processes on one host: direct stdlib SQLite;
- multi-host shared state: an external store, only if this is a real product requirement.

WAL is not an automatic improvement. It requires a supported deployed SQLite version and a local, non-network filesystem. The default rollback journal may be simpler for low write volume. `aiosqlite`, SQLModel, and SQLAlchemy add interface/dependency cost without changing the one-table domain contract.

Whatever backend is chosen, test through `TestClient` entering the real FastAPI lifespan: startup failure before readiness, prediction then observation, unknown ID, duplicate observation policy, exact one-row transition, analytics totals/order/retention, restart behavior promised by the selected backend, and shutdown closure of RPC and store resources. Run one real artifact load/predict/observe/analytics smoke without live-chain dependence by injecting the existing external RPC seam.

## Size feasibility and budget

The hard cap requires at least 2,904 net lines removed. The expected range requires 4,354–5,804 net lines removed. The following is a central planning model, not a quota:

| Area | Current | Gross deletion hypothesis | Gross addition hypothesis | Central net |
| --- | ---: | ---: | ---: | ---: |
| Storage/persistence | 5,429 | 3,200 | 1,200 | -2,000 |
| Benchmarks | 2,891 | 1,300 | 500 | -800 |
| Config | 2,333 | 950 | 350 | -600 |
| Modeling + prediction + temporal | 7,744 | 2,100 | 950 | -1,150 |
| Corpus + acquisition | 3,184 | 950 | 350 | -600 |
| Core + CLI + workflows + execution | 3,625 | 500 | 250 | -250 |
| Evaluation + features + serving | 3,660 | 450 | 450 | 0 |
| Package-level files | 138 | 0 | 0 | 0 |
| **Total** | **29,004** | **9,450** | **4,050** | **-5,400 / 23,604 final** |

This model explains why the expected range is possible: most gain must come from deleting persistence/catalog projections, benchmark ledgers/indexes, generic batch/fit glue, and corpus extension machinery. It also shows the risk. If replacement persistence, conversion-friendly records, native-training callbacks, and benchmark state machines recreate those concepts, the route may meet the hard cap but miss the expected range.

Approve budgets only after each replacement interface is sketched. Report by the same stable subsystem grouping, including moved code as a deletion plus addition. Do not count tests, docs, generated files, caches, or temporary audit/conversion tools. Do count durable code added to support migration after cutover; the candidate says temporary migration code is removed.

Use these rules:

- 26,100 is a hard upper gate if the selected interfaces still satisfy all approved invariants;
- 23,200–24,650 is a forecast, not a lower or upper merge target;
- no phase-level numeric quota; require either clear net deletion or an approved deeper interface with a revised whole-route forecast;
- reject compressed formatting, combined unrelated ownership, removed validation, or hidden generated Python as line-count wins;
- recalculate after the persistence, training, and benchmark prototypes, before implementation is authorized.

## Evidence runs that are not ordinary unit tests

These should produce immutable reports with commands, revision, environment, inputs, hashes, repetitions, and raw results. They should not become slow or hardware-sensitive pytest cases.

### Performance baseline

Freeze before deleting the old path:

- acquisition: rows/second, retries, peak memory, and bytes written on a representative exact window plus interrupt/resume;
- Parquet promotion: elapsed time and peak memory for old read/rewrite versus validate/promote;
- tensorization: fixed-context samples/second and peak host memory for each representative sequence length;
- DataLoader/training: epoch samples/second, peak CUDA memory, worker count, pinning, persistence, and prefetch on L40 and `disi_rtx2080`;
- inference: artifact load time, batch throughput, one-window latency, and peak memory;
- discovery/collection: list/resolve/delete-scan and a 648-record collection scan;
- serving: startup time and prediction/observation latency for the approved backend/process model.

Approve relative regression tolerances after the baseline is measured. Do not invent absolute thresholds after the old implementation is gone. Correctness gates remain hard even if the new path is faster.

### CUDA equivalence

Run old and new paths with identical weights and samples for LSTM, Transformer-LSTM, and Transformer, including full and tail batches. Require exact positions and action masks, zero decoded-action mismatches, and `torch.testing.assert_close(atol=1e-5, rtol=1e-4, equal_nan=False)` for every raw output head. Record device, driver, CUDA, cuDNN, Torch, dtype, model config, sequence length, sample hashes, and artifact IDs. Remove the dual-path harness after retaining the report.

### Shared-filesystem and Journal evidence

On both local and university storage:

- record mount/filesystem type and whether stage/destination paths share a device;
- exercise concurrent immutable creation and verify one winner plus one conflict/equal result;
- exercise file and directory replacement, directory sync behavior, and interrupted recovery;
- run two processes against the selected Optuna journal lock, prove writer exclusion, then kill one and prove recovery;
- verify the chosen Journal lock on the actual NFS version, if NFS is used;
- prove study transfer is rejected while a writer is active or produces a coherent locked snapshot.

### Fresh environment

Create an empty environment from the committed lock with `uv sync --frozen`. Record Python and linked SQLite versions. Run package import, CLI help, one local acquire/train/evaluate/collect/load/serve tracer, and `uv lock --check`. Confirm `SQLAlchemy` and `scikit-learn` are absent; confirm direct `torchmetrics` and `optuna-integration` dependencies if imported. Run Ruff, Pyright, pytest, and Vulture there, not only in the developer environment.

### Conversion rehearsal and failure injection

Use mode-restricted SQLite backups and the frozen old revision/lock. Rehearse into a disposable `outputs.next-<id>` and emit:

- source database integrity checks, schemas, row counts, and raw hashes;
- item disposition: import, static archive, or incomplete, with one reason;
- ID maps and collision report;
- corpus file/schema/order/coverage/content hashes;
- study trial count/state/value/param/distribution/attribute/intermediate-value comparison and explicitly accepted timestamp/DB-ID loss;
- artifact tensor key, shape, dtype, and content hashes plus old/new inference probes;
- evaluation corpus proof and exact parent/reference joins;
- benchmark plan/submission/collection referential closure;
- target inventory and whole-tree hash.

Inject one failure in each conversion phase and each cutover state. Prove the active tree remains unchanged before the visibility switch and that the recovery journal selects exactly one old/new tree afterward. Keep quiescence through smoke and rollback. Never automatically delete the old tree.

### CLI, mobile, and Slurm smokes

Final acceptance needs more than import:

- CLI: help plus one exact-ID show/load/transfer path and the acquire → tune → tuned-train → evaluate → benchmark collect tracer;
- mobile: TypeScript check, production bundle/build, launch against the staged API, model-info/predict/observe/analytics flow, and error rendering for unavailable API/expired request;
- serving: process startup enters lifespan and fails readiness on corrupt/missing artifact; shutdown closes resources;
- Slurm: tiny dependency chain proving `afterok`, exact persisted configs/IDs, provenance environment, log path, signal/interruption retention, follow behavior, and resume from the same revision;
- cluster: one L40 route and one `disi_rtx2080` route, including actual CUDA and shared-filesystem evidence.

## Disproved or unsupported candidate claims

- “17 checked-in benchmarks”: 23 exist now.
- “two stock finite-gated ModelCheckpoint callbacks”: Lightning has no such stock finite gate; a first NaN can still be saved.
- native checkpoint resume implies uninterrupted shuffle order: false for a newly constructed DataLoader generator.
- sample-count-weighted batch loss is full-split weighted cross-entropy: false when class weights vary by batch composition.
- strict conversion can populate complete training metric maps from current summaries: false; current [TrainingRuntimeSummary](../../../src/spice/modeling/results.py#L143) stores only validation/test total loss.
- two directory renames make cutover atomic: false; they can be crash-recoverable under quiescence, not one atomic visibility operation.
- removing the acquisition stage record preserves resume provenance: unsupported; the current record is incomplete, but no record permits a different provider/settings context to resume the same bytes.
- WAL is always the lean/correct serving choice: unsupported until process count, filesystem, SQLite version, and workload are approved.
- “22 of 179 university artifacts” is a current inventory: unsupported and conflicts with the repository's last recorded inventory.
- the expected LOC range is evidence-backed: unsupported until replacement-interface budgets are approved.

## Ticket-ready Wayfinder route

### Approve the clean-break behavioral invariant ledger

Type: `wayfinder:grilling` (HITL). Blocked by **Ratify the clean break against accepted architecture decisions**.

Question: Approve the observable behavior that survives the clean break for finite metrics, best-state selection, resume, corpus reuse, atomic visibility, immutable conflicts, provenance, exact-root consumption, metric formulas, benchmark collection, and serving. Explicitly choose raw-minimum versus min-delta-qualified best state, fail-versus-stop nonfinite behavior, state-correct versus uninterrupted-order resume, exact versus batch-partition-dependent loss, and serving durability. Mark implementation shapes such as registries, handles, ledgers, codecs, callbacks, and SQL indexes as non-contracts.

### Freeze the pre-break evidence baseline

Type: `wayfinder:task` (AFK). Blocked by **Approve the clean-break behavioral invariant ledger** and **Run the 648-window macro-F1 impact audit** for the audit portion.

Question: Freeze the exact revision, lock, test/tool results, 29,004-line subsystem inventory, 23 benchmark configs, historical run files and hashes, root inventories/hashes, representative performance measurements, and local/university environment/filesystem facts. Preserve the 648-window audit as a separate immutable dataset with class counts and both formulas. Produce one signed/hash-addressed evidence manifest; do not change production behavior.

### Prove persistence failure semantics on the target filesystems

Type: `wayfinder:task` (AFK). Blocked by the map's **Choose atomic persistence, immutable publication, and direct discovery semantics** decision.

Question: On local and university filesystems, exercise the selected atomic JSON/root primitives, concurrent no-replace creation, equal/conflicting destinations, hidden-stage resume, symlink/canonical-path rejection, directory durability/recovery, dependency deletion policy, and coherent study-journal locking. Record filesystem/mount versions and failure-injection results. Decide any platform-specific fallback before the persistence interface is approved.

### Set an evidence-backed subsystem size budget

Type: `wayfinder:grilling` (HITL). Blocked by the selected persistence/direct-discovery, Lightning/metrics, corpus acquisition, benchmark state, and serving interface decisions.

Question: Re-estimate gross deletions, gross additions, and final LOC from the approved replacement interfaces. Approve the stable counting command, subsystem grouping, 26,100 hard cap, forecast range or its replacement, treatment of moved/generated/temporary code, and the rule for an interface-deepening phase with little net deletion. Reject quotas that reward dense formatting or weakened validation.

### Design the replacement verification suite

Type: `wayfinder:grilling` (HITL). Blocked by **Approve the clean-break behavioral invariant ledger** and the selected interfaces for persistence, training, tuning, benchmarks, and serving.

Question: Map each approved invariant to the smallest test at the deepest public module interface. Identify old tests deleted with their interfaces, scenario tests that replace them, real temporary-filesystem tests, true external fakes, and evidence runs kept outside pytest. Require a lean suite with no architecture-transition, compatibility, internal callback, registry-membership, or old-schema tests.

### Rehearse strict conversion and recoverable cutover

Type: `wayfinder:task` (AFK). Blocked by the final corpus/study/artifact/evaluation/collection schemas, identity/collision policy, **Prove persistence failure semantics on the target filesystems**, and the human conversion eligibility policy.

Question: Repeat local and university inventories from quiesced backups, classify every item, convert into a disposable staged tree, compare hashes/counts/trials/tensors/inference/references, inject failures, and exercise every cutover recovery state without touching active storage. Return the exact eligible/archive counts, capacity requirement, recovery journal, smoke ordering, rollback authority, and retained evidence for human approval.

### Approve the final acceptance matrix

Type: `wayfinder:grilling` (HITL). Blocked by **Set an evidence-backed subsystem size budget**, **Design the replacement verification suite**, **Rehearse strict conversion and recoverable cutover**, the CUDA equivalence evidence, and the selected serving/Slurm contracts.

Question: Review the complete evidence bundle and approve or reject cutover. Require fresh-lock gates, full tests/lint/types/dead-code review, subsystem LOC and dependency proof, performance comparison, CUDA equivalence, shared-filesystem/Journal results, conversion closure, CLI/mobile/serving/Slurm smokes, documentation/ADR disposition, archive retention, rollback authority, and zero unresolved high-severity invariant failures.

## Fog to retain on the map

- Exact replacement test files and counts remain fog until interfaces are selected; pre-slicing them now would encode old seams.
- Performance tolerances remain fog until the old path is benchmarked on both target GPU classes.
- The final expected LOC range remains fog until persistence, training, benchmark, and serving interface sketches yield a reviewed budget.
- University import eligibility, filesystem behavior, archive capacity, and current root counts remain fog until a fresh quiesced inventory.
- The analytics migration test remains fog until durability/backend is approved.
- Exact benchmark submission reconciliation remains fog until the durable attempt identity and Slurm lookup rule are chosen.
- Exact cutover recovery steps remain fog until the filesystem primitive and per-host deployment order are selected.

## Recommended final human approval gates

No implementation/cutover approval should be inferred from this investigation. Require explicit approval for:

1. The invariant ledger, including every deliberate semantic change.
2. Corpus identity/content-collision, root address, immutable conflict, durability, deletion, and journal-lock rules.
3. Best-state, nonfinite, resume-order, loss-reduction, and macro-F1 semantics.
4. Serving durability, retention, process/host model, backend, journal mode, and migration/discard policy.
5. Conversion eligibility, recomputation versus archive, Optuna information loss, archive security/retention, and rollback authority.
6. The post-design subsystem budget and final LOC forecast.
7. The replacement test matrix and external evidence thresholds.
8. The final evidence bundle immediately before per-host cutover.
