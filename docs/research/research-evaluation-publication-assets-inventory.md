# Research, evaluation, and publication asset inventory

Status: frozen read-only inventory for [Inventory research scripts, evaluation-suite data, and publication assets](https://github.com/edoski/spice/issues/8). It makes no retention, deletion, architecture, or thesis-claim decision.

Scope and method: tracked sources and ignored local evidence were inspected without executing scripts, querying mutable stores, copying data, or regenerating the existing evidence manifest. The authoritative point-in-time asset identity is [`spice-pre-break-evidence-manifest.tsv`](spice-pre-break-evidence-manifest.tsv), 1,245 rows and SHA-256 `213e31475bcd9a56e44385fcc61f9be40ff18d4120adfdf95063d742ccdb143b`; its companion baseline records the capture window and exclusions.

## Inventory

| Group | Identity and size at freeze | Inputs / current consumer | Status | Reproducibility limitation |
|---|---|---|---|---|
| Benchmark definitions | 23 tracked YAML, 29,452 bytes, 3,734 expanded seeds | `src/spice/conf/benchmark/`; benchmark CLI and materializer | maintained source | Only eight definitions have all explicit roots catalogued and present; parsed/materialized does not prove executable. |
| Evaluation suites | 22 tracked YAML, 410,385 bytes, 3,059 windows; manifest `d70761f916f3808054727cd66aeb45caaa2454c28b965eb640df543df35be977` | `src/spice/conf/evaluations/`; typed suite loader and benchmark references | maintained source; three unreferenced suites are archival/unknown, not removable | 1,763 timestamp and 1,296 block windows; suite bytes reproduce selection definitions, not corpus/artifact availability. |
| Evaluator definitions | 3 tracked YAML, 301 bytes | `src/spice/conf/evaluator/`; replay registry | maintained source | Freeze identifies parameters, not historical result provenance. |
| Research/benchmark scripts | 16 tracked Python scripts, 6,374 HEAD physical lines / 424 KiB total (plus `.keep`) | `benchmarks/scripts/`; direct user invocation; no production import surface found | lifecycle unknown; individual methods are reproducible only conditionally or archival-only | Scripts require ignored exports, local corpora/catalogs, or artifact SQLite state; no script establishes that its historical outputs can be regenerated now. |
| Derived exports | 145 ignored files, 231,911,606 bytes | `benchmarks/exports/`; renderer/scan scripts | generated evidence, publication-critical candidate | Complete path/size/hash identities are in the frozen manifest; source-run, renderer revision, and all private inputs are not universal provenance. |
| Figures | 265 ignored PNG/PDF/SVG files, 33,206,764 bytes | `benchmarks/figures/`; renderer scripts and external Obsidian copy targets | generated publication asset, archival until claim is approved | A figure is reproducible only with its exact export, renderer revision, Python environment, and any private source state. |
| Results and artifact state | ignored `benchmarks/results.sqlite` (9.1 MiB), historical run tree and local catalogs | scripts, result index, artifact readers | archival-only / partial current consumer | Eight snapshots hold 2,609 records, but current code reads only two block-quartile snapshots (1,296 observations); never treat the current index as complete history. |

Sources: [`spice-pre-break-evidence-baseline.md`](spice-pre-break-evidence-baseline.md) §§4–5; [`.gitignore`](../../.gitignore); [`benchmarks/README.md`](../../benchmarks/README.md); `src/spice/benchmarks/collection_resolver.py`; `src/spice/evaluation/config.py`.

Detailed read-only evidence: [tracked-script inventory](issue-8/ticket-8-research-script-inventory.md), [evaluation-suite/data findings](issue-8/evaluation-suite-data-findings.md), and [independent red-team findings](issue-8/inventory-redteam-findings.md).

## Script and publication provenance

The tracked scripts divide by direct evidence, not a deletion judgement:

| Script family | Paths | Source state and dependencies |
|---|---|---|
| Corpus assembly | `merge_ethereum_pectra_jun20_corpus.py` | Reads local corpus `.spice/state.sqlite` and corpus roots. Reproducible only where those private/local roots remain. |
| Window scans and suite writer | `scan_*_windows.py`, `write_evaluation_suite_from_window_csv.py` | Scans read ignored `outputs/corpora/*/.spice/state.sqlite` or exports and write ignored window CSV/YAML candidates. These are reproducible methods only with the named local corpus state. |
| Result summaries | `summarize_ethereum_pectra_edge_case_ci.py`, `summarize_matched_lstm_training_fee_stats.py` | Read artifact SQLite or fixed artifact IDs and write exports. The former explicitly constructs artifact-state paths; the latter names historical artifact references. |
| Figure renderers | `render_*.py` | Read ignored CSV exports and write `benchmarks/figures`. Five renderers also write to `/Users/edo/Documents/Obsidian/the-vault/notes/benchmark_figures`; this private destination is provenance, not a portable output contract. |

The 145 exports and 265 figures are intentionally ignored by [`.gitignore`](../../.gitignore). Their tracked renderers prove a possible transformation for named inputs, not that they produced an existing file or a complete chain of custody. In particular, the pre-break baseline records a dirty `render_lstm_block_count_quartile_results.py` and states that historical exports do not universally store renderer hashes. Results must not be attributed automatically to either the dirty or HEAD revision.

## Classification rules and frozen limitations

- **Maintained** means tracked source with a current loader, CLI, or direct research workflow. It does not mean validated for the eventual thesis.
- **Reproducible** requires all named versioned inputs, environment, and source state. No ignored export/figure gets this label solely because a renderer exists.
- **Archival-only** means preserved historical evidence with incomplete current loading or unavailable inputs. It remains evidence.
- **Generated** means a derived local file with frozen identity, not a claim of scientific validity.
- **Stale** is not assigned from lack of a current consumer. **Unknown** applies where provenance or intended thesis use cannot be established from the working tree.

No asset is classified safe to remove. The later owner decision must select any maintained/frozen/archive bundle only after the temporal protocol and permitted thesis claims are approved.

## Preservation pointers

Use the existing manifest for all export/figure path, size, and SHA-256 detail; creating a second machine manifest would duplicate it without preservation value. Preserve these contextual limits with it:

- corpus and model bytes were deliberately not copied or content-hashed;
- local and university catalogs disagree on roots, and the university environment cannot import Torch;
- ignored asset directories may contain the only publication evidence;
- current code's partial collection support is not evidence that unsupported snapshots, exports, or figures are obsolete.
- the external Obsidian figure copies and thesis PDF are not manifest rows; they are external/unverified dependencies rather than absent assets.
