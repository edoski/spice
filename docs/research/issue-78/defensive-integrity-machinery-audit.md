# Defensive integrity machinery audit

Date: 2026-07-14. Scope: current code and approved/open clean-break contracts. This is design
evidence only. It changes no production code, issue, graph, data, artifact, or job.

## Verdict and approval boundary

The owner-approved direction is now stronger: **production SPICE computes and persists no
SHA-256, checksum, digest, or source fingerprint**. Keep only identifiers computed by systems that
own their meaning:

- Git commit IDs identify source revisions;
- blockchain block/parent/finalized-anchor hashes identify chain facts;
- already-frozen archival/research checksums remain static custody evidence.

Do not replace deleted SHA fields with CRCs, tree hashes, shortened hashes, byte lengths, content
fingerprints, or a checksum service.

Also approved: use one native Lightning checkpoint as the canonical model artifact, and replace
defensive publication/submission machinery with single-operator/manual handling. Edo explicitly
approved the complete consolidated cross-issue contract below on 2026-07-14. That approval
authorizes this ticket-scoped evidence publication, issue supersession notices, and Wayfinder-map
reconciliation; it authorizes no production, configuration, test, data, storage, acquisition,
training, evaluation, scheduler, archive, or cutover mutation.

The global concurrency rule is manual: at most one live writer for a given UUID. Distinct UUIDs
may run in parallel. SPICE implements no lock, lease, concurrent-writer arbitration, race-proof
publication, exactly-once submission, or automatic recovery.

## UUID corpus identity, without content hashing

Mint a UUIDv4 `corpus_id` before acquisition, like study/artifact/evaluation IDs. Persist one strict
private `CorpusRequest {corpus_id, definition}` as `request.json` before provider work. Before
publication, replace/remove that private request and write direct `corpus.json` containing only the
UUID, exact CorpusDefinition, and minimal finalized-anchor facts.

The corpus owner derives `corpora/<corpus_id>/`, lets Polars discover/decode the Parquet files, and
validates the typed `corpus.json`, exact schema, chain, regime, inclusive range/count, unique
contiguous block numbers, domains, ordering, and finality/ancestry. There is no persisted filename
inventory.
It computes no payload inventory, file digest, byte length, package digest, or same-content
equality.

This changes corpus identity from “these exact compressed bytes” to “this predeclared acquisition
instance.” That is sufficient because one operator creates one immutable result under that UUID,
all scientific consumers bind the UUID plus typed definition/ranges, and every load revalidates
the actual rows. A deliberate reacquisition receives a fresh UUID. There is no deduplication claim.

Resume loads the hidden sibling's typed `request.json` and validates the Parquet prefix against it.
Delete the stage-only `definition_sha256`; the request already carries the exact readable
definition. This preserves the wrong-regime/wrong-range fix from Issue 27 without custom hashing or
duplicated definition columns.

## One native Lightning artifact

Publish the selected Lightning 2.6.5 weights-only best checkpoint unchanged as
`artifacts/<artifact_id>.ckpt`. Put the smallest strict artifact record into the supported native
checkpoint hook/hyperparameter seam: artifact ID, exact TrainRequest, fitted feature/target states,
and approved minimal runtime provenance. Derive model family, C, K, features, loss, corpus, and
selected-study source from the request. Lightning owns checkpoint write/load and strict weight
restoration. SPICE validates only the embedded small Pydantic domain record and its requested
corpus/model association; it implements no checkpoint parser or key/shape/dtype inventory.

Accept Lightning's unavoidable `epoch`, `global_step`, loop state, and version as inert framework
envelope data. A separate `weights.pt`, manifest sidecar, hash, inventory, byte length, custom
serializer, `CheckpointIO`, SQLite store, catalog, or framework-neutral wrapper adds more concepts
than it removes. Lightning documents native checkpoint contents and hooks
([checkpointing](https://lightning.ai/docs/pytorch/stable/common/checkpointing_basic.html),
[hooks](https://lightning.ai/docs/pytorch/stable/api/lightning.pytorch.core.hooks.CheckpointHooks.html)).

During fitting, stock Lightning still keeps two different private files: the selected best and the
broad latest completed-validation checkpoint used by `fit(ckpt_path=...)`. After success, the best
becomes the one canonical artifact; the latest checkpoint remains disposable hidden work. These
are different epochs, not duplicate storage machinery
([ModelCheckpoint](https://lightning.ai/docs/pytorch/stable/api/lightning.pytorch.callbacks.ModelCheckpoint.html)).

## Owner-local hidden siblings

Use one runtime storage root. Add no configured/global private root, scratch-root abstraction,
work-kind enum, status, or lifecycle. A leading dot alone marks unfinished owner-local work:

```text
corpora/.<uuid>/      -> corpora/<uuid>/
artifacts/.<uuid>/    -> artifacts/<uuid>.ckpt
studies/.<uuid>/      -> studies/<uuid>.json
evaluations/.<uuid>.json -> evaluations/<uuid>.json
```

Canonical-path presence means complete. Unfinished bytes never live inside a canonical path. The
operator may inspect or remove hidden siblings manually.

## Lock and concurrency audit

Current production source contains no explicit application mutex, `flock`, advisory-file lock, or
lease. The problematic lock anchors and mount gates exist in approved future contracts, not in an
already-shipped implementation. Delete them before implementation rather than replacing them.

The manual rule is sufficient: one live writer per UUID; different UUIDs may proceed concurrently.
Delete Issue-15/29/30 lock anchors and all NFS lock/capability, exactly-once, and reconciliation
machinery. Delete the old storage lifecycle/transaction/catalog coordinators, Optuna coordination,
and benchmark scheduling/collection coordinators with their approved clean break.

Do not confuse these with useful library behavior:

- if Issue 33 retains durable serving SQLite, use one process/client and the library transaction;
  add no application lock, WAL tuning, busy-timeout policy, or concurrency abstraction;
- `tempfile` plus `os.replace` gives private `progress.json` update visibility without a lock;
- fixed bounded asynchronous acquisition reads are ordinary independent I/O, not writer
  arbitration;
- Lightning, PyTorch, DataLoader, and TorchMetrics may use their own internal synchronization;
- “every eligible origin exactly once” is a scientific traversal invariant, not exactly-once job
  execution;
- `uv.lock` and a “locked runtime” mean pinned dependencies/runtime facts, not a mutex. The file's
  SHA is still deleted from provenance.

Issue-41 quiescence is manual: stop writers, inspect, proceed. Add no quiescence service, global
lock, or proof record.

## Concrete lean machinery

### Publication and transfer

Add no publication helper. After building and validating its hidden candidate, each domain owner
uses ordinary `pathlib` directly:

```python
if destination.exists():
    raise FileExistsError(destination)
candidate.rename(destination)
```

This intentionally relies on the manually enforced one-writer-per-UUID rule. It is not
race-proof. On error, preserve what exists and require manual inspection/delete/retry.

Mutable private `progress.json` may use a standard temporary file plus `os.replace`. Remove fsync
choreography, hard-link/exclusive-rename capability layers, NFS probes/locks, byte equality/no-op,
automatic ambiguous recovery, publication journals, cleanup matrices, and crash-matrix tests.

Typed transfer stays small: resolve the named domain source, let rsync copy it to the corresponding
hidden destination sibling, require the canonical destination absent, then rename. Normal later
loads validate domain facts. Add no destination receipt validation, post-rename reload, digest,
transfer result model, generic kind, replace mode, or recovery engine.

### Submission

Delete the plan concept. One generic seam persists the closed Pydantic `WorkflowRequest` union at:

```text
requests/<workflow>/<destination_uuid>.json
```

Train and Evaluate submit that file directly. Tune uses the same persisted request while candidate
execution remains Issue-29-private. Persistence uses typed equality; JSON byte spelling and a
trailing LF are not identity. Call `sbatch --parsable` once, return/print its numeric job ID, and
pass the ID to `follow`; persist no job fact. Delete intent/job ordinal trees, marker/search bounds,
`squeue`+`sacct` reconciliation, authority/UID proofs, capability gates, automatic restart,
predecessor support, and reconciliation tests. A lost acknowledgement or unknown state stops. The
operator inspects/cancels Slurm work and explicitly reruns only after clearance.

### HPO

Under the global one-live-writer-per-study-UUID rule, remove the
special Tune-request seam, study lock anchor, shared-mount capability gate, sync/no-replace
machinery, and lock-contention tests. `studies/.<uuid>/` contains progress and native candidate
continuation bytes; `requests/tune/<study_id>.json` is authoritative. `run_candidate` updates
`progress.json` with standard temp+replace. `publish_study` validates the
current snapshot, writes `studies/.<uuid>.json`, requires the canonical file absent, renames it,
then leaves hidden work for manual removal. Other study UUIDs may run concurrently.

## What remains and what is deleted

| Mechanism | Result |
| --- | --- |
| Artifact SHA/inventory/length | Delete; owner-approved. |
| Corpus SHA/content inventory/length | Delete; replace with UUID + typed request/direct `corpus.json`/row validation. |
| Stage `definition_sha256` | Delete; typed hidden `request.json` binds resume. |
| Feature-source fingerprint | Delete. Current implementation is [`features/core.py`](../../../src/spice/features/core.py#L186-L212). |
| Endpoint/source-requirement fingerprint | Delete. Current implementation is [`corpus/metadata.py`](../../../src/spice/corpus/metadata.py#L124-L128). |
| Truncated hash-derived storage/evaluation IDs | Delete. Current implementations are [`storage/ids.py`](../../../src/spice/storage/ids.py#L10-L47) and [`storage/artifact.py`](../../../src/spice/storage/artifact.py#L264-L280). |
| Dependency-lock SHA | Delete. Clean Git ID plus actual relevant runtime versions suffice; a commit already identifies its tracked tree ([Git objects](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)). |
| Tensor/result repeat hashes | Delete; compare/report direct typed values and numerical deltas where the evidence question requires them. |
| Git IDs | Retain; Git owns revision identity. |
| Blockchain hashes | Retain; the protocol owns ancestry/finality/head identity. |
| Existing Issue 8/14/20 archival checksums | Freeze as non-runtime evidence only; add no reader/checker/service or new manifest. |

Also delete artifact SQLite/codecs, custom model checkpoint parsers/formats, generic
publication/transfer kernels, and automated Slurm recovery. Trust Lightning for checkpoint
write/load/best/resume, PyTorch for batching/autograd/native nonfinite gradient handling,
TorchMetrics for metric accumulation, Polars for Parquet decoding, rsync for byte transfer,
`sbatch --parsable` for submission, and Pydantic for small domain records. SPICE retains only facts
those libraries cannot know: request/corpus/model association, causal ranges, blockchain
ancestry/finality, and thesis-specific loss/economic mathematics. Do not duplicate framework
validation.

## Amendment map

The following is the exact approved handoff map:

| Issue | Required amendment |
| --- | --- |
| #2 | Retain filesystem observations as research only. Remove NFS lock/rename capability gates as implementation prerequisites; direct rename plus manual recovery is accepted. |
| #10 | Make corpus identity UUIDv4. Add/own the strict pre-work corpus request/constructor; remove the full-SHA identity claim. Train/Tune/Evaluate continue carrying exact corpus UUIDs. Their typed union gains no plan or canonical-byte identity. |
| #11 | Replace content-derived corpus identity/inventory/equality with UUID instance identity, direct `corpus.json`/range/finality validation, and `corpora/<uuid>/`. Replace artifact directory+manifest+inventory with `artifacts/<uuid>.ckpt`. Remove byte-equality rules for UUID objects; existing destination means stop/manual inspection. |
| #13 | Keep direct typed paths/loaders, but remove inventories, equality/no-op/conflict engines, scans used as authority, and generic publication/receipt behavior. Load corpus rows and the native artifact directly. |
| #14 | Keep already-frozen custody checksums as static historical evidence only. Remove new pre/post hash generation and public SHA inventories from active project tooling; Git identifies any committed sanitized bundle. |
| #15 | Replace publication/durability/recovery with direct owner-local `exists`/`Path.rename`, standard private JSON replace, manual recovery, and no per-record deletion API. State the manual one-writer-per-UUID rule; add no publication helper or race arbitration. |
| #19 | Keep direct SSH/revision/`sbatch --parsable`/follow and ordinary rsync. Remove predecessor rendering, artifact/corpus hash receipt, and transfer-publication orchestration. |
| #20 | Preserve its existing frozen archive manifest only outside runtime. Do not propagate archive hashes into clean storage or add another verifier. |
| #27 | Pre-mint corpus UUID; persist typed `request.json`; publish direct `corpus.json`; remove `definition_sha256`, per-file SHA/length inventory, content-derived ID, equality/conflict machinery, sync/capability probes, and hash-based import. Trust Polars decode; keep domain row/header/link/finality validation and provider-owned retry. |
| #29 | Use `studies/.<uuid>/` under the storage root and generic `requests/tune/<uuid>.json`. Under the manual one-writer-per-study-UUID rule remove special request persistence, lock anchor, mount gate, sync/no-replace/equality, and lock tests; keep progress, native continuation, operator curation, and direct rename publication. Distinct studies may run concurrently. |
| #30 | Delete plans. Own only typed request persistence at `requests/<workflow>/<destination_uuid>.json`, direct submit/follow, and manual ambiguity. Use typed equality, not canonical byte/LF identity. Persist no job facts; remove plan/attempt/restart/reconciliation/predecessor/exactly-once contracts. |
| #22 | Keep serving trust/action semantics, but infer no serving lock, transition coordinator, or exactly-once observation mechanism. |
| #33 | If durable serving survives, prefer one ordinary SQLite connection/client and library transactions only. Add no app lock, WAL tuning, busy-timeout policy, lifecycle coordinator, or multi-writer claim. |
| #34 | Freeze one native Lightning checkpoint with embedded minimal typed facts; no custom checkpoint parser, manifest sidecar, weights projection, SQLite, inventory, digest, length, or content-addressed wording. Evaluation remains direct typed JSON. |
| #37 | Acceptance budget removes hash/inventory golden tests, fsync/NFS/crash matrices, Slurm reconciliation matrices, and compatibility checks. Keep one test per deep typed/scientific seam. |
| #38 | Runbook uses UUID corpus requests, simple hidden rename/manual recovery, request-only submission, native checkpoint artifacts, and no hashed-artifact transfer. |
| #40 | Remove “hashed artifact” and deterministic-repeat-hash requirements. Compare direct same-weight outputs/losses/actions and report numerical deltas; transfer/load the native checkpoint. |
| #41 | Conversion/cutover eligibility uses strict typed loaders and operator classification, not hashes. Existing archives remain static evidence; new clean objects receive UUIDs. Quiescence is manual stop/inspection, not a lock, service, or record. |
| #42 | Rehearse the simple hidden-sibling/manual operator flow, not fsync, no-replace capability, content-identity, or automated recovery matrices. |
| #47 | Replace content-bound corpus/per-file SHA wording with corpus UUID plus exact typed chain/regime/schema/range/count/finality validation. Recovery gets a new UUID. |
| #48 | Keep typed exhaustive evaluation mathematics. Frozen research hashes stay research-only; evaluation records and artifact parents gain no digest. |
| #49 | Replace content-bound/reuse/hash language with exact corpus/artifact UUIDs plus typed definition/range/role/request association. Imported prefixes use row/header/link validation, not hashes. Scientific inventory/order is unchanged. |
| #50 | Record exact UUIDs, requests, typed provenance, and scientific results; remove result/artifact hashes and hashed-transfer wording. |
| #62 | Accept the native Lightning weights-only checkpoint as the FP32 model artifact and remove repeat-hash evidence. Broad last checkpoint remains private continuation state. |
| #64 | Replace SHA corpus roots, lock hash, inventories, broad publication kernel, request plans/Slurm reconciliation, custom checkpoint validation, and artifact no-history literal with this contract. |
| #65 | Integration verifies UUID/direct loaders, native checkpoint, direct owner `exists`/rename, request-only submission, typed transfer, and zero old hash/fingerprint/lock/recovery code. Remove crash/reconciliation/inventory/concurrency golden suites. |
| #68 | Closed/superseded brief must not be reused. No replacement publication module is needed; each owner validates then calls direct `exists`/rename. |
| #69 | Closed/superseded brief must not be reused. Replacement acquisition uses corpus UUID+request and direct validation, no project hash/inventory. |
| #72 | Closed/superseded brief must not be reused. Replacement host publishes the native best checkpoint directly and keeps broad last privately. |
| #73 | Closed/superseded brief must not be reused. Replacement evaluation relies on DataLoader/TorchMetrics traversal and keeps the scientific every-origin-once invariant without a job/execution coordinator. |
| #74 | Closed/superseded brief must not be reused. Replacement execution/transfer has no plan: generic typed request file, direct submit/follow, hidden rsync/rename, manual ambiguity. |
| #76 | Target-hardware verification may use framework synchronization needed for correct CUDA measurement, but adds no application lock, repeat hash, persistent coordinator, or execution lifecycle. |
| #77 | Before real acquisition, pre-mint each corpus UUID and persist its exact request. Record definition/range/finality/role sufficiency, not inventory/content identity/provider hashes. |
| Map #1 | Update gists/pointers for all amended contracts and future implementation slices. State explicitly that Git/blockchain/archive hashes remain while production-computed digests do not. |

## Lean verification

- Corpus: one UUID/request/resume/finalize fixture covering wrong definition, schema/range/link/finality
  and hidden-to-canonical rename—no digest vectors or post-publication reload assertion.
- Artifact: one Lightning-native best/last continuation and canonical CPU load/inference fixture—no
  custom parser, manifest/hash/inventory/corruption tests.
- Study: one generic TuneRequest/progress/manual-curation/publish fixture—no special request seam or
  lock/mount/sync tests.
- Requests: one Pydantic typed persist/equal/conflict fixture across Train/Tune/Evaluate—no
  canonical-byte, LF, plan, or job-fact tests.
- Submission: one normal `sbatch --parsable` parse/follow fixture; ambiguous calls raise and never
  retry automatically.
- Transfer: one typed source resolution, hidden rsync candidate, absent rename fixture; normal
  consumers own later loads.
- Repository: `rg` proves no production SHA/digest/fingerprint implementation remains; manually
  confirm Git IDs, blockchain hashes, and frozen research checksums are the only exceptions.
