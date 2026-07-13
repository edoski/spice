# Issue 27 dependent completeness audit

Status: dependent audit complete; all four original and three reconciled independent decisions
are explicitly approved, as are the original and corrected complete recaps. This audit
performs no acquisition or production/data mutation. The derived edge `#27 blocks #34` was
separately authorized, completed, and verified by the orchestrator/map owner rather than this
thread.

## Approval receipt

On 2026-07-13 Edo explicitly approved:

1. no separate resume marker; use the validated private Parquet prefix;
2. provider-only retry/backoff, with zero acquisition retries and no persisted retry fact;
3. block/parent hashes only in private staging, omitted from finalized rows;
4. full fresh source validation for hashless existing Parquet, with reacquisition on failure;
5. the complete recap then presented in `implementation-map.md`.

The dependent audit preserved that receipt. After its failing definition-mismatch probe and
Edo's pushback reconciliation, Edo also explicitly approved:

6. one constant stage-only `definition_sha256`, equal to the lowercase full SHA-256 of the
   strict canonical JSON bytes of the entire `CorpusDefinition`; exact equality is required
   before resume and the field is stripped from final payload. Readable regime name/start stay
   in the trusted request and final manifest only, never raw/model payload;
7. a chain-generic Issue 27 interface; the already-approved Issue 49 downstream plan invokes
   one Ethereum definition and one Polygon definition, with no Avalanche invocation;
8. priority fees deferred from the current baseline with no Issue 27 machinery. A later
   authorized map pass retains one Wayfinder fog line and removes the contradictory
   out-of-scope duplicate; a fresh concrete ticket is created only after preprocessing,
   training, evaluation, and serving stabilize.

Edo then explicitly approved the corrected complete Issue 27 contract below exactly as recapped
on 2026-07-13. He separately authorized wiring the derived native edge `#27 blocks #34` and
assigned that mutation and verification to the orchestrator/map owner, which completed and
verified it. This owned thread did not duplicate it.

## Approved definition binding

An OS-temp probe acquired `regime-a` blocks 100–103, then inspected the same private files as
`regime-b` blocks 100–105. The old validator accepted them at block 104 and acquisition
silently extended through 105. `chain_id` and row numbers cannot prove the regime name,
regime start, or original last block. This violates exact-definition resume, wrong-regime
rejection, and the ban on cross-window extension.

The approved correction adds exactly one `String` column to every private stage row:
`definition_sha256`. Its value is the full SHA-256 of the complete definition encoded alone as:

```python
json.dumps(
    definition_payload,
    ensure_ascii=True,
    allow_nan=False,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")
```

Every existing stage row must contain the same valid lowercase digest and match the requested
definition before any provider read or stage write. Finalization drops it with block/parent
hashes. The request and final manifest still carry readable `regime.name` and
`regime.start_block` because Issue 11 makes them trusted recipe facts and Issue 47 makes them
containment metadata; raw/model rows do not. This adds no readable regime column, marker,
definition-keyed path, footer contract, registry, lifecycle, counter, compatibility field, or
final-payload duplicate.

## Audit-derived corrections

These follow from already-approved contracts and add no owner design branch:

- Finalization must stream stage rows into one fixed, non-runtime canonical Parquet geometry
  and fixed writer settings. Runtime acquisition/import chunk boundaries cannot change the
  inventory or corpus ID. Issue 34 freezes the production geometry and payload fields.
- Validate exact source keys/types/requested number/chain/domain/hash as each call completes,
  then validate parent/timestamp links in write order before buffering for output. If one
  `asyncio.wait` completion set includes a terminal result, write none of that set's successes
  before observing the terminal result; cancel every sibling.
- Require positive `base_fee_per_gas`, positive `gas_limit`, nonnegative integer remaining
  domains, `gas_used <= gas_limit`, exact nonempty string regime name, and no coercion.
- Validate every ancestry header's requested number and hash fields. Immediate numbered anchor
  reread must equal the tagged anchor in number, block hash, and parent hash.
- Strict candidate/canonical load requires exactly `manifest.json` and `blocks/`; direct real
  directories/regular files; no symlink, escape, or extra entry; exact manifest types/keys;
  anchor number at least the declared last block; exact inventory bytes; and streamed payload
  schema/domain/range/order validation. Validate the owned hidden candidate immediately before
  visibility.
- “Failure leaves no canonical package” applies only before the exclusive rename is visible.
  Rename, parent-sync, or strict-reload failure after that point is ambiguous under Issue 15:
  preserve visible/unpublished paths, inspect them, and persist no recovery status.
- Resume/finalization memory is `O(max chunk + file inventory)`, not `O(max chunk)`, because
  path sorting, inventory rows, and identity bytes are retained. Payload IO/hashing remains
  linear; ancestry headers remain streamed with `O(1)` header memory.

The disposable prototype now implements these derived corrections and the approved definition
binding. It remains disposable research and performs no external acquisition.

## Approved corrected whole-contract recap

One direct chain-generic module accepts one exact inclusive single-chain `CorpusDefinition`
fixed by Issue 11. It issues ordinary numbered reads through one provider
seam. The provider alone owns finite runtime retry/backoff; acquisition performs zero retries,
persists no retry fact, bounds a numeric concurrency window, validates completed rows eagerly,
observes all terminal outcomes before writing from a completion set, writes only exact order in
atomic private Parquet chunks, and cancels siblings on terminal failure. Every private row
carries temporary block/parent hashes and the same stage-only `definition_sha256` of the strict
canonical complete definition JSON (`ensure_ascii=True`, `allow_nan=False`, sorted keys,
compact separators). Resume scans the whole existing stage and requires exact
digest/schema/row equality before any provider read or write. It accepts only an exact immutable
prefix. An incomplete valid prefix resumes; an invalid stage is preserved and reacquired in a
fresh disposable stage, never repaired, truncated, shrunk, extended across definitions, or
silently restarted. No marker or lifecycle exists. Provider/RPC URL/name, host/path,
concurrency, retry/backoff, stage chunk tuning, runtime timestamps, counters, and observations
remain ephemeral.

One finalizer rejects missing, extra, corrupt, gapped, duplicated, reordered, wrong-definition,
wrong-schema, wrong-chain, wrong-domain, decreasing-timestamp, hash-invalid, or parent-broken
rows without sorting or repair. It queries `finalized`, proves the corpus last block equals or
is a streamed hash-linked ancestor, and immediately rereads the same numbered anchor with full
header equality; unsupported finality or any mismatch fails closed. It omits stage-only
definition/hash fields from finalized rows, streams rows
through fixed canonical Parquet geometry/settings, builds the exact UTF-8-sorted
`{relative_path, byte_length, full_sha256}` inventory, makes the identity preimage exactly the
canonical JSON bytes of `{"definition": ..., "files": [...]}`, and assigns its bare full
SHA-256. Readable regime name/start remain trusted request and
final-manifest metadata for Issue 11 identity and Issue 47 containment, never raw/model rows.
The manifest retains only the approved definition, inventory, corpus ID, and finalized-anchor
evidence—no provider fact, validation report, status, resume record, format/version marker,
compatibility data, runtime tuning, or stage digest.

The owned hidden candidate is strictly loaded and synced before Issue 15's exclusive no-replace
rename, then the parent is synced and the canonical package strictly reloaded. Existing equal
identity is no-op even when structurally valid anchor evidence differs. Invalid or different
same-ID content is conflict and preserves both. Pre-visibility failure leaves no canonical
package; post-rename failure is ambiguous, preserves paths, and triggers direct inspection with
no durable lifecycle. Only the owner of an unpublished stage may remove it. NFS publication
remains gated.

Acquisition memory is `O(concurrency + stage chunk rows)` with completed results bounded by the
numeric concurrency window. Resume/finalization memory is `O(max chunk + file inventory)`;
payload IO and hashing are linear in corpus bytes. Ancestry proof streams headers in `O(1)`
header memory. Hashless existing Parquet is the one case requiring one fresh source-row read per
corpus row because no cheaper exact parent-link proof exists.

Hashless existing Parquet enters only this same validator/finalizer under an explicit
definition. Its target must validate as a fresh empty stage before any provider read or write.
It receives a fresh new-layout content identity and pays one fresh exact source read per row to
recover hash/link proof; any mismatch means reacquire, never convert or repair.
Issue 27 itself remains chain-generic and performs no acquisition. Under the already-approved
Issue 49 downstream plan, that later owner checks intervening material protocol changes,
freezes exact facts, then invokes this path for one contiguous Ethereum definition and one
Polygon definition; it invokes no Avalanche definition. That scope is not an Issue 27 branch.

Priority fees are excluded from the current baseline, not permanently rejected. Issue 27 and
the approved Issue 49 plan add no enrichment machinery. There is no active follow-up ticket or
native gate. On a later authorized Wayfinder pass, the map owner retains one fog line and
removes the contradictory out-of-scope duplicate. Only after preprocessing, training,
evaluation, and serving stabilize does a fresh ticket begin with the bounded Ethereum
`eth_feeHistory` provider/range/provenance probe scoped by closed Issue 60, followed by a fresh
owner decision.

Clean-break implementation removes the exact old acquisition, pre-content identity, SQLite
catalog/root, replace-publication, config/CLI, source-requirement, current priority-fee, transfer,
loader, caller, documentation, and test paths in `implementation-map.md`; it creates no legacy
reader or parallel path. The required native graph correction is exactly `#27 blocks #34`.
That is a derived graph-correctness handoff, not a design choice. The orchestrator/map owner
connector-first wired and verified it; this owned thread did not mutate it.

Edo approved this corrected recap exactly. Under his standing final-contract rule, the normal
ticket-scoped research publication and completion sequence needs no further owner question. He
also explicitly directed publication on synchronized `main`. Resolution, close-only-Issue-27,
fresh map-pointer/tracking correction, and verification proceed only after unchanged green
verification and immutable links for these assets.

## Authorized research publication

Publication is exactly the five files in this directory: `README.md`, `prototype.py`,
`prototype_logic.py`, `implementation-map.md`, and `dependent-completeness-audit.md`. Commit
them once directly on synchronized `main`, push `main`, verify that the cached and remote commit
contain only those five additions from this workspace, and use full-commit-SHA GitHub tree/file
permalinks as the immutable research links. Do not include generated output, `__pycache__`,
corpora, tests, production code/config/data, unrelated dirty files, a branch, PR, merge, tag, or
release. Stop on any extra staged path.

## Transitive completeness and graph

`implementation-map.md` now names the complete clean-break impact across acquisition exports,
RPC, corpus planning/staging/validation, pre-minted IDs and chain-qualified layout, SQLite
catalog/discovery, replace-based publication/transfer, configuration/resolution/YAML, workflow
preparation/reporting, modeling/study provenance, serving callers, priority-fee routing,
normative docs, ADR 0004, and directly coupled tests. The old corpus merge script is never
adapted; its active-tree removal follows Issue 20's approved custody procedure.

Handoffs are exact for Issues 10, 15, 20, 32, 34, 38, 42, 49, and 63. In particular, Issue 34
owns final payload fields, fixed canonical writer geometry/settings, readable manifest
serialization, and one strict manifest-plus-inventory-plus-payload loader; Issue 49 owns the
intervening-protocol-change check and exact Ethereum/Polygon definition freeze.

Read-only native graph verification found Issue 27 directly under open map 1 and blocked by
closed Issues 15 and 24. After explicit authorization, the orchestrator/map owner wired and
verified `#27 blocks #34`: Issue 27 now blocks open Issues 34, 32, and 63; Issue 34 is blocked by
Issues 27, 25, and 43. No graph mutation occurred in this owned thread.

## Verification

After the approved binding and derived hardening, all six OS-temp synthetic scenarios pass.
Changed regime name and changed last block both reject the private prefix before any provider
call; a mismatched import target also rejects with zero provider calls and unchanged bytes; final
payload contains no `definition_sha256`. Runtime stage chunk sizes 2 and 3 produce the same
canonical corpus ID, provider failure cancels siblings, strict finality fails before visibility,
same-content is no-op, invalid same-ID content preserves both, a simulated lost rename-success
reply is classified ambiguous with the visible canonical path preserved, and hashless existing
bytes either receive a fresh identity or require reacquisition. Ruff, Pyright, and Vulture are
all green; no `__pycache__` remains.
