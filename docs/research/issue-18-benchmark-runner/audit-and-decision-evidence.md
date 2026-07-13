# Benchmark-runner audit and decision evidence

Scope: read-only inventory plus the disposable prototype in this directory. No
production code, test, configuration, corpus, artifact, database, training run, or
evaluation run changed.

## Current implementation

`src/spice/benchmarks` has 18 Python files, 2,891 physical lines, 2,492
nonblank/noncomment lines, 40 classes, and 81 top-level functions. The classes include
20 Pydantic models with 136 fields, 18 dataclasses, one protocol, and one ordinary
resolver. The package exposes eight root symbols and 34 unique explicitly exported
symbols across its public modules.

| Files | Lines | Current responsibility | Clean-break disposition |
| --- | ---: | --- | --- |
| `schema.py`; `plan_materialization/__init__.py`, `_models.py`, `_planner.py`, `_expansion.py`, `_problem_grid.py`, `_dependencies.py`, `_roots.py`, `_selection.py` | 1,365 | YAML cases/steps, six axes, Cartesian expansion, problem grids, coordinate joins, dependency checks, selection/root ledgers, resolved snapshots | Delete. Complete workflow requests already contain exact IDs and semantic facts. No axes, grids, producer matching, root facts, or duplicated ledgers survive. |
| `_run_state_codec.py`; `runs.py` | 308 | `metadata.json`, `plan.jsonl`, `submission.jsonl`, `collection.json` codecs and run directories | Delete. Issue 30 owns one atomic direct plan/submission contract. No benchmark codec or old reader survives. |
| `submission.py` | 102 | Reopen persisted benchmark plan and call `ExecutionSession.submit_workflow` | Delete as a benchmark module. Hand already-constructed requests to the Issue-30/execution seam. |
| `collection.py`; `collection_resolver.py`; `result_records.py` | 553 | Pull whole artifacts, search evaluation summaries by evaluator/delay/provenance, duplicate plan/result facts | Delete. Transfer/load exact `evaluation_id`, validate the immutable record, then form one table row. |
| `_result_schema.py`; `result_index.py` | 536 | Three-table SQLite projection, filters, rebuild, and 30-column CSV export | Delete. The fixed thesis evidence needs one regenerated table, not a query subsystem. |
| `__init__.py` | 27 | Eight-symbol package facade | Delete with the package. |

No current benchmark module survives intact. The useful behavior—exact request order,
persist-before-work, completion checks, exact result identity, and complete evidence
publication—moves to its existing owner instead of being wrapped in another benchmark
interface.

The current “dependency graph” is not a general scheduler: it rejects forward edges
and validates an already ordered list. Submission is non-resumable once any submission
record exists. Plan and submission writes are non-atomic; duplicate submission IDs are
last-record-wins. Collection mutates local artifact storage before proving completeness,
then writes `collection.json` before a separate SQLite update. The result index drops
window metrics, history-row counts, and evaluation-row counts. These defects are not a
reason to repair the engine; their intended behavior belongs to Issues 15, 30, and 34.

## Configurations

The active benchmark group contains 23 YAML files and 993 lines: 43 cases and 64
authored steps (20 train, 2 tune, 42 evaluate). Seventeen files use case dimensions;
seven use problem grids; none uses step-local or scoring dimensions. Current specs
contain 18 `artifact_from` edges, 20 local `after` edges, and 13 literal external Slurm
dependencies. Twenty files currently materialize 3,294 rows. Three evaluation-only
files fail because materialization performs catalog lookup. Raw syntax describes 3,734
rows including those three.

| Active files | Current rows or failure | Why they create no clean runner requirement |
| --- | --- | --- |
| `delay_degradation_eth_lstm_beyond_600.yaml` (10); `delay_degradation_eth_polygon_lstm_330_900.yaml` (44); `delay_degradation_extension.yaml` (270); `delay_degradation_lstm_long_extension.yaml` (30); `delay_degradation_short_window_fillin.yaml` (20); `delay_degradation_sweep.yaml` (180) | 554 | Seconds/delay grids and generic problem expansion are superseded by independently trained fixed block horizons. |
| `lookback_window_sweep.yaml` (54); `slot_spacing_sweep.yaml` (36); `old_window_comparison_36s.yaml` (fails) | 90 plus failure | The approved context grid is explicit block counts; selected/multi-duration window machinery is retired. |
| `edge_case_baseline_36s.yaml` (69); `ethereum_pectra_jun20_edge_case_lstm_36s.yaml` (473); `lstm_36s_block300_quartile_eval.yaml` (648); `lstm_36s_block_count_quartile_eval.yaml` (648); `lstm_36s_wall_clock_quartile_eval.yaml` (648); `lstm_36s_large_polygon_avalanche_edge_eval.yaml` (fails); `nov9_cutoff_36s_day_eval.yaml` (fails) | 2,486 plus two failures | Representative-window, 300/1,200, quartile, Poisson/replay, and 648-window work is archival under Issue 48. |
| `large_capacity_hpo.yaml` (27); `nov9_cutoff_36s_warm_hpo.yaml` (27) | 54 | Issue 29 owns exactly three K=5 studies and their internal search. Legacy HPO plans are not authority. |
| `lstm_36s_matched_training_budget_polygon_avalanche.yaml` (2); `nov9_cutoff_36s_sweep.yaml` (18); `safe_baseline_grid.yaml` (18) | 38 | Old training/model cells are superseded by the Issue-49 ladder and final topology. |
| `elapsed_position_ablation.yaml` (36); `priority_fee_ablation.yaml` (36) | 72 | Stale feature selectors do not survive; priority-fee work is explicitly deferred. |

Recommendation: remove all 23 from executable configuration. Preserve frozen historical
run bytes, exports, figures, and the old SQLite file only as archival evidence. Add no
reader, converter, migration, alias, version marker, or active legacy config directory.

## Tests, callers, scripts, and documentation

| Surface | Inventory | Disposition |
| --- | --- | --- |
| `tests/benchmarks/test_benchmarks.py` | 6 source tests: packaged shapes, expansion, fields, problem grid, cycles/dependencies | Delete with schema/materializer. |
| `tests/benchmarks/test_plan_materialization.py` | 11: study/artifact derivation, catalog lookup, ledgers, suite fan-out, problem IDs | Delete. All assert superseded implementation shapes. |
| `tests/benchmarks/test_collection.py` | 5: run round trip, snapshot/index replacement, partial failure, transfer reuse | Replace only the exact-ID all-or-nothing evidence behavior at the final interface. |
| `tests/benchmarks/test_collection_resolver.py` | 12: evaluator/delay/provenance search and catalog/manifest mismatches | Delete. Exact `evaluation_id` removes the resolver/search algorithm. |
| `tests/benchmarks/test_result_index.py` | 6: SQLite upsert/rebuild/query/export/collision/limit | Delete with the index. |
| `tests/benchmarks/test_run_state_codec.py` | 4: JSONL shapes and project schema version | Delete. Issue 30 owns direct plan behavior; no compatibility tests. |
| `tests/cli/test_benchmark_cli.py` | 6: plan/submit/collect/index routing | Delete with the benchmark command tree; test any surviving thin routing at its owner. |
| `tests/benchmarks/test_window_suite_writer.py` | 1 archival evaluation-suite script test | Not runner behavior. Retain only if the archival script remains intentionally runnable. |

These eight files total 2,672 lines and 51 source test functions, expanded by
parametrization to 56 collected tests. Direct runner tests excluding the adjacent
window writer are 2,648 lines and 55 collected cases. A clean implementation should
keep one focused exact-ID evidence-table behavior test; Issue 30 separately tests exact
request persistence/submission. Add no deletion, transition, old-shape, or compatibility
tests.

The only production caller is `src/spice/cli/commands/benchmark.py`: eight commands
(`plan`, `submit`, `collect`, `show`, plus index `rebuild`, `show`, `list`, `export`)
across 176 lines. `src/spice/cli/app.py` registers the tree;
`src/spice/cli/options.py` defines run/index paths; `config/group_catalog.py` exposes
the benchmark group. No workflow imports benchmark code. The benchmark package instead
calls config resolution, storage/catalog, transfer, and `ExecutionSession` directly.
Remove the command tree, options, registration, and benchmark config-group entry. A
thin direct-plan command belongs to Issue 30 only if that issue approves it.

All 16 files under `benchmarks/scripts` are research/archive scripts, not production
runner callers. Four bypass the package and SQLite index by reading `collection.json`
directly: `render_ethereum_pectra_jun20_lstm_edge_figures.py`,
`render_lstm_block_count_quartile_results.py`,
`render_lstm_edge_case_cross_chain_figures.py`, and
`render_lstm_wall_clock_quartile_results.py`. Their frozen inputs do not justify a new
collection contract. Publication/cutover owners decide their eventual archival
disposition.

Direct benchmark documentation is 186 lines across
`src/spice/benchmarks/ARCHITECTURE.md`, `IMPLEMENTATIONS.md`, and
`benchmarks/README.md`. It documents ledgers, catalog matching, stable JSON shapes,
SQLite, and obsolete metrics. `ARCHITECTURE.md` says root kind `dataset` where code says
`corpus`; its stability claim conflicts with unreadable stored runs. Replace normative
text with the final explicit-stage/evidence-table contract; keep historical research
notes as history.

## Stored state

The checkout contains 195 run directories and eight `collection.json` snapshots. The
current strict codec loads only two 648-row snapshots; six are invalid under the current
models. `benchmarks/results.sqlite` is 9.1 MiB and contains 2 runs, 1,296 observations,
and 10,368 metric rows. Existing run trees total about 36 MiB.

This is archival evidence, not active state to migrate. The clean runner reads none of
it. Preserve required bytes through the publication/archive decision; do not alter or
delete them during implementation of the new contract.

## Actual finite topology

| Stage | New durable identities | Reuse/gate | Runner consequence |
| --- | ---: | --- | --- |
| Capacity/activity | 6 artifacts | Freeze winner per chain | One explicit ready train list. |
| UTC hour | 3 artifacts | Reuse 3 selected artifacts; freeze | New list created after the gate. |
| CE weighting | 3 artifacts | Reuse 3 selected artifacts; freeze | New list created after the gate. |
| Representative HPO | 3 studies | After feature/loss winners | One independent tune list; search stays inside Tune. |
| Context | 12 artifacts | Reuse 3 exact C=200 artifacts | Independent branch after HPO. |
| Horizon | 30 artifacts | 3 chains × 10 K values | Independent branch after HPO. |
| Sealed testing | 45 evaluations | Join branches and pass affordability gate | Exact evaluate list; one declared range per artifact. |
| Accelerator parity | 0 workflow requests | Issue-40 same-weight full/tail proof | One report pointer only; no fourth workflow or extension mechanism. |

The fixed minimum is 54 Train, 3 Tune, and 45 sealed-test Evaluate requests. HPO trial
operations stay inside Tune. Any later-approved validation `EvaluateRequest` values are
another explicit ready list and do not change the interface. Ordinary per-request Slurm
submission is assumed to have no material orchestration overhead.

## Alternatives and recommendation

| Alternative | Interface | Result |
| --- | --- | --- |
| Explicit named typed-request lists | Named stage builders return ordinary tuples of complete `WorkflowRequest` values; Issue 30 persists/submits them; collection loads exact evaluation IDs and writes one table | Recommended. Thesis choices remain visible and no benchmark-owned type is added. |
| Minimal labelled batch | `BatchPlan` + `BatchEntry{label, request, after}` + validation/map | Reject. The prototype creates seven stage batches and 102 entries but zero useful in-stage dependency edges. Owner/affordability gates, not scheduler edges, join the work. Reuse such fields only if Issue 30 independently needs them. |
| Current generic engine | Cases, six axes, grids, step graph, coordinate matching, three ledgers/facts, four state files, search, SQLite/query/export | Reject. It earns unknown future matrices and general historical queries, neither of which is in the bounded thesis destination. |

Delete the entire benchmark package and active benchmark config surface. Keep small
named stage construction beside the thesis workflow. Use the existing exact request
union and Issue-30 direct-plan/execution seam. Collect the exact evaluation IDs in
request order and regenerate one evidence TSV atomically after all records validate.
SQLite, Cartesian axes, a sampler, custom `BatchPlan`, dependency graph, project codec,
registry, resume state, producer-coordinate matching, collection search, and fixed
query/export interface do not survive.

## Approved owner decisions

Edo approved these decisions on 2026-07-13:

1. Delete the full benchmark package and use explicit named request lists. Add no
   benchmark-owned `BatchPlan`; permit no tiny replacement unless Issue 30 proves its
   own direct entry needs the same fields.
2. Publish one exact-ID, all-or-nothing, request-order TSV. Each row uses only
   Issue-34/48-approved identity, range, provenance, total, and metric fields. Add no
   SQLite index, collection snapshot, scan, filter, or generic export interface.

   Plain explanation: every evaluation request already contains its unique
   `evaluation_id`, like a claim-check number. Collection opens that one named file
   instead of searching for a likely match. It verifies the embedded artifact, corpus,
   and testing range, builds all 45 rows in memory, and replaces the prior TSV only when
   all 45 records pass. A missing or wrong record publishes nothing and preserves the
   prior table. SQLite and search solve discovery and ad-hoc-query problems this fixed
   thesis table does not have. The approved Issue-40 pointer follows those 45 rows; it
   is not an evaluation record and carries no copied parity facts.
3. Use ordinary per-request Slurm submission and assume it has no material orchestration
   overhead for this bounded thesis. Add no array/index language, numeric runner cap,
   concurrency controller, submission probe, fallback, or dormant abstraction. A truly
   new future requirement needs a fresh owner decision.
4. Remove all 23 YAMLs and current run/index formats from the active contract while
   preserving required historical bytes as static archive only. Add no legacy reader,
   migration, converter, alias, dual mode, or compatibility test.
5. Keep same-weight accelerator semantic-parity evidence under Issue 40. Issue 18's TSV
   may append only a pointer to that report after its 45 request-order evaluation rows.
   Add no fourth workflow, callback, plugin, registry, or other extension mechanism.

## Downstream handoffs

Issue 29 already owns preset promotion before reuse. Issue 10's selected-study source
contains only `corpus_id` and `study_id`; Issue 49 requires selected model/optimizer
facts to survive while K changes. Issue 29 must define a clean promotion into each
fully constructed final-K `TrainRequest`, preserving `(study_id, trial_number)`
provenance. Issue 18 adds no runner override, copied study definition, extra studies, or
provenance-losing baseline route.

Issue 30 owns the atomic direct plan, submission attempts, crash reconciliation, and
dependency job recovery. Issue 34 owns exact durable record/provenance fields. Issue 15
owns transfer and publication. Issues 26/30 own host/execution transport. Issue 18 does
not pre-empt those contracts.

## Dependent completeness audit

| Dependency | Remaining authority | Issue-18 boundary |
| --- | --- | --- |
| Issue 15 | Transfer, publication, and archive custody | The runner names exact evaluation IDs and one regenerated TSV; it adds no transport or archive contract. |
| Issues 26 and 30 | Training host, direct plan persistence, per-request submission, attempts, crash reconciliation, and dependency-job recovery | Fully constructed requests cross this seam unchanged. The approved ordinary-submission assumption leaves no runner scheduling choice. |
| Issue 29 | Search policy, selected-preset promotion, and `(study_id, trial_number)` provenance | The runner accepts the resulting complete `TrainRequest`; it cannot override or reconstruct the selection. |
| Issue 34 | Durable result and provenance fields | The TSV projects only fields approved there; Issue 18 invents no record shape. |
| Issue 40 | Same-weight accelerator parity semantics and evidence | Issue 18 appends one report pointer and owns no parity execution hook. |
| Issue 48 | Evaluator, declared block-origin range, and metric semantics | Issue 18 collects exact evaluation records; it owns no evaluator or benchmark loop. |
| Issue 49 | Canonical ladder, branch cells, gates, and any later validation requests | Each approved ready set becomes another explicit typed list; no runner interface changes. |

All dependent details either arrive inside a complete request/result or remain at their
named owner. None requires an Issue-18 type, extension point, policy, or unresolved
choice. The five approved decisions therefore form a complete Issue-18 contract.

## Whole-contract recap for authorization

Delete the benchmark package, its CLI/config surface, all 23 active YAMLs, and its
runner tests and formats from the active contract. Keep required historical bytes only
as static archive: no reader, shim, migration, converter, alias, dual mode, version
marker, or compatibility test.

After each owner gate, named thesis functions construct ordinary ordered lists of the
already-approved exact `TrainRequest | TuneRequest | EvaluateRequest` union. IDs are
minted once and complete requests are persisted before work. Issue 30 receives and
submits each request unchanged. Assume ordinary per-request Slurm submission has no
material orchestration overhead; add no benchmark plan, array/index language, numeric
cap, concurrency controller, dependency graph, probe, fallback, resume state, or
dormant extension.

The fixed minimum is 54 non-HPO Train requests, three Tune requests, and 45 sealed-test
Evaluate requests. HPO trials remain inside Tune. A later approved validation set is
another explicit list, not a new runner concept. Issue 29 promotes selected facts into
final-K requests while K changes and preserves `(study_id, trial_number)`; Issue 18
adds no override, copied study definition, extra study, or provenance-losing route.

Collect the 45 exact `evaluation_id` records in request order, validate the complete set
in memory, and atomically replace one TSV only when every record passes. Use only
Issue-34/48-approved fields. Add no SQLite index, collection snapshot, search, scan,
filter, producer-coordinate matching, sampler, registry, generic codec, or generic
export interface. After the 45 evaluation rows, append only a pointer to the
Issue-40-owned parity report; add no fourth workflow, callback, plugin, or registry.
