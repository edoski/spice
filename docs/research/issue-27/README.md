# Issue 27 exact-root acquisition prototype

Disposable logic prototype. It answers one question: can an explicit minimal
`CorpusDefinition` reach one immutable content-bound corpus with provider-only retry,
bounded ordered writes, resumable private staging, direct validation, and Decision-A
publication without adding a durable acquisition lifecycle? The dependent audit found and
closed one gap: raw row continuity alone could not prove which full definition created a
stage. See [`dependent-completeness-audit.md`](dependent-completeness-audit.md).

Run:

```bash
uv run python -B docs/research/issue-27/prototype.py
```

Run every scenario non-interactively:

```bash
uv run python -B docs/research/issue-27/prototype.py --all
```

The prototype creates synthetic Parquet only under an OS temporary directory and deletes it
on exit. It makes no RPC call and writes no production root, config, corpus, database, or
package resource.

## Discriminating observation

Cheapest observation: interrupt an out-of-order bounded pull after some atomic chunks are
visible, then ask whether scanning those chunks can identify the one valid contiguous prefix
without a separate marker. Push that state through invalid-prefix, finalized-anchor mismatch,
same-content no-op, same-id conflict, and old-Parquet validation cases.

Budget: six synthetic scenarios, 4–9 corpus rows each, at most three concurrent in-memory
rows plus one output chunk, a few KiB of temporary Parquet, no network, and under one minute.
Stop when every branch either publishes exactly one validated immutable root, returns no-op,
or fails closed while preserving the unpublished bytes needed for inspection. Do not grow a
framework after that observation.

## Prototype contract

The external seam is two operations: acquire an inclusive `CorpusDefinition` into a private
stage, then finalize that stage into `corpora/<bare-full-sha256>/`. The definition is exactly
`{chain_id, regime: {name, start_block}, first_block, last_block}`. Provider, URL, host,
paths, concurrency, chunk size, retry/backoff, timestamps, counters, and runtime observations
never enter it or the final manifest.

Acquisition issues ordinary numbered calls through one provider seam. The provider owns its
bounded retry/backoff. Acquisition has no retry loop, adaptive split, adaptive concurrency,
or counters. It bounds the numeric request window, buffers out-of-order results, writes only
the next exact block, atomically exposes complete Parquet chunks, and cancels siblings on the
first terminal provider or validation error.

The private Parquet files are the only resume checkpoint. Resume scans them chunk by chunk
and accepts only an exact validated row prefix beginning at `first_block`. No
`progress.json`, status, attempt count, provider fact, or manifest provenance is needed. A
corrupt, gapped, extra, wrong-schema, wrong-chain, wrong-domain, or parent-broken stage is
preserved and rejected; the next attempt uses a fresh disposable stage rather than
truncating or repairing it.

Every private row also carries one constant stage-only `definition_sha256`: the lowercase
full SHA-256 of the complete `CorpusDefinition` JSON encoded with `ensure_ascii=True`,
`allow_nan=False`, sorted keys, and compact separators. Resume requires exact digest equality
before any provider read or write. The digest is removed during finalization. Readable regime
name/start remain trusted request and final-manifest metadata under Issues 11 and 47; they are
never repeated in raw or model payload rows. There is no marker file, path identity, footer
contract, lifecycle, or final-payload duplicate.

Private stage rows temporarily carry block hash and parent hash so direct finalization can
verify every adjacent link across files. Final payload rows omit those two columns, matching
the approved no-mandatory-per-row-hash boundary. The finalizer validates exact range, order,
schema, domains, nondecreasing integer timestamps, and links; queries `finalized`; streams only
intervening headers when `last_block` is an ancestor; immediately rereads the numbered anchor;
then rechunks the stream with one fixed non-runtime prototype geometry, writes deterministic
ordered payload files, and builds the exact byte/hash inventory. The fixed value demonstrates
that ephemeral acquisition chunk tuning cannot change identity; Issue 34 must freeze the
production writer geometry and payload fields.

The identity preimage is exactly `{"definition": ..., "files": [...]}` using the approved
canonical JSON encoding. Inventory rows are exactly `relative_path`, `byte_length`, and full
SHA-256, sorted by UTF-8 path bytes. The corpus ID is the bare full SHA-256. Finalized-anchor
evidence is in the candidate manifest but outside identity.

Publication strictly reloads the owned hidden candidate before visibility, syncs files and
directories, uses the host's exclusive no-replace directory rename, syncs the parent, and
strictly reloads the canonical root. Existing equal identity is no-op. Invalid or different
same-id content is conflict and preserves both. Pre-visibility validation/finality failure
leaves no canonical package. A rename, parent-sync, or reload error after the exclusive rename
is ambiguous: preserve visible paths and inspect them under Issue 15; never speculatively
delete. The prototype depends on the approved local APFS primitive; canonical NFS publication
remains separately gated.

Existing Parquet is never a legacy path. The prototype feeds it through the same new schema,
domain, range, source-row, hash-link, finality, inventory, identity, and publication path. Its
old payload lacks hashes, so this demonstration rereads every exact source row to earn the
link proof. The import target must first validate as a fresh empty stage, before any provider
read or write. Any mismatch returns “reacquire”; it never converts, repairs, shrinks, extends,
or silently reuses old bytes.

## Bounds

Acquisition memory is `O(concurrency + chunk_rows)` and completed-result buffering cannot move
beyond the fixed numeric concurrency window. Resume and finalization use
`O(max chunk + file inventory)` memory because paths, inventory rows, and identity bytes are
retained; payload IO and hashing are linear in corpus bytes. When the declared last block is
older than the finalized anchor, ancestry proof uses `anchor - last_block - 1` ordinary header
reads and `O(1)` header memory; last-equals-anchor needs none. Existing hashless Parquet needs
one fresh source-row read per corpus row because no cheaper exact parent-link proof exists.

## Owner approval

On 2026-07-13, Edo explicitly approved all four choices and the complete whole-contract recap
exactly as presented:

1. No separate partial-acquisition marker: the exact immutable Parquet prefix is the
   only private checkpoint.
2. The public provider is the sole retry/backoff owner. Acquisition performs zero retries and
   persists no retry fact. No project-fixed numeric retry limit is added; finite provider
   settings remain runtime-only.
3. Private stage-only block hashes/parent hashes, with hashes omitted from finalized
   per-row payload and only the finalized anchor retained in the manifest.
4. Full fresh row/header validation is the price of reusing hashless existing Parquet;
   failure means fresh acquisition, never repair.

After the dependent audit and explicit pushback reconciliation, Edo also approved these three
decisions exactly:

1. Bind each private stage with the one constant strict-canonical full-definition
   `definition_sha256` above; require exact equality before resume; strip it from final payload;
   keep readable regime name/start only in the trusted request and final manifest.
2. Keep Issue 27 chain-generic. The already-approved Issue 49 plan later invokes this path once
   for Ethereum and once for Polygon, with no Avalanche invocation; that is downstream scope,
   not an acquisition branch.
3. Exclude priority fees from the current baseline only. Add no Issue 27 machinery. On a later
   authorized Wayfinder pass, retain one fog line and remove the contradictory out-of-scope
   duplicate. Create a fresh concrete ticket only after preprocessing, training, evaluation,
   and serving stabilize; closed Issue 60 scopes the first bounded Ethereum `eth_feeHistory`
   probe and fresh owner decision.

These approvals authorize no acquisition, production/data mutation, Resolution comment, issue
closure, map edit, native-edge mutation, or prototype publication. Edo then explicitly approved
the corrected complete Issue 27 contract exactly as recapped on 2026-07-13.

Edo separately authorized the one derived native edge `#27 blocks #34`; the orchestrator/map
owner completed and verified it.
Issue 27 now blocks Issues 34, 32, and 63; Issue 34 is blocked by Issues 27, 25, and 43. This
owned thread did not duplicate the graph mutation.

Edo explicitly authorizes publishing exactly these five Issue 27 research files as one isolated
commit directly on synchronized `main`, with every unrelated dirty path excluded and no branch,
PR, merge, tag, or release. Once the immutable links verify and nothing changes, the approved
final contract authorizes the connector-first Resolution, close-only-Issue-27, fresh
map-pointer/tracking correction, and verification sequence without another owner question.
