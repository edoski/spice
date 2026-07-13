# Lean benchmark-runner prototype

Question: do the approved finite thesis matrices need a benchmark-owned batch
language, or are explicit named lists of complete `WorkflowRequest` values enough?

Cheapest discriminating observation: express every approved cell, gate, reuse, and
exact evaluation join in all three runner shapes. Budget: read-only audit plus a
small in-memory prototype; no training, evaluation, database writes, or production
changes. Stop when every surviving workload fits and extra scheduling machinery can
be counted.

Run:

```bash
uv run python docs/research/issue-18-benchmark-runner/explore.py --report
uv run python docs/research/issue-18-benchmark-runner/explore.py --tsv
```

The fixture expands the fixed minimum route to 54 non-HPO train requests, three HPO
study requests, and 45 exact sealed-test evaluation requests. It does not presume
extra validation `EvaluateRequest` values before Issue 49 freezes that need. Selection is staged:
6 capacity/activity artifacts, 3 UTC-hour additions, and 3 CE-weighting additions.
After the three HPO studies, the context branch adds 12 artifacts and reuses 3;
the horizon branch trains 30 chain-by-K artifacts. Testing evaluates those 45
artifacts. The same-weight accelerator proof is not a train/tune/evaluate workflow;
the table adds only the approved pointer to its Issue-40-owned report.

| Alternative | New benchmark-owned machinery | Fit to actual topology |
| --- | --- | --- |
| Explicit named request lists | No new types; named stage builders call the direct execution plan and collect exact evaluation IDs | Complete |
| Minimal `BatchPlan` | `BatchPlan`, `BatchEntry`, label dependencies, validation | Adds no useful in-stage edge: every request inside each surviving stage is independent |
| Current generic engine | 18 Python files, 2,891 lines, 40 classes, axes/grids/graph/ledgers/codecs/search/index | Complete but shallow and dominated by retired workflows |

Recommendation: delete the benchmark engine. Keep named thesis stage functions near
the thesis workflow, each returning an ordinary tuple of already-constructed exact
requests. Issue 30/execution owns persist-before-work and submission state. Collection
receives the 45 `EvaluateRequest` values, transfers or loads each exact
`evaluations/<evaluation_id>.json`, validates the record against the request, and
writes one TSV table. No SQLite index, collection scan, producer-coordinate match,
Cartesian schema, sampler, registry, or benchmark codec survives.

Downstream Issue-29 handoff: Issue 10's selected-study source contains only
`corpus_id` and `study_id`. Final-K requests need a clean, provenance-preserving
promotion of the selected model/optimizer facts while K changes. Issue 29 must retain
the selected `(study_id, trial_number)` provenance. The runner accepts fully
constructed `TrainRequest` values. It must not add an override, copy a study
definition, create extra studies, or lose the selected-trial provenance.

Edo approved all five decisions on 2026-07-13: full engine/config deletion, explicit
request lists, exact-ID table publication, ordinary per-request submission, static-only
archival treatment, and an Issue-40 report pointer with no fourth workflow or extension
mechanism. Delete the terminal shell after the whole contract resolves; retain only the
reviewed decisions and final evidence table.
