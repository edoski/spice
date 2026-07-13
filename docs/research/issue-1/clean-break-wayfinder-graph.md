# SPICE clean-break Wayfinder graph

This is a proposed map, not an approved architecture. It deduplicates the candidate route and the six `clean-break-*.md` investigations. No recommendation, existing behavior, or accepted ADR is treated as a decision.

## Map body

### Destination

An owner-approved, dependency-ordered SPICE clean-break specification and execution/cutover runbook. It must preserve approved domain behavior while making the production code materially smaller, leaner, idiomatic, and understandable, with no unresolved design decision left for implementation.

### Notes

Planning only. Production implementation is outside this map; AFK tasks and prototypes exist only to obtain evidence needed for a decision. Every grilling/prototype ticket requires the owner's live approval. Use `/research` for external facts, `/prototype` for concrete comparisons, and `/domain-modeling` when vocabulary changes. Challenge ADRs 0001–0005; never silently retain, amend, supersede, or retire one. Prefer standard public APIs, direct owner functions, real alternatives only, and the lowest total interface/dependency cost. Clean break means no legacy readers, dual writes, compatibility shims, or transition tests. One ticket per Wayfinder session.

### Decisions so far

None.

### Not yet specified

- Exact imported-root eligibility, ID collision/remap tables, and archive capacity depend on the quiesced local/university inventory.
- Exact filesystem fallbacks, Journal lock, and cutover primitive depend on target mount probes.
- Exact performance tolerances and final LOC forecast depend on approved replacement interfaces and frozen baselines.
- Exact maintained-script ports, research extras, collection export columns, and evaluation-suite-data disposition depend on script classification and collection design.
- Exact submission reconciliation depends on the durable attempt identity and supported Slurm lookup surface.
- Exact analytics migration/discard steps depend on the serving trust and durability decisions.
- Exact post-refactor dead-code and old-test deletion lists depend on the replacement interfaces; Vulture is currently clean.
- Exact documentation wording depends on the final ADR and glossary disposition.

### Out of scope

- Production implementation during wayfinding.
- Permanent compatibility readers, dual metrics under one name, dual writes, migration shims, or architecture-transition tests.
- Hydra, an ORM for a one-table service, or a generic plugin/registry without two real implementations and distinct contracts.
- Replacing Optuna only to remove its mandatory transitive SQLAlchemy dependency.
- DDP or multiwriter tuning, a new prediction target, a new economic objective, or Transformer reinitialization.
- A multi-tenant public service if loopback demo is approved; new smart-contract behavior unless the mobile protocol requires it.
- Rewriting frozen historical research methods when an immutable code/input/output bundle is more faithful.

## Ticket graph

`Blocked by: none` means initial frontier. Dependency entries use ticket titles and contain no transitive-only edge.

### Inventory and export the pre-break state

Type: `task` — AFK. Blocked by: none.

## Question

Create read-only, integrity-checked local and university SQLite backups and a sanitized neutral export pinned to the exact old revision and lock. Inventory active roots, hidden stages, backups, benchmark indexes, serving state, duplicate IDs, manifests, trials, schemas, row counts, hashes, filesystem/mount facts, and archive capacity. Record raw-backup security needs without exposing RPC URLs or credentials; do not mutate active state.

### Freeze the total-loss versus economic-objective A/B evidence

Type: `task` — AFK. Blocked by: none.

## Question

Recover the A/B run named in `CLEAN_BREAK_TRACKER.md` and freeze terminal job states, revision, configs, IDs, formulas, joins, metrics, plans, submissions, collections, logs, and hashes. If incomplete, state exactly what is and is not supported; do not rerun under changed semantics.

### Audit remote execution capabilities and the retained Session

Type: `research` — AFK. Blocked by: none.

## Question

Apply the deletion test to the Execution Session and inventory supported local/cluster OpenSSH, rsync, Slurm, and slurmrestd capabilities. Verify `sbatch --parsable`, state/query formats, log/follow races, quoting, SSH-config requirements, transfer, provenance, remote revision, polling cost, and config-size limits. Identify public-CLI replacements without assuming the Session or ADR 0005 survives.

### Classify recipe names, executable discriminators, and domain identities

Type: `grilling` — HITL. Blocked by: none.

## Question

Classify every checked-in config name/id as recipe coordinate, executable branch discriminator, or genuine domain identity. Decide file-name-plus-kind versus `NamedConfig`, recipe provenance, `block_poisson_replay_300`, `ProblemSpec` identity, and every one-implementation selector. Do not approve any registry merely because an ADR or glossary names it.

### Define serving trust, exposure, and observation transitions

Type: `grilling` — HITL. Blocked by: none.

## Question

Choose loopback single-user, trusted-LAN, or public exposure. Define request ownership, rate/bounds, pending expiry, retention, one-time observation transition, retry/idempotency, transaction attestation, analytics visibility, and process/host assumptions. Choose the minimum authentication/authorization that contract needs; an exposed request ID is not authority.

### Prototype one-owner RPC retry and adaptive acquisition

Type: `prototype` — HITL. Blocked by: none.

## Question

Compare JSON-RPC batches with explicit transport backoff against bounded ordinary Web3 calls using public retry on deterministic failures and representative providers. Preserve ordered prefix writes, fee-history alignment, oversize splitting, transient classification, cancellation, adaptive concurrency, counters, and one global attempt ceiling. Choose one delay/backoff owner.

### Choose corpus identity, collision, and finality semantics

Type: `grilling` — HITL. Blocked by: **Inventory and export the pre-break state**.

## Question

Define canonical `CorpusDefinition`, stable chain identity, deterministic ID inputs, requested versus resolved range, source/finality limitation, and same-definition/different-content policy. Compare semantic ID plus per-file hashes, content addressing, and source-fingerprinted identity; explicitly decide reorg proof, block-hash scope, collision handling, and imported corpus remapping.

### Choose output identity, minting, and canonical addresses

Type: `grilling` — HITL. Blocked by: **Choose corpus identity, collision, and finality semantics**.

## Question

Choose study, artifact, and evaluation identity/minting rules; opaque legacy-compatible IDs versus remapping; mint-once and hydration preservation; chain-qualified versus flat paths; and nested versus flat evaluations. Every exact reference and transfer descriptor must locate its target without scanning or a hidden catalog.

### Choose atomic persistence and hidden-stage lifecycle semantics

Type: `grilling` — HITL. Blocked by: **Choose output identity, minting, and canonical addresses**.

## Question

Specify strict Pydantic record IO, atomic mutable replacement, immutable file/root publication, equality-versus-conflict, no-replace fallback, fsync/directory durability, hidden-stage naming/resume, cleanup error precedence, and collection preservation. Distinguish atomic visibility, crash durability, and recoverable multi-step operations; do not call two renames atomic.

### Choose the direct-discovery and storage-owner seam

Type: `grilling` — HITL. Blocked by: **Choose atomic persistence and hidden-stage lifecycle semantics**.

## Question

Choose direct corpus/study/artifact/evaluation owner functions or a small generic store. Define resolve, validate, publish, enumerate, and corruption results while rejecting wrong path/kind/id/chain/parent, symlink escape, malformed content, and hidden stages. The interface must not recreate catalogs, selectors, handles, payload codecs, or root-kind registries without measured leverage.

### Choose dependency deletion, archive, and garbage-collection policy

Type: `grilling` — HITL. Blocked by: **Choose the direct-discovery and storage-owner seam**.

## Question

Choose graph locking, enforced quiescence, or dependency-checked archive-to-trash before manual GC. Cover promoted and staged corpus/study/artifact/evaluation dependents, promotion/delete races, cascade authority, reversible recovery, and final destructive-retention ownership.

### Choose the remote execution control architecture

Type: `grilling` — HITL. Blocked by: **Audit remote execution capabilities and the retained Session**.

## Question

Choose a reduced OpenSSH/rsync/Slurm Session, split transport/scheduler interfaces, or a supported cluster-side/REST/SSH framework. Minimize interface and dependency cost while preserving exact snapshot submission, target paths, provenance, dependencies, follow interruption, transfer staging, errors, and remote revision lookup. Decide ADR 0005 later, not here by inertia.

### Choose root transfer and study snapshot semantics

Type: `grilling` — HITL. Blocked by: **Choose dependency deletion, archive, and garbage-collection policy**; **Choose the remote execution control architecture**.

## Question

Define the smallest exact transfer address/protocol, source and destination validation, equal/no-op versus conflict, partial-transfer cleanup, and primary-error preservation. Decide whether active studies are untransferable, require quiescence/read lock, or produce explicit snapshots; include evaluation parent identity and exclude catalog envelopes.

### Specify the corpus acquisition, resume, and manifest contract

Type: `grilling` — HITL. Blocked by: **Prototype one-owner RPC retry and adaptive acquisition**; **Choose corpus identity, collision, and finality semantics**; **Choose atomic persistence and hidden-stage lifecycle semantics**.

## Question

Specify exact-root reuse, strict partial-stage resume, full staged pull, direct chunked-Parquet validation/promotion, retry ownership, and failure retention. Define the minimal non-secret resume marker and final manifest: definition, source/settings fingerprint, safe provider provenance, coverage, schema/order/row/content facts, and no persisted URLs or credentials. Decide removal of problem-driven acquisition and cross-window extension.

### Prove persistence failure semantics on target filesystems

Type: `task` — AFK. Blocked by: **Choose dependency deletion, archive, and garbage-collection policy**.

## Question

On local and university filesystems, exercise the chosen JSON/root primitives, concurrent create, equal/conflicting destinations, hidden resume, canonical/symlink rejection, fsync/recovery, delete/promotion races, and cleanup failures. Record mount/kernel/filesystem behavior and validate every platform fallback without changing active roots.

### Choose the schema-owned config-file interface

Type: `grilling` — HITL. Blocked by: **Classify recipe names, executable discriminators, and domain identities**.

## Question

Choose the smallest module/API for group metadata, safe YAML, canonical raw show/edit/seed, and typed loading. Preserve the real raw-versus-executable distinction while deciding schema-owned Literal unions versus runtime registries and rejecting Hydra unless a concrete missing requirement justifies it.

### Choose the resolved workflow configuration algebra

Type: `grilling` — HITL. Blocked by: **Choose output identity, minting, and canonical addresses**; **Choose the schema-owned config-file interface**.

## Question

Specify exact Literal-tagged train, tune, and evaluate models, including nested baseline/study training source, complete root addresses, minted outputs, tagged windows, runtime-only fields, and strict hydration. Require one `TypeAdapter` round trip with no owner coercers, resolved-field records, `SerializeAsAny`, structural guessing, or reminting.

### Choose the model-space and tuned-parameter application seam

Type: `grilling` — HITL. Blocked by: **Choose the resolved workflow configuration algebra**.

## Question

Define config-only model/model-space unions, constructor dispatch, stable flat Optuna names, and one pure best-trial application operation. Compare explicit allowlisted applicators with generic path patching; preserve unknown-name rejection, cross-field validation, and explicit Transformer feedforward derivation while removing tuned-parameter models and lazy loaders.

### Choose temporal compiler and action/outcome module boundaries

Type: `grilling` — HITL. Blocked by: **Classify recipe names, executable discriminators, and domain identities**.

## Question

Choose direct interfaces for observed-time temporal compilation and strict-deadline action/outcome realization after removing one-implementation registries and abstract config bases. Preserve geometry, capability metadata, masks, overflow, optimum, and fail-closed persisted versions without combining unrelated temporal, tensor, prediction, or evaluator ownership.

### Choose fixed-sequence tensorization, normalization, and batch ownership

Type: `grilling` — HITL. Blocked by: **Choose temporal compiler and action/outcome module boundaries**.

## Question

Choose direct tensorizer versus narrow function seam, flat training/inference batch records, single action-mask ownership, CPU inference positions, fixed-length assertions, contiguous copying, and strict NumPy population-scaler semantics. Reassess ADR 0003 explicitly; do not restore padding, masks, signatures, or a registry without a real second representation.

### Run the 648-window macro-F1 impact audit

Type: `task` — AFK. Blocked by: **Inventory and export the pre-break state**.

## Question

Produce a separate frozen 648-row audit with per-class TP/predicted/target counts, active-class counts, old target-supported and union-active formulas, deltas, samples, IDs, hashes, revisions, and versions. Require uniqueness, 216 rows per chain, finite/formula/sample agreement, unchanged source hashes, and no rewrite of the historical collection.

### Define shared metric scorer and loss semantics

Type: `grilling` — HITL. Blocked by: **Run the 648-window macro-F1 impact audit**.

## Question

Approve exact metric IDs/formulas, micro accuracy, macro-F1 active-class rule, float64 MAE/MSE, phase isolation, full-map finite behavior, and loss reduction. Choose batch-scalar sample weighting or true numerator/denominator aggregation, define total-loss composition, and require one scorer for Lightning, standalone scoring, conversion, and evaluation.

### Choose training/tuning selection, best-state, and nonfinite semantics

Type: `grilling` — HITL. Blocked by: **Freeze the total-loss versus economic-objective A/B evidence**; **Define shared metric scorer and loss semantics**.

## Question

Approve the metric/formula selecting epochs, stopping, Optuna trials, and pruning: validation loss, economic replay profit, or a deliberately narrow choice. Decide raw-minimum versus min-delta-qualified best, evaluator-primary meaning, one-based epochs, fail-versus-retain-prior-best on nonfinite maps, and persisted selection provenance. Do not infer approval from current code.

### Choose interruption semantics for shuffled training

Type: `grilling` — HITL. Blocked by: **Choose training/tuning selection, best-state, and nonfinite semantics**.

## Question

Choose state-correct/non-bitwise native resume with restarted seeded shuffle permutations or persisted DataLoader generator state matching uninterrupted order. Define the claim and test boundary; native `ckpt_path` does not restore a newly constructed generator.

### Prototype the standard fixed-context DataLoader contract

Type: `prototype` — HITL. Blocked by: **Choose fixed-sequence tensorization, normalization, and batch ownership**; **Choose interruption semantics for shuffled training**.

## Question

Demonstrate that a standard seeded `DataLoader` plus fixed contiguous collation preserves rows, positions, masks, full/tail batches, transfer/pinning, measured worker settings, and the approved resume order while deleting `BatchPlan`, batch signatures, padding, input masks, and the custom sampler.

### Prototype the minimal Lightning checkpoint contract

Type: `prototype` — HITL. Blocked by: **Choose atomic persistence and hidden-stage lifecycle semantics**; **Choose training/tuning selection, best-state, and nonfinite semantics**; **Choose interruption semantics for shuffled training**; **Prototype the standard fixed-context DataLoader contract**.

## Question

Find the smallest automatic-optimization LightningModule/callback design enforcing complete-map finite policy, latest-finite resumable full state, strict best weights, stable stage path, total `max_epochs`, clipping, and exact best value/epoch. Define the `model.` weight ABI and prove stock `ModelCheckpoint` alone is not misrepresented as finite-gated.

### Define Optuna terminal-budget and abandonment semantics

Type: `grilling` — HITL. Blocked by: **Choose training/tuning selection, best-state, and nonfinite semantics**.

## Question

Choose which COMPLETE/PRUNED/FAIL/recovered RUNNING states consume requested work, when RUNNING may become FAIL, retry ceilings, fresh/resumed sampler and pruner construction, and corruption handling for a journal lacking its namespaced immutable definition. Fix one-writer and single-device scope.

### Prototype the Journal study lifecycle and coherent locking

Type: `prototype` — HITL. Blocked by: **Inventory and export the pre-break state**; **Choose atomic persistence and hidden-stage lifecycle semantics**; **Define Optuna terminal-budget and abandonment semantics**.

## Question

On actual target filesystems, prove create/crash recovery, resume, extension, abandoned-trial recovery, one-writer exclusion, coherent best-trial read locking, definition atomicity, and study transfer interaction. Choose append-only promoted study versus hidden-until-terminal and the supported Journal lock.

### Validate per-epoch pruning without trial artifacts

Type: `prototype` — HITL. Blocked by: **Choose the model-space and tuned-parameter application seam**; **Define shared metric scorer and loss semantics**; **Prototype the minimal Lightning checkpoint contract**; **Prototype the Journal study lifecycle and coherent locking**.

## Question

Prove the official Optuna Lightning callback reports every validation epoch, prunes Median trials, records Nop intermediates, retains approved best value/epoch in memory, and emits no test score, manifest, checkpoint, artifact, or artifact stage. Freeze a coherent tuned-training snapshot under the study read lock.

### Prototype the concrete one-family prediction interface

Type: `prototype` — HITL. Blocked by: **Classify recipe names, executable discriminators, and domain identities**; **Choose temporal compiler and action/outcome module boundaries**; **Define shared metric scorer and loss semantics**; **Choose training/tuning selection, best-state, and nonfinite semantics**.

## Question

Compare the callable-heavy generic prediction contract with one Min-Block-Fee task module covering heads, fitted state, targets, loss/scorer, decoding, model construction, evaluators, and serving. Remove one-family registries and generic target/accumulator/result protocols while retaining real feature, model-family, and evaluator alternatives.

### Choose feature compatibility and fingerprint semantics

Type: `grilling` — HITL. Blocked by: **Prototype the concrete one-family prediction interface**.

## Question

Choose explicit semantic feature-contract version plus ordered outputs/requirements, the current source-byte hash, or another minimal compatibility rule. Define compatible changes, software-revision complement, conversion mapping/rejection, and bump ownership; reject both silent formula drift and accidental refactor-only incompatibility unless approved.

### Run the same-weight CUDA model gate

Type: `task` — AFK. Blocked by: **Prototype the standard fixed-context DataLoader contract**; **Prototype the minimal Lightning checkpoint contract**; **Prototype the concrete one-family prediction interface**.

## Question

Run old/new same-weight CUDA comparisons for all three model families on full and tail batches. Require exact positions/masks, zero decoded-action mismatches, raw-head tolerance `atol=1e-5, rtol=1e-4`, and retained device/framework/config/sample/artifact hashes; remove the temporary dual path afterward.

### Specify the artifact manifest, checkpoint, and summary contract

Type: `grilling` — HITL. Blocked by: **Choose output identity, minting, and canonical addresses**; **Choose the resolved workflow configuration algebra**; **Choose the model-space and tuned-parameter application seam**; **Choose training/tuning selection, best-state, and nonfinite semantics**; **Prototype the minimal Lightning checkpoint contract**; **Prototype the Journal study lifecycle and coherent locking**; **Prototype the concrete one-family prediction interface**; **Choose feature compatibility and fingerprint semantics**.

## Question

Specify the immutable artifact schema: exact effective training definition, corpus/range provenance, runtime and software hooks, scaler, sequence length, temporal capability, feature/prediction contract, strict best-weight ABI, full finite validation/test maps, and optional coherent tuned-trial snapshot. Exclude duplicated recipes, runtime controls, and completed-run resume state.

### Specify the evaluation record and ReplayTotals contract

Type: `grilling` — HITL. Blocked by: **Choose the direct-discovery and storage-owner seam**; **Prototype the concrete one-family prediction interface**; **Specify the artifact manifest, checkpoint, and summary contract**.

## Question

Specify immutable evaluation identity/address, artifact and corpus references, chain, evaluator definition, window, delay, execution provenance, counts, typed replay totals, metric metadata/results, finite validation, and merge/extraction behavior. Ensure exact discovery and deletion dependencies without a string-keyed catalog or artifact-local mutation.

### Choose historical and online inference preparation boundaries

Type: `prototype` — HITL. Blocked by: **Choose the resolved workflow configuration algebra**; **Choose fixed-sequence tensorization, normalization, and batch ownership**; **Prototype the concrete one-family prediction interface**; **Specify the artifact manifest, checkpoint, and summary contract**.

## Question

Prototype one-frame historical requested-window preparation and compare a focused online right-edge preparer with a tagged shared interface. Preserve coverage, no-future online behavior, scaling, sequence selection, masks, and compatibility; do not hide two algorithms behind a mode flag merely to claim reuse.

### Choose the labelled Cartesian benchmark language

Type: `prototype` — HITL. Blocked by: **Choose the resolved workflow configuration algebra**.

## Question

Prototype generic labelled axes and retained named categories on a 648-job suite, tune-to-train-to-evaluate suite, and external-ID evaluation suite. Decide defaults, merge/conflict rules, coordinate labels, ordinary problem options, and overrides; cover all 23 files while removing unused step dimensions and special problem grids.

### Choose benchmark data-flow and scheduling semantics

Type: `grilling` — HITL. Blocked by: **Choose output identity, minting, and canonical addresses**; **Choose the labelled Cartesian benchmark language**.

## Question

Decide whether local `study_from`/`artifact_from` implies scheduling, how producer matching works, how explicit existing IDs differ, and how `after` and `slurm_dependencies` separate. Require plan-time zero/multiple-match failure, chain propagation, once-only output minting, and proof every local consumer follows its producer.

### Specify atomic benchmark plans and resumable submissions

Type: `grilling` — HITL. Blocked by: **Choose the remote execution control architecture**; **Choose benchmark data-flow and scheduling semantics**.

## Question

Define the `plan.json` envelope/minimal entry and `submissions.json` attempt state machine: schema, run/target/revision/hash, coordinates, dependencies, exact workflow request, atomic writes, sbatch-success/local-crash reconciliation, retries, authoritative attempt, dependency job recovery, and mixed-revision operator gate.

### Specify exact-ID benchmark collection and minimal remote transfer

Type: `prototype` — HITL. Blocked by: **Choose root transfer and study snapshot semantics**; **Specify the evaluation record and ReplayTotals contract**; **Specify atomic benchmark plans and resumable submissions**.

## Question

Prototype exact evaluation plus deduplicated artifact manifest/summary collection using rsync `--files-from` versus a validated remote bundle. Define strict joins, namespaces, stable ordering, malformed-run policy, artifact deletion dependency, all-or-nothing candidate construction, and byte-preservation of the prior collection on failure; no artifact-root pull or fuzzy evaluator/delay match.

### Classify research scripts and generated benchmark assets

Type: `grilling` — HITL. Blocked by: **Inventory and export the pre-break state**.

## Question

Classify every tracked research script and publication-critical ignored export/figure as maintained tool, frozen historical method, or obsolete one-shot helper. Name public inputs and direct dependencies for maintained tools, immutable archive bundles for frozen work, and decide whether large evaluation-suite YAML is package config or benchmark data.

### Prototype maintained research consumers on clean records

Type: `prototype` — HITL. Blocked by: **Specify exact-ID benchmark collection and minimal remote transfer**; **Classify research scripts and generated benchmark assets**.

## Question

Port one maintained window scanner, CI summarizer, and figure renderer to strict public manifest/collection JSON. Decide metric namespaces, run-level statistical facts, deterministic order, fixture shape, and a minimal research dependency extra before specifying remaining ports/deletions.

### Decide serving analytics durability and storage

Type: `grilling` — HITL. Blocked by: **Define serving trust, exposure, and observation transitions**.

## Question

Choose memory, bounded atomic snapshot, direct stdlib SQLite rollback journal/WAL, aiosqlite, events, ORM, or external storage from the approved restart, retention, process, host, and workload contract. Specify bounds, expiry, exact transition/counter invariants, corruption, locking/offload/connection closure, filesystem/SQLite gates, and old-store import/archive/discard with lowest total cost.

### Define serving resource lifecycle and artifact-chain policy

Type: `grilling` — HITL. Blocked by: **Choose the direct-discovery and storage-owner seam**; **Specify the artifact manifest, checkpoint, and summary contract**; **Choose historical and online inference preparation boundaries**; **Decide serving analytics durability and storage**.

## Question

Specify FastAPI lifespan construction/readiness/cleanup, test injection ownership, RPC/model/store closure, blocking IO offload, exact observation updates, and artifact discovery by complete address. Explicitly approve or reject serving an artifact trained on a chain different from live Sepolia.

### Reconcile confirmed-head inference with the mobile timed-transfer protocol

Type: `prototype` — HITL. Blocked by: **Define serving resource lifecycle and artifact-chain policy**.

## Question

Exercise backend and Expo together and define confirmed head, live head, selected offset, broadcast threshold, target block, TTL, cancellation, receipt observation, RPC disagreement, and metadata/API compatibility. Decide generated OpenAPI types versus one lean contract test and delete the unused contract/address unless an exact event protocol is approved.

### Set dependency, packaging, runtime, and vulnerability policy

Type: `grilling` — HITL. Blocked by: **Prototype one-owner RPC retry and adaptive acquisition**; **Prototype the Journal study lifecycle and coherent locking**; **Validate per-epoch pruning without trial artifacts**; **Classify research scripts and generated benchmark assets**; **Prototype maintained research consumers on clean records**; **Decide serving analytics durability and storage**.

## Question

Approve direct runtime/serving/research/dev dependencies; state the truthful no-SPICE-SQL/no-direct-SQLAlchemy gate despite Optuna's transitive packages; decide aiohttp/eth-typing, TorchMetrics, Optuna integration, Uvicorn extras, and research extras. Include `asyncio.run`, import-time `MPLCONFIGDIR`/version cleanup, wheel/resource/CLI/mobile checks, target locks, and vulnerability triage.

### Define minimal software and runtime provenance

Type: `grilling` — HITL. Blocked by: **Prototype the Journal study lifecycle and coherent locking**; **Specify the artifact manifest, checkpoint, and summary contract**; **Specify the evaluation record and ReplayTotals contract**; **Specify atomic benchmark plans and resumable submissions**; **Set dependency, packaging, runtime, and vulnerability policy**.

## Question

Define one small shared/referenced provenance record for studies, artifacts, evaluations, benchmark evidence, conversion, and audits: schema, SPICE/package version, source revision when available, Python, behavior-critical frameworks, and hardware only where relevant. Define safe logging and exclude secrets, URLs, and duplicated device/config facts.

### Choose conversion eligibility and accepted information loss

Type: `grilling` — HITL. Blocked by: **Inventory and export the pre-break state**; **Specify the corpus acquisition, resume, and manifest contract**; **Define shared metric scorer and loss semantics**; **Prototype the Journal study lifecycle and coherent locking**; **Choose feature compatibility and fingerprint semantics**; **Specify the artifact manifest, checkpoint, and summary contract**; **Specify the evaluation record and ReplayTotals contract**; **Specify exact-ID benchmark collection and minimal remote transfer**.

## Question

Define `import`, `static archive`, and `incomplete` eligibility for every corpus, study, artifact, evaluation, benchmark run, research asset, and serving store. Decide ID remapping, metric recomputation versus archive, Optuna timestamp/database-ID loss, RUNNING trials, evaluation-corpus proof, referential closure, raw-backup security, and fail-closed rules; no partial legacy schema.

### Prototype strict best-checkpoint and summary conversion

Type: `prototype` — HITL. Blocked by: **Choose training/tuning selection, best-state, and nonfinite semantics**; **Choose feature compatibility and fingerprint semantics**; **Specify the artifact manifest, checkpoint, and summary contract**; **Choose conversion eligibility and accepted information loss**.

## Question

On representative eligible roots, prove conversion to the one best-checkpoint ABI with exact tensor keys/dtypes/shapes/hashes and recompute complete finite validation/test maps under the approved scorer. Reject roots whose provenance, split, corpus, feature compatibility, or weights cannot be proven; add no legacy loader.

### Choose recoverable cutover and archive governance

Type: `grilling` — HITL. Blocked by: **Choose atomic persistence and hidden-stage lifecycle semantics**; **Choose dependency deletion, archive, and garbage-collection policy**; **Prove persistence failure semantics on target filesystems**; **Choose conversion eligibility and accepted information loss**.

## Question

Choose per-host two-rename journal, stable pointer, or proven directory exchange; define quiescence through smoke/rollback, deployment order, crash states, recovery authority, capacity, permissions/encryption, archive immutability/retention/deletion owner, and the rule that old storage is never automatically removed.

### Rehearse strict conversion and recoverable cutover

Type: `task` — AFK. Blocked by: **Choose root transfer and study snapshot semantics**; **Prove persistence failure semantics on target filesystems**; **Prototype the Journal study lifecycle and coherent locking**; **Specify exact-ID benchmark collection and minimal remote transfer**; **Prototype strict best-checkpoint and summary conversion**; **Choose recoverable cutover and archive governance**.

## Question

From quiesced backups, convert every item into a disposable staged tree, compare inventories/hashes/trials/tensors/inference/references, inject each phase/cutover failure, and exercise every recovery state without touching active storage. Return exact eligible/archive counts, capacity, whole-tree hash, runbook facts, and unresolved blockers.

### Cross-verify the storage and conversion contract

Type: `grilling` — HITL. Blocked by: **Rehearse strict conversion and recoverable cutover**.

## Question

Review the complete identity, address, persistence, discovery, corpus, Journal, artifact, evaluation, transfer, deletion, conversion, and cutover decisions as one contract. Resolve contradictions, confirm no catalog/compatibility layer reappears, and approve the storage/conversion specification and dependency order or reopen named tickets.

### Cross-verify the modeling and tuning contract

Type: `grilling` — HITL. Blocked by: **Validate per-epoch pruning without trial artifacts**; **Run the same-weight CUDA model gate**; **Prototype strict best-checkpoint and summary conversion**.

## Question

Review configuration application, fixed data flow, scorer, selection, Lightning, Optuna, prediction, feature compatibility, artifact ABI, CUDA, and conversion evidence as one contract. Resolve semantic/interface conflicts, confirm framework APIs replace glue without weakening checks, and approve the modeling/tuning specification or reopen named tickets.

### Cross-verify the workflow, benchmark, and research contract

Type: `grilling` — HITL. Blocked by: **Prototype maintained research consumers on clean records**; **Define minimal software and runtime provenance**.

## Question

Review config files, workflow snapshots, benchmark language/edges/plan/submission/collection, research consumers, packaging, and provenance as one contract. Prove exact IDs and coordinates flow once, state is resumable and auditable, public research inputs are sufficient, and approve the specification/order or reopen named tickets.

### Cross-verify the acquisition, serving, and execution contract

Type: `grilling` — HITL. Blocked by: **Choose the remote execution control architecture**; **Specify the corpus acquisition, resume, and manifest contract**; **Reconcile confirmed-head inference with the mobile timed-transfer protocol**; **Set dependency, packaging, runtime, and vulnerability policy**; **Define minimal software and runtime provenance**.

## Question

Review RPC acquisition, corpus handoff, remote execution, inference, serving trust/storage/lifespan, mobile timing, package/runtime, and safe provenance as one slice. Resolve boundary and deployment contradictions, choose the leanest approved interfaces, and approve the specification/order or reopen named tickets.

### Approve ADR dispositions and the post-break glossary

Type: `grilling` — HITL. Blocked by: **Cross-verify the storage and conversion contract**; **Cross-verify the modeling and tuning contract**; **Cross-verify the workflow, benchmark, and research contract**; **Cross-verify the acquisition, serving, and execution contract**.

## Question

For ADRs 0001–0005, explicitly choose retain, amend, split, supersede, or retire and link each surviving principle to an approved contract. Rewrite the proposed `CONTEXT.md` vocabulary around genuine domain/workflow concepts, retire implementation inventory terms, set a glossary budget/rule, and choose concise normative versus historical documentation. Do not silently overwrite ADR history.

### Design the replacement verification and evidence suite

Type: `grilling` — HITL. Blocked by: **Approve ADR dispositions and the post-break glossary**.

## Question

Map each approved invariant to the smallest test at the deepest public module, name old shallow tests deleted with their interfaces, and separate pytest from immutable hardware/filesystem/performance/conversion evidence. Require real CPU Lightning/lifespan/filesystem tests, true external fakes only, wheel/CLI/mobile/Slurm smokes, and no compatibility or architecture-transition tests.

### Set the evidence-backed size and documentation budget

Type: `grilling` — HITL. Blocked by: **Approve ADR dispositions and the post-break glossary**.

## Question

Re-estimate gross deletion, gross addition, and final LOC from approved interfaces. Approve the counting command/grouping, 26,100 hard cap, forecast range or replacement, moved/generated/temporary treatment, dependency gates, documentation set, and rule for an interface-deepening phase with little deletion. Reject dense formatting or weaker validation as savings.

### Freeze the complete pre-implementation evidence baseline

Type: `task` — AFK. Blocked by: **Freeze the total-loss versus economic-objective A/B evidence**; **Prove persistence failure semantics on target filesystems**; **Run the 648-window macro-F1 impact audit**; **Run the same-weight CUDA model gate**; **Prototype maintained research consumers on clean records**; **Rehearse strict conversion and recoverable cutover**.

## Question

Assemble one hash-addressed evidence manifest containing revision/lock, tests/tools/LOC, inventories, historical and A/B data, macro-F1, filesystem/Journal, conversion rehearsal, representative old-path performance, CUDA, research assets, environments, and raw report locations. Fill missing baseline measurements before old paths disappear; change no production behavior.

### Specify the implementation order and acceptance/cutover runbook

Type: `grilling` — HITL. Blocked by: **Design the replacement verification and evidence suite**; **Set the evidence-backed size and documentation budget**; **Freeze the complete pre-implementation evidence baseline**.

## Question

Produce tracer-bullet implementation phases ordered by dependency and cutover risk, with each phase's approved interface, deletion boundary, focused verification, evidence artifact, rollback point, and reforecast rule. Define final fresh-lock, lint/type/test/Vulture, LOC/dependency, performance, CUDA, filesystem/Journal, conversion, CLI/mobile/serving/Slurm, docs/ADR, archive, and rollback gates without implementing them.

### Approve the final clean-break specification and execution order

Type: `grilling` — HITL. Blocked by: **Specify the implementation order and acceptance/cutover runbook**.

## Question

Review the complete clean-break specification, evidence, unresolved-risk register, implementation order, acceptance matrix, conversion/cutover runbook, and explicit out-of-scope list. Approve it for implementation, reject it, or reopen named decisions. Approval here is the only map-level authorization; it does not itself supersede ADRs or mutate production/storage.

## Graph audit

- Tickets: 60.
- Initial frontier: 6 — **Inventory and export the pre-break state**; **Freeze the total-loss versus economic-objective A/B evidence**; **Audit remote execution capabilities and the retained Session**; **Classify recipe names, executable discriminators, and domain identities**; **Define serving trust, exposure, and observation transitions**; **Prototype one-owner RPC retry and adaptive acquisition**.
- Types: 39 grilling, 12 prototype, 8 task, 1 research.
- Modes: 51 HITL, 9 AFK.
- Maximum direct blockers: 8, on **Specify the artifact manifest, checkpoint, and summary contract** and **Choose conversion eligibility and accepted information loss**.
- The graph is acyclic. Every ticket reaches **Approve the final clean-break specification and execution order**.
