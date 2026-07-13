# SPICE clean-break persistence semantics

Research date: 2026-07-10. Scope: the candidate clean-break plan's storage, identity, discovery, corpus acquisition, transfer, deletion, serving SQLite, export, conversion, and cutover proposals. Local claims refer to the current checkout at `b9b9a53`; external claims cite the owning project's documentation or specification.

## Findings

### The present design is coupled through derived IDs, a catalog, and mutable root databases

SPICE currently derives corpus, study, artifact, and evaluation identifiers from configuration rather than minting instance identifiers. Corpus IDs include the chain, corpus name, and timestamps (`src/spice/storage/ids.py:13-47`); study and artifact identity payloads include large configuration fragments (`src/spice/storage/identity.py:31-56`). `WorkflowRootMaterializer` computes these identities, resolves exact catalog records, and dispatches root creation (`src/spice/storage/workflow_root_materialization.py:75-190`).

The catalog is not merely a list command. It is the current discovery and dependency index: materialization validates path/manifest agreement (`src/spice/catalog/materialization.py:42-98`), scanning deliberately ignores hidden stage directories (`src/spice/catalog/index.py:229-242`), and deletion queries catalog dependencies before removing a root (`src/spice/storage/lifecycle.py:160-280`). Transfer also resolves and publishes catalog records (`src/spice/execution/transfer_transaction.py:157-267`; `src/spice/storage/sync_cli.py:36-79`). Removing the catalog therefore requires an explicit replacement contract for discovery, validation, dependency scans, transfer addressing, and collision reporting, even if that replacement is only a few direct functions.

The root databases are mutable. Artifacts receive evaluation rows after training (`src/spice/storage/artifact.py:133-164`; `src/spice/storage/transactions.py:139-150`), and Optuna studies are resumed in the same RDB (`src/spice/storage/study_optuna.py:31-91`). Artifact staging currently uses a deterministic hidden directory, reuses it after failure, and publishes with replacement enabled (`src/spice/storage/transactions.py:104-123`). The candidate rule that every promoted root is immutable conflicts with resumed JournalStorage studies unless studies are declared append-only mutable or remain hidden until terminal completion.

The earlier ADRs describe this coupling as intentional. ADR 0001 requires exact root IDs and manifest-first validation but also says older roots should be regenerated instead of migrated (`docs/adr/0001-root-id-consumer-workflows.md:15-31`). ADR 0004 argues that root materialization, selectors, and handles must remain (`docs/adr/0004-compiler-materialization-existing-root-vocabulary.md:9-29`). ADR 0005 retains the custom SSH/rsync/Slurm session and catalog envelopes (`docs/adr/0005-custom-execution-session-retained.md:9-23`). The clean break changes the premises behind ADR 0004: minted IDs and direct paths eliminate much of the config-derived identity and global-ledger work. ADR 0001's exact-ID and manifest-first principles still fit, while its catalog mechanism and no-migration statement do not. ADR 0005's execution session can remain while its catalog envelope is superseded. These are architectural reversals and need an explicit human approval gate, not silent drift.

### Identity needs separate semantic and instance rules

The proposed deterministic `CorpusDefinition` and UUID study/artifact IDs are coherent only if the ID type is an opaque string and UUID is a minting policy. Phase 6 also proposes preserving legacy `art_...` and `std_...` values. A UUID-validated field cannot preserve those values; the alternatives are to remap legacy IDs and rewrite every reference, or accept opaque legacy IDs alongside UUIDs.

The corpus definition needs a canonical answer for `chain`: display name, stable chain ID, or full chain runtime configuration. It also needs a collision policy. If provider, resolved block boundary, and content hashes are excluded, two acquisitions can have the same semantic ID but different bytes after an RPC reorganization or provider change. Credible contracts are:

1. Keep a semantic corpus ID, store a per-file SHA-256 inventory, and reject a same-ID/different-content promotion or transfer.
2. Make the corpus ID content-addressed, accepting that the ID is unknown until acquisition finishes.
3. Include sanitized source and resolved-range fingerprints in the definition, reducing reuse but making identity more operational.

The first is the smallest clean break. It requires the manifest to carry a format version, canonical definition, exact resolved range, and content inventory. Structural Parquet/checkpoint validation without hashes is a credible lower-cost alternative, but it cannot distinguish equal definitions with different bytes during transfer or conversion.

### Direct discovery is viable, but `{kind, id, chain}` is not yet a complete address

Corpus, artifact, and study roots can be validated at their canonical paths. Evaluation files are proposed as `evaluations/<chain>/<artifact_id>/<evaluation_id>.json`, so `{kind, id, chain}` lacks the `artifact_id` needed to locate one without scanning. Evaluate configuration currently contains artifact and corpus IDs but no chain or explicit evaluation ID (`src/spice/config/models.py:634-648`). Either the evaluation transfer descriptor must include `artifact_id`, evaluation layout must become directly addressable by evaluation ID, or evaluation transfer must be excluded in favor of a separate exact fetch operation.

Direct discovery also needs defined behavior for duplicate IDs across chains, symlink escapes, hidden stages, a wrong manifest ID/chain/kind, and malformed roots. Two credible seams are:

1. Owner modules expose `resolve`, `validate`, `publish`, `scan_dependencies`, and `delete`; callers use plain paths and models.
2. A small typed `RootStore`/`RootRef` repository centralizes those operations without a global catalog or SQLAlchemy.

A generated read-only JSON index can later accelerate operator listing, but it should not be a source of truth. At current scale, requiring it before measuring discovery is unnecessary.

### Atomic visibility, crash durability, and no-replace are different requirements

SPICE's JSON writer writes a temporary file and calls `os.replace`, and its multi-path publisher checks destinations before sequential replacements (`src/spice/core/files.py:13-58`). Lifecycle root promotion similarly checks and renames (`src/spice/storage/lifecycle.py:58-100`). Those operations do not supply an atomic no-replace primitive, and the pre-check can race another writer.

Python documents that a successful same-filesystem `os.rename`/`os.replace` is atomic, and that cross-filesystem moves may fail ([Python `os.rename`](https://docs.python.org/3/library/os.html#os.rename)). Atomic directory-entry visibility is not a complete crash-durability protocol: SPICE should explicitly flush file content and the containing directory before considering a promotion durable. For immutable destinations, Linux `renameat2(RENAME_NOREPLACE)` rejects an existing target and `RENAME_EXCHANGE` atomically swaps two existing paths, but support is Linux/filesystem dependent; the Linux manual also warns that an NFS rename may have happened even when the client observes failure ([Linux `renameat2(2)`](https://man7.org/linux/man-pages/man2/renameat2.2.html)).

Publication therefore needs separate tested primitives for a file and a root directory, plus a documented fallback on filesystems without `RENAME_NOREPLACE`. An existing immutable destination should be validated as equal and treated as an idempotent no-op, or reported as a conflict; it should never be silently replaced.

### Acquisition can become much smaller, but resumable provenance cannot disappear

The acquisition `problem` is compiled but source requirements use only the feature contract (`src/spice/corpus/planning.py:16-72`), so removing it is supported. Full split materialization currently reads chunked Parquet into one frame and writes it back (`src/spice/corpus/split_materialization/_materializer.py:285-317`; `src/spice/corpus/split_materialization/_parquet_io.py:144-176`). The pull sink already writes resumable chunk prefixes and validates them (`src/spice/corpus/split_materialization/_parquet_io.py:38-79,351-390`). Directly validating and promoting those files removes a redundant full-data read/write. The one-value split kind/intent/spec and cross-window extension paths can also disappear; transient RPC retry remains a separate requirement (`src/spice/acquisition/pull.py:179-267`).

The current stage record identifies chain, corpus, window, and stage ID but not provider or settings (`src/spice/corpus/acquisition_stage.py:65-90,166-187`). If that record is simply removed, a partial stage can resume under a different provider/settings while the final manifest claims only the latter. The clean alternatives are:

1. Keep a tiny strict hidden resume marker containing the corpus definition plus a non-secret source/settings fingerprint; reject mismatches.
2. Put the source/settings fingerprint in `CorpusDefinition`, making it part of the corpus ID.
3. Permit mixed acquisition provenance and record an ordered segment/event list, which is more machinery than the clean break warrants.

The first preserves semantic corpus reuse and is the recommended choice. The fingerprint must derive from a sanitized user-authored provider alias and non-secret adapter settings. Resolution currently falls back from an explicit reference to the raw endpoint URL (`src/spice/config/resolution.py:261-265`), and the manifest stores that reference plus a full-URL hash (`src/spice/corpus/metadata.py:181-186`). Raw snapshots must therefore be treated as sensitive; a sanitized conversion bundle must not copy endpoint URLs or credentials.

### Dependency deletion is a concurrent graph operation

Replacing catalog dependencies with manifest/study-attribute scans preserves correctness only if promotion and deletion cannot race. A corpus can pass a dependency scan just before a new artifact is promoted. An active hidden stage can also be consuming a root without a promoted manifest. Studies are mutable, so their definition attributes need a read lock while being scanned.

Credible lifecycle policies are:

1. Lock the affected dependency graph, scan promoted and staged consumers, default to block, and require an explicit cascade flag.
2. Permit deletion only during an operator-enforced quiescent/offline window and never cascade automatically.
3. Atomically move eligible roots to a hidden archive/trash and make destructive garbage collection a separate manual operation.

The third is a missed simplification: it makes mistakes reversible and narrows immediate deletion logic, although dependency checks are still required. Separate evaluation JSON files create a new artifact dependency and need an explicit block/cascade/archive rule. Current evaluations are embedded in the artifact database and disappear with it (`src/spice/storage/artifact.py:133-164`).

### Descriptor-only transfer needs immutable conflict and study-quiescence rules

The custom execution session can remain. The catalog record envelope can be reduced to a typed descriptor plus manifest validation at both ends. Destination existence must mean equal/no-op or conflict, never replacement. A study journal cannot be copied consistently while writers append to it; study transfer must be disallowed while active, performed under quiescence, or defined as an explicit snapshot. Evaluation descriptors need the parent artifact identity as noted above.

### The old-state export must be broader than `outputs/`

The workspace audit found eight canonical artifact databases and five canonical corpus databases under `outputs`, plus `outputs/.spice/catalog.sqlite`. Persistence also exists outside that tree: `benchmarks/results.sqlite` and `.spice/serving.sqlite`; the latter had eight observation rows and used the default delete journal mode at audit time. Backups, hidden stages, and manifest-backup directories also exist. These observations are local-state evidence, not claims about the university host, whose inventory must be repeated.

Python's SQLite backup API creates a database backup even while other clients access the source ([Python `Connection.backup`](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup)). Each database snapshot can be internally consistent while the set of snapshots is not one cross-root point in time. The early export can support rehearsal, but the final cutover export must quiesce all writers or accept and label that limitation.

The export should be pinned to the exact pre-break commit and frozen dependency lock, record Python/SQLite/Optuna versions, run `PRAGMA integrity_check`, record schema/table/row counts and SHA-256 for every raw snapshot, and decode a neutral JSON/Parquet bundle before old readers are deleted. Keep raw snapshots mode-restricted and preferably encrypted; retain only sanitized provider aliases in the neutral bundle. A human must approve raw-backup location, retention, and deletion.

### Strict conversion cannot synthesize complete training metrics

Current `TrainingRuntimeSummary` stores row/split counts, best epoch, best validation total loss, and test total loss (`src/spice/modeling/results.py:135-152,230-248`). It does not contain complete validation/test metric maps. A converter cannot truthfully populate the proposed strict target model from that source alone. The choices are:

1. Archive artifacts lacking complete maps and import none of them as first-class new artifacts.
2. Recompute maps from the preserved model, corpus, manifests, and pinned old code, with exact sample-count and output checks.
3. Add a partial/nullable converted-summary variant, which violates the candidate's single strict contract.

The first is strictest and simplest; the second preserves more data but is an auditable recomputation project. It needs human approval before implementation.

Evaluation IDs are currently deterministic only inside an artifact database (`src/spice/storage/artifact.py:264-280`), so the conversion key must be `(source_host, artifact_id, old_evaluation_storage_id)`. The current evaluation runtime model omits evaluation corpus ID (`src/spice/modeling/results.py:198-227`); a benchmark plan/collection join may prove it, but coverage equality alone does not. Unprovable evaluations should be archived, not guessed. Benchmark plan, selected submissions, and collection references must be rewritten together or the whole run remains a static archive.

Optuna publicly supports constructing a trial with state, objective values, parameters, distributions, attributes, and intermediate values, then adding evaluated trials to a study ([Optuna `create_trial`](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.trial.create_trial.html), [Optuna `Study.add_trial`](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.study.Study.html#optuna.study.Study.add_trial)). `create_trial` has no trial-number or timestamp arguments, so public-API replay can preserve ordered trial numbers only by adding trials in order; it cannot preserve database trial IDs or original timestamps. This loss must be accepted explicitly. Conversion should fail on active `RUNNING` trials after quiescence, or archive the study as incomplete.

`JournalFileBackend` is documented as unsuitable for high write concurrency, and accepts a pluggable lock ([Optuna `JournalFileBackend`](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.storages.journal.JournalFileBackend.html)). `JournalFileOpenLock` is specifically documented for NFSv3 or later and uses `O_EXCL`; older NFS requires the symlink lock ([Optuna `JournalFileOpenLock`](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.storages.journal.JournalFileOpenLock.html)). The target filesystem type and lock behavior must be measured before hardcoding a journal lock.

### The macro-F1 audit is a new frozen dataset, not a reinterpretation of the old collection

The historical run at `outputs/benchmarks/runs/lstm_36s_wall_clock_quartile_eval/20260628T131456Z` contains 648 plan records, 659 submission records, and 648 collection records. The current loader rejects the raw plan because historical `selection.objective` is not accepted by the current model (`src/spice/benchmarks/_run_state_codec.py:134-147`; `src/spice/benchmarks/_models.py:38-56`). Source files must remain byte-for-byte unchanged; a normalized derivative may strip only the known obsolete field and must record both hashes.

The historical collection has only three distinct macro-F1 values, one per chain, because it copied artifact training-test metrics rather than recomputing each evaluation window. Current collection construction no longer copies macro-F1 (`src/spice/benchmarks/result_records.py:101-125`). The 648-window audit must therefore emit fresh per-window records containing per-class true-positive, predicted, and target counts; target-supported, union-active, and predicted-only class counts; old/new scalar values and delta; expected/observed sample counts; run/window/artifact/corpus IDs; payload hashes; source and audit commits; dependency versions; and an overall dataset hash.

Current SPICE macro-F1 skips classes whose target count is zero (`src/spice/prediction/metrics.py:76-94`). The installed TorchMetrics behavior was independently checked against the count formula; its official multiclass F1 API documents macro averaging across class scores ([TorchMetrics multiclass F1](https://lightning.ai/docs/torchmetrics/stable/classification/f1_score.html)). The audit should store the raw counts and compare both formulas, rather than trusting either scalar alone. It should cache artifact/corpus loads per array job so the audit measures metric computation instead of repeatedly loading identical payloads.

### Serving SQLite needs explicit ownership

`ServingAnalyticsStore` opens a connection per operation and uses `with self._connect()` (`src/spice/serving/analytics.py:29-33,214-217`). Python documents that a SQLite connection context manager commits or rolls back but does not close the connection ([Python sqlite3 context manager](https://docs.python.org/3/library/sqlite3.html#how-to-use-the-connection-context-manager)). These connections are therefore left to garbage collection. `record_observation` also does not inspect the update cursor's row count (`src/spice/serving/analytics.py:89-118`), although Python exposes the number of modified rows for `UPDATE` through `Cursor.rowcount` ([Python `Cursor.rowcount`](https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor.rowcount)).

SQLite WAL mode persists after it is set ([SQLite WAL persistence](https://www.sqlite.org/wal.html#persistence_of_wal_mode)), while `busy_timeout` installs a handler on a particular connection ([SQLite `PRAGMA busy_timeout`](https://www.sqlite.org/pragma.html#pragma_busy_timeout)). A connection-per-operation design should therefore close with `contextlib.closing` and set the timeout on every connection. A single lifespan-owned connection is also credible, but Python defaults to same-thread use and requires explicit serialization if sharing is enabled ([Python `sqlite3.connect`](https://docs.python.org/3/library/sqlite3.html#sqlite3.connect)). Adding `aiosqlite` is not justified for this small store.

The API lazily constructs the service without a lifespan (`src/spice/serving/api.py:23-26,79-84`), while the live RPC client exposes `async close` (`src/spice/serving/live_blocks.py:43-44`). FastAPI's lifespan runs setup before accepting requests and cleanup after request handling, and is its recommended startup/shutdown mechanism ([FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)). Build the service once there, close the live client, and close analytics only if the chosen design holds a persistent connection. The current default `.spice/serving.sqlite` (`src/spice/serving/config.py:13-16`) also conflicts with the candidate `outputs/serving/analytics.sqlite`; cutover must import, archive, or explicitly discard the old file.

### Two renames do not make one atomic cutover

The candidate sequence “rename old outputs, then rename staged outputs” contains two individually atomic operations with a visible/crash gap between them. It must not be called atomic. Credible choices are:

1. Quiesce writers/readers and use two renames plus a durable cutover journal and tested recovery procedure. This is crash-recoverable, not atomic.
2. Store versioned roots and atomically replace one stable symlink/pointer. This gives one visibility switch but requires every consumer to resolve the pointer correctly.
3. On a proven supporting Linux/filesystem pair, atomically exchange two existing directories with `renameat2(RENAME_EXCHANGE)` and then archive the old tree.

Local and university hosts cannot switch as one filesystem transaction. The cutover needs a per-host state machine, deployment ordering, smoke-test gate, and rollback authority. Quiescence must continue through smoke tests: rolling back after new writes would otherwise discard them. Archive immutability also needs a real policy—permissions, snapshot, or external/object storage—and an explicit retention owner. Merely renaming to `outputs.pre_clean_break.*` is a convention, not an immutable external archive.

## Recommended decision gates

Human approval is required before:

- choosing opaque legacy-compatible IDs versus full UUID remapping;
- selecting semantic corpus identity and its content-collision rule;
- declaring studies append-only mutable versus hidden-until-terminal;
- superseding ADRs 0001, 0004, and the catalog portion of 0005;
- selecting lock-guarded deletion, offline deletion, or archive-then-GC;
- accepting Optuna timestamp/database-ID loss and deciding how `RUNNING` trials are handled;
- archiving versus recomputing artifacts with incomplete metric summaries;
- selecting the remote journal lock after filesystem tests;
- selecting the per-host cutover primitive, rollback authority, and archive retention/security policy.

Remaining fog is factual, not a reason to preserve legacy code: university inventory and filesystem semantics, cross-host same-ID/different-content collisions, old-to-new corpus many-to-one collisions, the count of evaluations with provable corpus identity, the count of artifacts eligible for strict import, and available archive capacity. Resolve those with inventories and rehearsal before writing the converter or cutover code.
