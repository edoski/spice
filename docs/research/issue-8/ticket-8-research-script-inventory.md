# Ticket 8: tracked research-script inventory

Scope: the sixteen tracked Python files under `benchmarks/scripts/`, read at the
pre-break baseline `b9b9a53f42e3e88855ae5488ffff06d3d334fdee`. This is an
inventory, not a retention or removal decision. It reuses the frozen evidence
manifest and benchmark audit; it neither reads nor regenerates ignored outputs.

## Evidence and limits

The frozen baseline records 16 scripts and 6,374 physical lines
([crosscut red-team](../issue-1/clean-break-crosscut-red-team.md), “Benchmark scripts and
research assets are hidden consumers”). `render_lstm_block_count_quartile_results.py`
is user-modified in the current worktree; its current and HEAD hashes differ, so
historical outputs cannot be attributed to either renderer version
([pre-break baseline](../spice-pre-break-evidence-baseline.md), “Code and lock
identity”). All sizes and hashes for the 145 exports and 265 figures remain in
the existing 1,245-row [evidence manifest](../spice-pre-break-evidence-manifest.tsv);
this inventory deliberately does not duplicate it.

All sixteen scripts are standalone: no `spice` console entry point includes them
([pyproject.toml](../../../pyproject.toml)); repository search finds no production
or test importer. They are therefore research consumers, not operator interfaces.
The normal benchmark path is the `spice benchmark` CLI and its durable run
directory/collection/index contract ([benchmark README](../../../benchmarks/README.md)).

`numpy` and `polars` are declared dependencies, but these scripts additionally
import `matplotlib`, several import `scipy`, and one imports `sqlite3`; neither
plotting nor SciPy is declared in the project dependency list
([pyproject.toml](../../../pyproject.toml)). The pre-break audit already records
that this makes current research reproduction incidental rather than declared
([crosscut red-team](../issue-1/clean-break-crosscut-red-team.md)).

Status vocabulary below is observational: **reproducible** means inputs and
dependencies are named in the repository, not that they are present; **archival-only**
means the script names private state or a historical path; **unknown** means the
inventory cannot establish the input provenance. No script is labelled **maintained**:
tracked source plus no CLI/test consumer is insufficient evidence. No script is labelled
**stale**: a missing current consumer is likewise insufficient evidence for obsolescence.
It makes no later owner decision.

## Manifest

| Script | HEAD lines; first introduced | Direct inputs and outputs | Observed status |
|---|---:|---|---|
| `merge_ethereum_pectra_jun20_corpus.py` | 134; `e804880b` (2026-06-29) | Two hard-coded Ethereum corpus IDs; `.spice/state.sqlite`, Parquet blocks and private `split_materialization._parquet_io`; creates/replaces a merged corpus state. | archival-only; mutating and tied to private storage internals. |
| `scan_edge_case_windows.py` | 431; `e804880b` | Required `SPICE_SCAN_CHAIN`, corpus IDs, cutoff and prefix; corpus Parquet plus state SQLite; writes five `benchmarks/exports/evaluation_window_scans/*` CSVs. | reproducible only with the named local corpus/state and environment. |
| `scan_wall_clock_quartile_windows.py` | 396; `e804880b` | Same required scan environment; corpus Parquet/state SQLite; writes four scan CSVs. | reproducible only with the named local corpus/state and environment. |
| `scan_block_count_quartile_windows.py` | 277; `4b90a951` (2026-06-29) | Required scan environment, including corpus ID/cutoff/prefix; `outputs/corpora/.../blocks`; writes four block-window scan CSVs. | reproducible only with the named local corpus and environment. |
| `scan_ethereum_pectra_edge_case_windows.py` | 520; `e804880b` | Default historical corpus `cor_2edb8f7b84a4edf95e2b` or `SPICE_PECTRA_SCAN_CORPUS_ID`; Parquet; writes six scan CSVs. | archival-only default; alternate corpus provenance unknown. |
| `write_evaluation_suite_from_window_csv.py` | 100; `e804880b` | Explicit `--suite-id`, `--input`, `--output`; reads a window CSV and writes YAML. | reproducible utility if its CSV and requested suite contract are preserved. |
| `render_delay_degradation_figures.py` | 266; `0750f10a` (2026-05-18) | `delay_degradation_completed_{evals,ml_metrics}_merged.csv`; writes named figures. | archival-only until the two input exports and plotting dependency are bundled. |
| `render_edge_case_figures.py` | 289; `e804880b` | `edge_case_baseline_36s_evals_merged.csv`; writes named figures. | archival-only until the input export and plotting dependency are bundled. |
| `render_ethereum_pectra_fee_scatter.py` | 295; `e804880b` | Same edge-case merged export; writes a fee-scatter summary CSV and figures. | archival-only until input export and plotting dependency are bundled. |
| `render_ethereum_pectra_jun20_lstm_edge_figures.py` | 449; `e804880b` | Named scan CSV plus historical exports; writes joined/summary CSVs, figures, and an absolute Obsidian-vault copy. | archival-only: absolute user path and ignored inputs. |
| `render_lstm_edge_case_cross_chain_figures.py` | 622; `e804880b` | Per-chain joined exports, scan CSVs, and Ethereum joined export; writes cross-chain exports, figures, and Obsidian copies. | archival-only: ignored inputs and absolute user path. |
| `render_lstm_edge_case_class_only_figures.py` | 494; `e804880b` | `lstm_36s_edge_case_all_chains_joined.csv`; writes correlation CSV/Markdown, figures, and Obsidian copies. | archival-only: ignored input and absolute user path. |
| `render_lstm_wall_clock_quartile_results.py` | 709; `e804880b` | Historical/default benchmark `collection.json`, selected scan CSVs, environment-selected run dir; writes joined/correlation/summary/report exports, figures, and Obsidian copies. | archival-only: historical collection plus ignored scans and absolute user path. |
| `render_lstm_block_count_quartile_results.py` | 976; `7ce42888` (2026-06-29) | Historical/default benchmark `collection.json`, selected scan CSVs, optional run-dir/suffix environment; writes joined/correlation/summary/report exports, figures, and Obsidian copies. | unknown for exact historical provenance: renderer has an uncommitted diff. |
| `summarize_ethereum_pectra_edge_case_ci.py` | 251; `e804880b` | Edge-case and fee-scatter exports plus direct `evaluation_summary` query in artifact state SQLite; writes three CI CSVs. | archival-only: direct artifact SQLite schema and ignored inputs. |
| `summarize_matched_lstm_training_fee_stats.py` | 159; `e804880b` | Hard-coded historical artifact/corpus assumptions and Polars; writes `matched_lstm_36s_training_fee_stats.csv`. | unknown: no invocation contract or source export is recorded. |

First-introduced commits come from `git log --diff-filter=A`; they establish source
provenance, not output provenance. The pre-break baseline says only two of eight
historical collection snapshots currently load; six schema-v1 snapshots fail current
validation ([pre-break baseline](../spice-pre-break-evidence-baseline.md), “Historical
runs and results”). No renderer should be assumed able to recreate its associated
export merely because its source remains tracked.

## Input/output lineage seen in source

The four scanner scripts produce CSV candidates used by the quartile and edge-case
renderers. `write_evaluation_suite_from_window_csv.py` turns a selected CSV into
one YAML suite. The maintained configuration inventory has 22 typed suites, 3,059
windows, and an immutable definition-set hash in the [pre-break baseline](../spice-pre-break-evidence-baseline.md).
That inventory establishes identity of current suite definitions; it does not establish
which ignored scan CSV generated each one.

The figure/render/summarize scripts consume ignored `benchmarks/exports` and write
ignored `benchmarks/figures` (`.gitignore`), while the supplied manifest freezes their
path/size/content identities. The benchmark README calls named CSVs table/figure/appendix
inputs and rebuildable, not durable run state. Thus these files are **generated** in
the current benchmark model, but publication value is **unknown** without a paper or
thesis mapping. Generated does not mean safe to remove.

## Preservation facts for the next decision

- Exact archival replay needs each script revision, its named ignored CSV/figure inputs,
  collection snapshots or artifact SQLite where read, corpus IDs/Parquet where scanned,
  environment variables, and an environment containing Matplotlib/SciPy.
- The existing evidence manifest is the preservation pointer for ignored output bytes;
  it is not a source-to-output lineage graph.
- The two scripts with private imports/direct state mutation (`merge_...` and the CI
  summarizer) should not be run as inventory validation. This investigation performed
  no execution and changed no store.
