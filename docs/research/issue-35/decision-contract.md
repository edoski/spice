# Issue 35 decision contract

Status: explicitly approved by Edo on 2026-07-15.

This ticket is planning and prototype evidence only. It authorizes no production,
configuration, dependency, test, data, storage, acquisition, training, tuning,
evaluation, Slurm, serving, archive, sibling-ticket, or native-graph implementation.

## Exact collection

The sole collection instruction is the ordered, duplicate-free evaluation UUID list
supplied by the Issue 49-owned protocol constructor. That order is authoritative for
collection and the final TSV rows. Do not sort it.

For each UUID in caller order, ordinary-transfer exactly:

```text
evaluations/<evaluation_id>/evaluation.json
evaluations/<evaluation_id>/observations.parquet
```

After typed request validation, ordinary-transfer every distinct referenced native
`artifacts/<artifact_id>.ckpt` once, in first-reference order. The sealed predictive
reduction truly needs the checkpoint's `K` and fitted target mean and standard deviation.
No other checkpoint or file is transferred.

This is an external operator procedure, not an application collector. Its ordered copy
arguments are ephemeral. Persist no manifest, file list, bundle, inventory, receipt,
index, catalog, cache, collector state, summary, database, revision, or transfer record.
A failed transfer is manually retried. The transfer itself creates no partial summary
authority and promises no batch transaction.

## Application seam

One deep application module owns strict explicit-path loading, the single fixed
column-pruned Polars reducer, and the all-or-nothing sealed TSV writer. Its research
entry point accepts the Issue 49-owned ordered protocol list, the corresponding explicit
evaluation JSON, observations Parquet and native checkpoint paths, and the destination
path as ephemeral typed values. It exposes no root scan, lookup, selector, filter,
query, metric name, view language, registry, output record hierarchy, or generic
research framework.

The module validates every input before it returns a frame or invokes publication. The
reducer selects the fixed columns needed by the approved Issue 21 and Issue 48 formulas
before collection, recomputes the approved predictive and economic values, and returns
only a transient frame for the writer. Checkpoint-derived facts come from native strict
Lightning loading. No scalar summary is loaded, cached, or treated as authority. No
numerator, vector, `S/G/Q` helper, plot fact, or other transient reducer state is stored
as a second result artifact.

The loader, reducer, and writer are count-agnostic. They preserve the supplied protocol
order, emit one row per supplied UUID, and contain no expected-count constant or check.
The current Issue 49 protocol list contains 48 UUIDs: nine fixed-C500 family
representatives, nine selected-family descriptive controls at `C={50,100,250}`, and
thirty final-K evaluations. This `48` is a current protocol fact, not application state.

The writer writes the one fixed ordered TSV to a hidden sibling and directly renames it
only after every object in the supplied exact list validates and reduces. For the
current protocol, all-or-nothing therefore means all 48. Failure preserves the prior
TSV unchanged. There is no partial frame or partial installed TSV.

## Malformed authority

Reject a duplicate evaluation UUID before file loading. Then visit evaluations in caller
order and deterministically stop at the first defect:

1. load the complete strict EvaluateRequest and require its evaluation UUID to match the
   requested direct path;
2. require the exact ordered 13-column observations schema and exact dtypes;
3. require a nonempty, non-null, finite, strictly ordered observation table and all
   approved local fee, action, and elapsed-time facts;
4. load the native checkpoint strictly, require its exact request/artifact association,
   and require every action index to satisfy `0 <= action < K`.

The error identifies the evaluation UUID/path and violated owned field or fact. Delegate
complete Window and checkpoint semantics to their owning typed/native loaders. Do not
duplicate those contracts here.

Never coerce, repair, sort, drop, deduplicate rows, accumulate an error report, return
partial data, or mutate the prior TSV after a failure. Do not add status objects,
fallbacks, recovery machinery, or compatibility modes.

## Clean-break survivor boundary

No current scanner, summarizer, renderer, collector, snapshot, result record, SQLite
index, export, or research script survives or is ported. The application survivor is
only strict explicit-path loading, the single column-pruned Polars reducer, and the
all-or-nothing sealed TSV writer.

Preserve no thesis renderer, external workbench, plotting dependency, placeholder,
adapter, or automation. If a future concrete thesis figure is needed, it begins fresh
outside this contract and must earn its own exact input and presentation boundary.

Add no manifest, summary authority, bundle, scanner, index, catalog, metric namespace,
prediction corpus, logits, probabilities, cache, SQLite, fuzzy matching, software
revision, compatibility shim, speculative abstraction, registry, or generic framework.

## Implementation handoff

The future implementation remains full-code-first. It removes old consumers before
adding this seam, uses the existing mature Pydantic, Polars, and native Lightning
facilities, and adds only lean behavior tests for strict loading, caller ordering,
checkpoint necessity, fixed reduction, and all-or-nothing TSV publication. It adds no
transition, legacy compatibility, or architectural regression tests.

The disposable `prototype.py` and `prototype_logic.py` are evidence only. Production
must absorb the approved behavior idiomatically and must not copy their synthetic Window
or checkpoint proxy.
