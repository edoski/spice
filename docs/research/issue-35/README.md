# Issue 35 exact collection prototype

Status: disposable decision evidence for the approved `decision-contract.md`. It is not
production code.

Question: what is the smallest exact collection and maintained research-consumer seam
that preserves explicit evaluation authority, deterministic order, strict failure, and
the single Issue 34 Polars reducer?

Run:

```console
uv run python docs/research/issue-35/prototype.py
```

The bounded synthetic fixture has two explicitly supplied evaluation directories that
share one artifact. The prototype validates both complete two-file objects before it
returns anything. It never scans a root, builds an index, writes a manifest, stores a
summary, or reads a database.

The prototype's `EvaluateRequest.window` is deliberately limited to a nonempty object.
Production must use Issue 46's complete strict Window model; Issue 35 must not invent or
duplicate that owner contract. The JSON `.ckpt` is likewise only a synthetic proxy for
facts returned by native strict Lightning loading, not a proposed checkpoint ABI.

## Findings

The minimal collection operation is an operator-owned ordinary transfer, not an
application collector. For each caller-supplied evaluation UUID, in caller order, copy
`evaluation.json` then `observations.parquet`. The sole surviving sealed predictive
summary additionally needs each referenced native checkpoint because fitted target mean
and standard deviation are required to recompute standardized Smooth-L1 and natural-log
MAE/MSE. Transfer checkpoints once, in first-reference order. This ordered command input
is ephemeral; it must not be persisted as a manifest or bundle.

The application seam can be one deep module:

```text
explicit EvaluationInput paths
  -> validate every request, exact Parquet schema, row facts, and needed checkpoint
  -> one column-pruned Polars reducer
  -> sealed summary rows for the all-or-nothing TSV writer
```

There is no reduction selector, metric registry, view language, or second consumer. The
reducer prunes Parquet columns to the sealed calculation. Results preserve the exact
Issue 49 caller-list order and validated origin order. The writer is count-agnostic and
publishes only after every supplied input validates and reduces; no partial table is
returned or installed. The current Issue 49 protocol list has 48 UUIDs, but `48` is a
protocol fact, never a loader, reducer, or writer constant.

Malformed authority fails at the boundary. Do not coerce, sort, drop, deduplicate,
repair, or partially summarize. Reject an empty explicit list, duplicate evaluation
UUIDs, path/request UUID mismatches, missing files, extra or malformed request fields,
wrong or reordered Parquet columns, wrong dtypes, nulls, non-finite values, empty rows,
non-increasing origins, invalid fee/action/wait facts, missing required checkpoints,
artifact mismatches, and action indices outside checkpoint `K`. Errors identify the
object and violated fact. Full Window/corpus/checkpoint association checks remain with
their owning typed loaders.

No scanner survives. None of the current collection, SQLite index, summary-record, scan,
summarizer, or renderer implementations fit the approved authority and should be ported.
The only maintained application consumer is the strict loader, reducer, and
all-or-nothing sealed TSV writer. Preserve no renderer, plotting dependency, workbench,
placeholder, or automation. Any future concrete thesis figure starts fresh outside this
contract.
