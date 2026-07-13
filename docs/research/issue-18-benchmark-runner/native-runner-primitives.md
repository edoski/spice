# Native runner primitives and the smallest labelled alternative

## Result

Do not add a benchmark-owned `BatchPlan`. The fixed minimum topology is 102 exact workflow requests, constructed in stages: 54 train requests, three tune requests, and 45 sealed-test evaluate requests. This count does not presume extra validation evaluate requests before Issue 49 freezes that need. Its real joins are owner freeze and affordability gates, not scheduler edges. Ordinary named Python lists plus the execution-owned durable plan from Issue 30 express the work with less interface than a second plan type.

The cheapest observation was static and outcome-free: express the 12-artifact validation ladder, three per-chain HPO studies, 12 context additions, 30 chain×K artifacts, and 45 sealed evaluations as exact requests; inspect ordering, reuse, and gates; stop as soon as the candidate either deletes repeated mechanics in two workflows or merely renames a loop. Budget: at most the 102 request rows and one regenerated evidence table; no submission, training, evaluation, database, or durable prototype state. The candidate merely renamed the loop, so the stop condition fired.

This follows the approved request algebra: one discriminated `TrainRequest | TuneRequest | EvaluateRequest`, with study, artifact, and evaluation UUIDs minted once and persisted before work. A request carries no target, host, path, catalog, selector, or duplicated resolved payload ([Issue 10 resolution](https://github.com/edoski/spice/issues/10#issuecomment-4957991242)). Pydantic's first-party documentation supports one reusable `TypeAdapter` for validating and serializing a non-model union, and recommends discriminated unions for predictable member selection ([TypeAdapter](https://pydantic.dev/docs/validation/latest/concepts/type_adapter/), [discriminated unions](https://pydantic.dev/docs/validation/latest/concepts/unions/#discriminated-unions)).

## Smallest plausible labelled candidate

The radically flexible version needs only this interface:

```python
@dataclass(frozen=True, slots=True)
class Entry:
    label: str
    request: WorkflowRequest
    after: tuple[str, ...] = ()

def submit_all(
    entries: Sequence[Entry],
    *,
    submit: Callable[[WorkflowRequest, tuple[str, ...]], Submission],
) -> tuple[Submission, ...]: ...
```

`submit` captures the runtime target. `submit_all` validates the whole sequence before side effects, submits in declared order, and replaces each `after` label with the already-returned job ID. Slurm supplies the scheduling semantics; `afterok` already defers a job until named predecessors exit successfully ([Slurm `sbatch --dependency`](https://slurm.schedmd.com/sbatch.html#OPT_dependency)). No concurrency limit belongs here: independent rows are submitted without dependencies and the selected target schedules them.

Exact invariants:

- labels are non-empty and unique;
- each dependency label is unique within the entry and names an earlier entry; forward references, missing labels, and cycles are therefore impossible;
- every request has already passed the one request-union adapter and already contains its destination ID;
- destination study, artifact, and evaluation IDs are unique within the sequence;
- sequence order is canonical output order; the runner does not sort, expand, sample, select, retry, resume, or infer dependencies;
- validation failure submits nothing; submission failure stops later submission and propagates with the entry label. Issue 30 owns attempt recording and crash reconciliation, so this interface must not invent recovery state.

Exact candidate errors are `ValueError("duplicate label: <label>")`, `ValueError("unknown or forward dependency: <label> -> <dependency>")`, and `ValueError("duplicate destination id: <id>")`; request hydration retains its schema `ValidationError`; remote submission retains its execution error with `entry=<label>` added as context. There is no error taxonomy or registry.

The candidate still adds four concepts—`Entry`, dependency validation, a label-to-job map, and a destination-ID extractor—plus focused tests for uniqueness, earlier-only dependencies, all-before-side-effects validation, and failure stop. Deleting it recreates one short `for` loop in the context/K submitter and one in sealed evaluation. That is a shallow module. If Issue 30's approved durable entry contains `label`, exact request, and dependencies, these mechanics belong there once; if it does not, Issue 18 should use explicit lists and no dependency language.

## Actual matrices

The approved topology proves why a generic graph does not help ([Issue 49, canonical topology](https://github.com/edoski/spice/issues/49#issuecomment-4956002091)).

```python
CHAINS = (ethereum, polygon, avalanche)
K_VALUES = (2, 3, 4, 5, 10, 15, 30, 50, 100, 200)
C_VALUES = (50, 100, 500, 1000)  # C=200 reuses earlier artifacts

final_k = tuple(
    named(f"final-k/{chain.name}/k={k}", train_request(chain, k=k))
    for chain in CHAINS
    for k in K_VALUES
)
context_additions = tuple(
    named(f"context/{chain.name}/c={c}", train_request(chain, c=c))
    for chain in CHAINS
    for c in C_VALUES
)
sealed = tuple(
    named(cell.label, evaluate_request(
        evaluation_id=cell.evaluation_id,
        artifact_id=cell.artifact_id,
        corpus_id=cell.corpus_id,
        window=cell.testing_window,
    ))
    for cell in (*context_cells_15, *final_k_cells_30)
)
```

The validation ladder is three separate explicit lists: six capacity/activity requests; after Edo freezes that winner, three UTC-hour additions; after the next freeze, three CE-weighting additions. Planning all 12 as a graph would falsely encode an unknown future winner. The three HPO studies are one independent three-item tune list. After their selections freeze, the 12 context additions and 30 final-K requests are independent lists and may be submitted in parallel. The 45 exact evaluate requests exist only after both branches complete and the metrics-blind affordability gate passes. The exhaustive evaluator evaluates one frozen artifact over one declared block-origin range; it remains evaluation code, not runner orchestration ([Issue 48 resolution](https://github.com/edoski/spice/issues/48#issuecomment-4950650999)).

Accelerator parity does not fit the three-workflow request union. It compares identical weights on full and tail batches and writes dedicated parity evidence; it is neither train, tune, nor exhaustive evaluation. Its current owner explicitly defers execution until the training host and artifact contract freeze ([Issue 40](https://github.com/edoski/spice/issues/40)). Edo approved one Issue-18 output consequence: append only a pointer to the Issue-40 report, with no fourth workflow, callback, plugin, or registry.

## Remote submission and exact collection

Keep the execution-owned SSH/Slurm seam. Current `ExecutionSession.submit_workflow` already accepts one typed workflow config, renders one `sbatch` script, returns job provenance, and supports a native dependency; the repository has separately accepted retaining this custom session because it also owns SSH selection, storage-root rewrite, logs, rsync, and remote invocation ([session.py](../../../src/spice/execution/session.py), [ADR 0005](../../adr/0005-custom-execution-session-retained.md)). The clean-break request union should replace the old resolved snapshot, not gain a batch wrapper. Lightning's `Trainer.fit` owns one model optimization routine, not multi-request SSH submission or result collection, so Lightning is relevant inside a train workflow only ([Lightning Trainer](https://lightning.ai/docs/pytorch/stable/common/trainer.html#fit)).

Edo approved the bounded submission rule: use ordinary per-request Slurm submission and assume it has no material orchestration overhead. Add no array/index language, numeric runner cap, concurrency controller, submission probe, fallback, or dormant abstraction. A truly new future requirement needs a fresh owner decision.

Collection becomes direct after the approved flat storage break. `EvaluateRequest` already carries `evaluation_id`; transfer exactly `evaluations/<evaluation_id>.json`, then call `load_evaluation(evaluation_id)` and validate its exact artifact, corpus, range, and execution provenance. Evaluation records are sibling-root immutable JSON, and exact loaders replace catalog scans and fuzzy lookup ([Issue 11 resolution](https://github.com/edoski/spice/issues/11#issuecomment-4957689163)). Missing ID, wrong embedded ID, parent mismatch, range mismatch, provenance mismatch, or non-success is a collection failure. Preserve input order and require all 45 before publishing the table.

`evidence.tsv` contains 45 successful evaluation rows in request order: `label`, `evaluation_id`, `artifact_id`, `corpus_id`, inclusive first/last parent block, and the approved metric columns. One final pointer-only row names the Issue-40 parity report without copying parity facts. The TSV is regenerated from the 45 exact records, not an authority. No SQLite result index, collection snapshot codec, scan, producer-coordinate match, or duplicated artifact manifest fields survive.

## Deletion test

The current benchmark package contains 18 Python files and 2,891 lines. Schema plus plan materialization account for 1,365 lines; submission/run-state/collection/result/index code accounts for 1,439 more. Its seven benchmark test files contain 2,259 lines; the benchmark CLI adds 176 source and 413 test lines; 23 benchmark YAMLs add 993 lines. These are checkout line counts, not a quality metric, but they show the explanatory surface: 40 classes, Cartesian dimension groups, problem grids, coordinate matching, a dependency graph, root/selection ledgers, four benchmark state files, a collection resolver, result schemas, and a SQLite projection.

The clean break can delete the benchmark schema, Cartesian axes, problem grids, materializer, coordinate dependency matcher, root and selection ledgers, external dependency syntax, benchmark YAML group, benchmark codecs, benchmark resume state, collection search, result record duplication, SQLite index, registry/special-case glue, and their transition-shaped tests. Sampler and HPO trial lifecycle stay inside Issue 29; host submission and attempts stay inside Issues 26/30; durable record fields stay inside Issue 34; transfer stays inside Issue 15.

Rejection rule: add a shared labelled interface only when two approved workflows need the same nontrivial label/dependency behavior and folding it into Issue 30 deletes more caller mechanics than its interface and tests add. Independent list enumeration does not qualify. Current evidence rejects a benchmark-owned plan and favors full deletion, with explicit typed lists calling the execution-owned plan/submission seam and exact-ID collection.

## Downstream Issue-29 handoff

Issue 10's selected-study source contains only `corpus_id` and `study_id`. Issue 49's final-K route must reuse the selected model/optimizer facts while semantic K changes. Issue 29 owns preset promotion before reuse and must preserve the selected `(study_id, trial_number)` provenance. Issue 18 accepts fully constructed `TrainRequest` values. It adds no runner override, copied study definition, extra studies, or provenance-losing baseline route.
