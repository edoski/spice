# Issue 20 dependent completeness audit

Status: planning evidence for [Classify research scripts and generated
assets](https://github.com/edoski/spice/issues/20). Edo approved the two decisions below.
This audit changes no production code, test, configuration, tracked research source,
dataset, generated output, database, or remote state.

## Evidence boundary

The accepted source inventory is
[`research-evaluation-publication-assets-inventory.md`](../research-evaluation-publication-assets-inventory.md)
and its linked script, suite, baseline, and red-team reports. The byte authority for the
selected ignored slice is the existing 1,245-row
[`spice-pre-break-evidence-manifest.tsv`](../spice-pre-break-evidence-manifest.tsv),
SHA-256 `213e31475bcd9a56e44385fcc61f9be40ff18d4120adfdf95063d742ccdb143b`.
This audit rechecked every row against the current working copy: no path was missing and no
size or SHA-256 differed.

Tracked configuration and clean script source are identified by pre-break commit
`b9b9a53f42e3e88855ae5488ffff06d3d334fdee`. The user-modified
`render_lstm_block_count_quartile_results.py` has current SHA-256
`0e1aefbe0d20f28ff7417fc37946e4a3210fcdf165b74868a4f43c56ca66c836`;
its HEAD bytes have SHA-256
`403cbaa5314cd6c4521a54b947047a6c5bec0f49490ec3f9f7cd34ace7dcedd9`.
Historical outputs are attributed to neither revision.

Issue 18 deletes the generic benchmark engine and replaces it with ordered exact workflow
requests plus one all-or-nothing exact-ID, request-order TSV and a pointer to the separately
owned accelerator-parity report. Issue 48 retires selected windows, 300/1,200-block and
duration matrices, Poisson/random replay, old correlations and intervals, and their plots.
Issue 15 permits no application archive or per-record deletion surface. Issue 14 leaves raw
SQLite/catalog originals untouched.

## Approved classification

No existing research script, benchmark definition, evaluation suite, evaluator definition,
export, figure, run collection, or result index is a maintained current tool or current tool
output. A future current thesis table is the Issue-18 TSV; this ticket adds no producer,
renderer, reader, scan, filter, registry, or framework around it.

All 16 Python files under `benchmarks/scripts/` are tracked mode `100644`, total 6,374
physical lines and 227,114 current bytes. No production or CLI module imports them. Only the
suite writer has a test consumer, and that test exists solely for the retired suite path.

| Classification | Exact scripts | Historical input -> output record |
| --- | --- | --- |
| Frozen historical method | `scan_edge_case_windows.py`; `scan_wall_clock_quartile_windows.py`; `scan_block_count_quartile_windows.py`; `scan_ethereum_pectra_edge_case_windows.py` | Named local corpus Parquet/SQLite, cutoff and environment parameters -> ignored selected-window CSVs. Exact corpus bytes are absent, so this is method evidence, not a reproduction claim. |
| Frozen historical method | `render_delay_degradation_figures.py`; `render_edge_case_figures.py`; `render_ethereum_pectra_fee_scatter.py`; `render_ethereum_pectra_jun20_lstm_edge_figures.py`; `render_lstm_edge_case_cross_chain_figures.py`; `render_lstm_edge_case_class_only_figures.py`; `render_lstm_wall_clock_quartile_results.py`; `render_lstm_block_count_quartile_results.py` | Named ignored exports, historical collections, and sometimes corpus Parquet -> named CSV/Markdown and PNG/PDF/SVG outputs plus external Obsidian copies. Source/output attribution is incomplete. |
| Frozen historical method | `summarize_ethereum_pectra_edge_case_ci.py` | Named exports and artifact-local evaluation SQLite -> three ignored confidence-interval CSVs. It directly depends on a retired private schema. |
| Obsolete one-shot, source retained for lineage | `merge_ethereum_pectra_jun20_corpus.py` | Two named corpus roots and private state/Parquet internals -> destructive merged corpus assembly. |
| Obsolete one-shot, source retained for lineage | `write_evaluation_suite_from_window_csv.py` | Explicit CSV and suite id -> retired YAML evaluation suite. |
| Obsolete one-shot, source retained for lineage | `summarize_matched_lstm_training_fee_stats.py` | Three hard-coded corpus/artifact assumptions -> one six-row ignored training-fee CSV. |

All 16 leave the active tree after custody verifies. `benchmarks/scripts/.keep` is deleted.
The archive is non-runnable: no entry point, environment, test, converter, compatibility
layer, or installable package. Existing NumPy/Polars use creates no research interface;
Matplotlib and SciPy earn no direct or optional dependency here.

### Benchmark definitions

All 23 tracked files under `src/spice/conf/benchmark/` are clean, total 29,452 bytes,
3,734 authored seeds, and aggregate SHA-256
`587d98db2ac8ee3ad17478b630e71aba704656231e9d37e65c3f5e572b1f87ea`.
Their only active consumer is the deleted generic benchmark loader/materializer.

Archive these 18 because matching local historical run directories exist:

- `delay_degradation_eth_lstm_beyond_600.yaml`
- `delay_degradation_eth_polygon_lstm_330_900.yaml`
- `delay_degradation_extension.yaml`
- `delay_degradation_lstm_long_extension.yaml`
- `delay_degradation_short_window_fillin.yaml`
- `delay_degradation_sweep.yaml`
- `edge_case_baseline_36s.yaml`
- `ethereum_pectra_jun20_edge_case_lstm_36s.yaml`
- `large_capacity_hpo.yaml`
- `lstm_36s_block300_quartile_eval.yaml`
- `lstm_36s_block_count_quartile_eval.yaml`
- `lstm_36s_large_polygon_avalanche_edge_eval.yaml`
- `lstm_36s_matched_training_budget_polygon_avalanche.yaml`
- `lstm_36s_wall_clock_quartile_eval.yaml`
- `nov9_cutoff_36s_sweep.yaml`
- `nov9_cutoff_36s_warm_hpo.yaml`
- `old_window_comparison_36s.yaml`
- `safe_baseline_grid.yaml`

Clean-delete these five. They have no local run directory, collection, or generated-output
row and their planned work is superseded:

- `elapsed_position_ablation.yaml`
- `lookback_window_sweep.yaml`
- `nov9_cutoff_36s_day_eval.yaml`
- `priority_fee_ablation.yaml`
- `slot_spacing_sweep.yaml`

Historical `plan.jsonl` remains stronger runtime evidence than an authored benchmark YAML.
None of these definitions remains executable configuration.

### Evaluation suites and evaluators

The 22 tracked files under `src/spice/conf/evaluations/` are clean, total 410,385 bytes
and 3,059 windows, with aggregate SHA-256
`d70761f916f3808054727cd66aeb45caaa2454c28b965eb640df543df35be977`.
Archive these 21:

- `avalanche_octane_1p53m_edge_case_recommended.yaml`
- `avalanche_octane_1p53m_train_cutoff.yaml`
- `avalanche_octane_edge_cases.yaml`
- `avalanche_octane_large_lstm_block300_quartile.yaml`
- `avalanche_octane_large_lstm_block_count_quartile.yaml`
- `avalanche_octane_large_lstm_edge_case_recommended.yaml`
- `avalanche_octane_large_lstm_wall_clock_quartile.yaml`
- `ethereum_pectra_edge_cases.yaml`
- `ethereum_pectra_jun20_block300_quartile.yaml`
- `ethereum_pectra_jun20_block_count_quartile.yaml`
- `ethereum_pectra_jun20_edge_case_recommended.yaml`
- `ethereum_pectra_jun20_wall_clock_quartile.yaml`
- `nov9_2025_2h.yaml`
- `nov9_2025_day.yaml`
- `polygon_bhilai_1p53m_edge_case_recommended.yaml`
- `polygon_bhilai_1p53m_train_cutoff.yaml`
- `polygon_bhilai_edge_cases.yaml`
- `polygon_bhilai_large_lstm_block300_quartile.yaml`
- `polygon_bhilai_large_lstm_block_count_quartile.yaml`
- `polygon_bhilai_large_lstm_edge_case_recommended.yaml`
- `polygon_bhilai_large_lstm_wall_clock_quartile.yaml`

The two unreferenced `1p53m_edge_case_recommended` suites remain evidence because matching
frozen scan outputs exist. Clean-delete only `ethereum_pectra_smoke.yaml`: it has no current
consumer, run, or frozen output evidence.

Archive all three tracked Poisson evaluator YAMLs as retired historical inputs:
`poisson_replay.yaml`, `block_poisson_replay.yaml`, and
`block_poisson_replay_300.yaml`. None remains wheel configuration. `pyproject.toml`
currently packages all `src/spice/conf/**/*.yaml`; Issue 32 owns the mechanical wheel and
dependency policy after this content decision removes these directories from the active
set.

## Generated and historical bytes

| Group | Files | Bytes | Classification and consumer value |
| --- | ---: | ---: | --- |
| Historical run tree | 830 | 35,069,893 | Frozen source evidence. Eight collection snapshots contain 2,609 records; current code reads only two. No compatibility reader follows. |
| Window-scan exports | 93 | 228,499,086 | Frozen historical inputs for selected suites/renderers. Missing corpus bytes prevent a complete reproduction claim. |
| Other analysis exports | 52 | 3,412,520 | Frozen observations and reports; some values are absent from the partial SQLite index. |
| Renderer figures | 262 | 31,170,585 | Frozen PNG/PDF/SVG outputs. Existing renderer source is possible lineage, not proven attribution. |
| Paper-reference images | 3 | 2,036,179 | Frozen derivatives. The external thesis PDF remains a pointer only. |
| SQLite/catalog rows | 5 | 9,089,024 | Frozen identity only; originals remain untouched in place under Issue 14. No copy, transfer, deletion, or reader. |

The exports tree is 145 files and 231,911,606 bytes; the figures tree is 265 files and
33,206,764 bytes. All 410 generated files are ignored and frozen. This includes the two
orphan corrected Ethereum PNGs that have no producer in the current tracked renderers.
Publication use remains incomplete: external Obsidian copies and the thesis PDF are not
manifest rows, and current documentation cannot turn them into reproduced outputs.

The current `benchmarks/README.md`, `src/spice/benchmarks/ARCHITECTURE.md`,
`src/spice/benchmarks/IMPLEMENTATIONS.md`, and `PROGRESS.md` still call run directories,
`results.sqlite`, generic CSV exports, selected windows, and Poisson replay active or
rebuildable. Issues 18, 20, and 48 supersede those claims. Later documentation work should
replace them; they do not preserve code or data interfaces.

## Approved custody and sequencing

Custody is one owner-private, non-runnable operator archive outside the repository, wheel,
application, and clean storage root. Its path and host are runtime-only operator facts and
are never written into SPICE code, CLI, configuration, records, or documentation. It has no
archive manager, service, reader, schema, version marker, converter, environment, retention
framework, or restore behavior.

The archive contains exact source bytes for all 16 scripts, both known block-count renderer
variants, the 18 benchmark definitions, 21 suites, three evaluators, Issue-8 evidence,
historical `pyproject.toml`/`uv.lock` identities, all 830 historical-run files, all 145
exports, and all 265 figures. Existing per-file and aggregate hashes are the verification
authority; no second manifest is created. Access is Edo/operator-only. The archive remains
until Edo later authorizes retirement of the whole archive.

Movement is a one-time operator-only filesystem action:

1. Recheck the approved source set and existing hashes before movement. Capture both known
   block-count renderer variants before the dirty working copy or tracked source can be
   removed.
2. On the same filesystem, an ordinary rename may move the exact approved working-copy
   trees into custody.
3. Across filesystems, copy the exact approved set, verify the destination with the existing
   approved hashes and manifest, then remove only the specifically approved working copies.
4. Remove tracked active scripts/configuration through the later clean-break implementation
   only after their archive source bytes verify. Remove no extra file by directory inference.
5. Leave all five raw SQLite/catalog rows untouched in their original locations. Do not
   infer deletion or movement from their manifest membership.
6. Keep only a pointer to the external thesis PDF. Remove an Obsidian duplicate only after
   independent byte equality with an archived figure; leave every unverified external copy
   untouched.

The archive never feeds the clean root or Issue-14 sanitized public bundle. Same-filesystem
rename or cross-filesystem copy/verify/remove is operator procedure, not a project command or
implementation requirement.

## Dependent ownership audit

| Owner | Consequence from Issue 20 |
| --- | --- |
| Issue 14 | Raw SQLite/catalog originals and sanitized neutral-export rules remain unchanged. The private archive is not the public neutral bundle. |
| Issue 15 | No application archive, restore, retention, cleanup, or per-record deletion interface is introduced. Whole-archive retirement needs a later Edo decision. |
| Issue 18 | The only current evidence-publication contract remains ordered exact requests -> exact evaluation IDs -> all-or-nothing request-order TSV plus parity-report pointer. No old reader, SQLite, scan, filter, or generic export survives. |
| Issue 32 | Zero old research script or suite earns wheel ownership, Matplotlib, or SciPy. Issue 32 still owns package-selection mechanics and all unrelated dependencies. |
| Issue 35 | Its body is stale where it asks to port a maintained scanner, summarizer, and renderer, add scan/filter/generic export behavior, or model artifact deletion. There are zero maintained old consumers; Issues 18 and 15 prohibit those surfaces. Issue 35 remains blocked by Issues 30 and 34 after Issue 20 and must reconcile its own remaining exact-collection question. Issue 20 does not edit or resolve it. |

Native graph inspection confirms Issue 20 remains a direct child of the open Wayfinder map,
is blocked only by closed Issues 8 and 18, and directly blocks open Issues 32 and 35. Closing
Issue 20 alone does not unblock Issue 35 because Issues 30 and 34 remain open.

The audit found no new consequential Issue-20 choice. The two approved decisions and the
ownership handoffs above form a complete contract.

## Completion verification

After Edo approved the compact whole contract, the GitHub connector posted exactly one
Resolution comment, `4958680081`, and closed only Issue 20 as completed. A fresh map read
was followed by one title-linked Issue-20 pointer appended to **Decisions so far**; a second
connector read found that pointer exactly once and the map remained open.

Native graph verification found the closed issue still directly under map 1, with closed
blockers 8 and 18. No frontier issue became ready: Issue 32 remains blocked by open Issues
25, 27, and 33, while Issue 35 remains blocked by open Issues 30 and 34. No archive movement,
production/data mutation, sibling edit, or cutover action occurred during completion.
