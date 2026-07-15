# Issue 35 current-code and authority audit

Status: disposable decision evidence. This is not production code or an approved
contract.

## Authority read

The latest owner-approved Issue 34 Resolution and its Amendments are the controlling
authority. They replace older hashes, inventories, manifests, summary objects, scanners,
runner plans, provenance, aggregate storage, and compatibility proposals found in
earlier issue text and prototypes.

The complete directly relevant issue bodies, Resolutions, Amendments, comments, local
research files, prototype Python, fixtures, and recorded outputs were read for Issues 18,
20, 21, 34, 35, 36, 48, 49, 63, and 78. The direct-path and transfer authorities in
Issues 11, 13, 15, 30, and 32 were also read. There was no pre-existing local
`docs/research/issue-35/` or Issue 36 research directory.

The resulting authority chain is:

- Issue 34 fixes direct UUID addresses, the exact five-field EvaluateRequest, the exact
  ordered 13-column observations schema, the single column-pruned Polars reducer, native
  checkpoints, ordinary transfer, and every forbidden stored or discovery surface. Its
  prior sealed-count wording is superseded by Issue 49's latest owner-approved list.
- Issues 18 and 36 fix the 60 Train / 3 Tune / 69 Evaluate request set, the explicit
  list discipline, and caller-loaded sealed evaluations. Their old sealed-count wording,
  runner, and collection prototypes are superseded evidence only.
- Issue 20 says no existing research reader, renderer, scanner, summarizer, snapshot,
  database, or script remains maintained. Issue 35 ports none of them.
- Issues 21 and 48 own the exact predictive and finite-window economic reductions. Issue
  35 must call that math once; it does not rename metrics or define a second reducer.
- Issue 49 owns the current 48-UUID sealed evaluation list and order: nine fixed-C500
  family representatives, nine selected-family descriptive controls at
  `C={50,100,250}`, then thirty final-K evaluations, each in its approved chain-major
  inner order. The Issue 35 consumer receives that exact list and contains no count
  constant.
- Issue 63 removes list, query, filter, export, scan, and follow surfaces. Known exact
  consumers validate direct inputs.
- Issue 78 removes revision equality, inventories, workflow plans, and transfer
  protocols. Native Lightning loading and ordinary `rsync` remain sufficient.
- Issues 11 and 13 require direct typed addresses and loaders, with no store wrapper,
  generic reader, catalog, scan, or discovery API.
- Issue 15 supplies the external operator primitive: ordinary transfer to a hidden
  sibling followed by direct rename, with manual recovery.
- Issue 30 supplies no canonical request root or reconciliation plan.
- Issue 32 leaves Polars as the data-frame dependency and preserves no application
  plotting framework or research extra.

No consequential contradiction remains after applying the latest Amendments, Edo's
three explicit Issue 35 decisions, the Issue 49 correction, and final contract approval.

## Current code

`src/spice/benchmarks/collection.py` pulls artifact roots through a transfer transaction,
then writes a collection snapshot and SQLite result index. Its interface and state are
forbidden.

`src/spice/benchmarks/collection_resolver.py` loads an artifact manifest and training
summary, scans stored evaluation summaries, and fuzzy-matches evaluator, delay, and
execution provenance. The approved consumer instead receives exact evaluation paths and
validates the embedded exact request.

`src/spice/benchmarks/result_records.py`, `_result_schema.py`, and `result_index.py`
create summary records, a metric namespace, SQLite observations and metrics, filters,
queries, rebuilds, exports, and stored derived values. No type or behavior is reusable.

Current `src/spice/evaluation` and `src/spice/modeling/results.py` expose generic metric
maps and persisted runtime summaries rather than the approved scalar observation rows.
Their old result envelopes are not an input or output of the Issue 35 seam.

All sixteen files under `benchmarks/scripts/` leave the maintained active tree under the
Issue 20 clean break. In particular, the four `scan_*` scripts discover windows, the two
`summarize_*` scripts read CSV or SQLite summary authority, and all eight `render_*`
scripts duplicate joins and scientific reductions while owning plotting and report
files. The corpus merge and evaluation-suite writer are also not ported. The uncommitted
user edit in `render_lstm_block_count_quartile_results.py` was inspected read-only and
preserved.

## Prototype result

The bounded synthetic prototype uses two caller-ordered evaluation UUIDs that share one
artifact. Exact sealed collection therefore contains five transferred files: two
evaluation pairs in caller order and one checkpoint in first-reference order.

The reducer preserves caller order, selects only its fixed required Parquet columns, and
derives checkpoint-dependent Smooth-L1 and natural-log errors without a stored summary.
Four malformed cases fail as intended: an extra JSON field, a wrong Parquet dtype,
unordered origins, and a missing checkpoint path.

The prototype deliberately uses a nonempty opaque Window object and a JSON checkpoint
proxy. Production must delegate those complete semantics to the Issue 46 request model
and native strict Lightning checkpoint loader. The proxy is not an ABI proposal.

Verified commands:

```console
uv run python docs/research/issue-35/prototype.py
uv run ruff check docs/research/issue-35
uv run ruff format --check docs/research/issue-35
uv run pyright docs/research/issue-35
uv run vulture docs/research/issue-35 --min-confidence 90
```

An initial Vulture run reported only the class parameters required by Pydantic
field-validator callbacks. They were manually verified as framework callbacks, not dead
code; their intentional underscore names leave the final Vulture run clean.
