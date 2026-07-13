# Evaluation-suite and data identity findings

Status: read-only inventory for **Inventory research scripts, evaluation-suite data, and publication assets**. It reuses the 2026-07-10/11 pre-break evidence freeze; it does not rehash, regenerate, execute benchmarks, inspect active stores, or decide later ownership/removal.

## Scope and identity source

The [pre-break baseline](../spice-pre-break-evidence-baseline.md) and its 1,245-row [path/size/content manifest](../spice-pre-break-evidence-manifest.tsv) are the preservation source. The manifest SHA-256 is `213e31475bcd9a56e44385fcc61f9be40ff18d4120adfdf95063d742ccdb143b`; it already records all 830 historical-run files, 145 exports, 265 figures, and five catalog/index files. Corpus and model bytes were intentionally not copied or content-hashed.

The current worktree has no diff under `src/spice/conf/evaluations`, `src/spice/conf/evaluator`, or `src/spice/conf/benchmark`. The freeze found 22 suite files (410,385 bytes; 3,059 windows) with aggregate SHA-256 `d70761f916f3808054727cd66aeb45caaa2454c28b965eb640df543df35be977`; every suite validated through the typed loader, matched its filename to its top-level ID, had unique item IDs/coordinates, and used one window type. The three evaluator files total 301 bytes and have aggregate SHA-256 `7601110568c244a5bd1ff409e15840616ca43ea46f006b4800f335d0e252e97c`.

## Current evaluation-suite definitions

`EvaluationsSpec` requires a non-empty suite, validates a path-safe suite ID and unique item IDs. Timestamp suites also supply the earliest start as a training cutoff; block suites cannot. Benchmark plan materialization loads a named suite, makes one evaluate seed per item, removes the item ID and tags from the materialized window, and places the item ID in the `evaluations` dimension label. Tests cover timestamp fan-out/training-cutoff derivation and block fan-out.

| Suite ID | Windows | Type | Current benchmark consumer(s) | Inventory status |
| --- | ---: | --- | --- | --- |
| `avalanche_octane_1p53m_edge_case_recommended` | 216 | timestamp | none | maintained definition; unreferenced |
| `avalanche_octane_1p53m_train_cutoff` | 1 | timestamp | `lstm_36s_matched_training_budget_polygon_avalanche` | maintained definition |
| `avalanche_octane_edge_cases` | 6 | timestamp | `edge_case_baseline_36s` | maintained definition |
| `avalanche_octane_large_lstm_block300_quartile` | 216 | block | `lstm_36s_block300_quartile_eval` | maintained definition |
| `avalanche_octane_large_lstm_block_count_quartile` | 216 | block | `lstm_36s_block_count_quartile_eval` | maintained definition |
| `avalanche_octane_large_lstm_edge_case_recommended` | 210 | timestamp | `lstm_36s_large_polygon_avalanche_edge_eval` | maintained definition |
| `avalanche_octane_large_lstm_wall_clock_quartile` | 216 | timestamp | `lstm_36s_wall_clock_quartile_eval` | maintained definition |
| `ethereum_pectra_edge_cases` | 8 | timestamp | `ethereum_pectra_jun20_edge_case_lstm_36s`, `edge_case_baseline_36s` | maintained definition |
| `ethereum_pectra_jun20_block300_quartile` | 216 | block | `lstm_36s_block300_quartile_eval` | maintained definition |
| `ethereum_pectra_jun20_block_count_quartile` | 216 | block | `lstm_36s_block_count_quartile_eval` | maintained definition |
| `ethereum_pectra_jun20_edge_case_recommended` | 236 | timestamp | `ethereum_pectra_jun20_edge_case_lstm_36s` | maintained definition |
| `ethereum_pectra_jun20_wall_clock_quartile` | 216 | timestamp | `lstm_36s_wall_clock_quartile_eval` | maintained definition |
| `ethereum_pectra_smoke` | 1 | timestamp | none | maintained definition; unreferenced |
| `nov9_2025_2h` | 1 | timestamp | `nov9_cutoff_36s_sweep` | maintained definition |
| `nov9_2025_day` | 1 | timestamp | `nov9_cutoff_36s_day_eval`, `nov9_cutoff_36s_warm_hpo` | maintained definition |
| `polygon_bhilai_1p53m_edge_case_recommended` | 215 | timestamp | none | maintained definition; unreferenced |
| `polygon_bhilai_1p53m_train_cutoff` | 1 | timestamp | `lstm_36s_matched_training_budget_polygon_avalanche` | maintained definition |
| `polygon_bhilai_edge_cases` | 6 | timestamp | `edge_case_baseline_36s` | maintained definition |
| `polygon_bhilai_large_lstm_block300_quartile` | 216 | block | `lstm_36s_block300_quartile_eval` | maintained definition |
| `polygon_bhilai_large_lstm_block_count_quartile` | 216 | block | `lstm_36s_block_count_quartile_eval` | maintained definition |
| `polygon_bhilai_large_lstm_edge_case_recommended` | 213 | timestamp | `lstm_36s_large_polygon_avalanche_edge_eval` | maintained definition |
| `polygon_bhilai_large_lstm_wall_clock_quartile` | 216 | timestamp | `lstm_36s_wall_clock_quartile_eval` | maintained definition |

The three unreferenced suites are exactly the two `1p53m_edge_case_recommended` suites and `ethereum_pectra_smoke`. Unreferenced means no current benchmark YAML selects them; it does not establish staleness or removal safety.

Evaluator identities are `poisson_replay` (7,200 seconds, 50 repetitions, `0.05/s`, seed 2026; `d2089acf1fc7bd75b563c49f84a1d369c91e8ad9d45f803470f06df90899f25c`), `block_poisson_replay` (1,200 blocks, 50 repetitions, `0.3/block`, seed 2026; `d2a6cdcd248abf9677772b49d5d95ef65f2e0963b9454a89b5caca15c45fb233`), and `block_poisson_replay_300` (300 blocks, 200 repetitions, `0.3/block`, seed 2026; `21461a5a941ec55da06fe6381e44b921ce264366ef50297198173db119ff60f0`).

## Results, exports, and figures

Eight historical collection snapshots contain 2,609 records. Two block-quartile snapshots remain reproducible through the current strict codec: 1,296 observations total, 648 each, and therefore populate the ignored `benchmarks/results.sqlite` projection (8,577,024 bytes; SHA-256 `ba70a8f65e9210edc2cfee63243d69e46f55235f5b78f39d7dd5cdd83bf724b0`). The other six are archival-only under current code: they declare schema version 1 but fail strict `BenchmarkCollectionSnapshot` validation. This is codec staleness, not evidence that their observations are invalid.

`benchmarks/exports` and `benchmarks/figures` are ignored by Git. The frozen inventory classifies them as archival generated assets: exports have 145 files, 231,911,606 bytes, 718,359 CSV rows, and 121,131 Parquet rows (tree SHA-256 `3fa9b351cda34052ab71e0f0ed0635f71d9cb0c01770c4f9eb75eb49b66d239d`); figures have 265 files, 33,206,764 bytes, comprising 99 PNG, 83 SVG, and 83 PDF files (tree SHA-256 `3d13652355a93abac965b2a22f67472a20359ff5355e6e35c2101c69001c069f`). Their individual paths, byte sizes, and SHA-256 values are frozen in the manifest.

These outputs are not presently reproducible as a set. Generator/config/renderer identity is absent for some files; the dirty renderer `benchmarks/scripts/render_lstm_block_count_quartile_results.py` cannot be attributed to existing exports. The freeze gives a concrete mismatch: merged delay exports have 183 rows while their three preserved collections hold only 30 records. Existing output is therefore archival evidence with unknown per-file provenance unless a specific file has a documented source chain.

Current scripts write or read outputs under these ignored locations: window scans write `benchmarks/exports/evaluation_window_scans`; renderers consume evaluation dimension labels from records; report Markdown files within exports reference adjacent joined/correlation/summary CSVs. No production module or test was found to load the ignored export/figure trees as runtime input. That is a consumer observation, not a deletion decision.

## Status and limits

- **Maintained:** tracked suite, evaluator, and benchmark definitions plus their typed loading/fan-out implementation and tests.
- **Reproducible, bounded:** the two readable block-quartile collections and their index projection, provided the frozen inputs and current strict codec remain available. A materialized plan still does not prove executable data/artifact roots.
- **Archival-only:** six historical collections rejected by current validation, and all frozen exports/figures. Preserve byte identity; do not normalize, regenerate, or infer current meaning.
- **Stale interfaces:** the six schema-v1 snapshots are incompatible with the current strict collection codec. No compatibility layer follows from this finding.
- **Unknown:** per-output generator/config/renderer provenance, corpus/model byte identity, and whether unreferenced suites have a thesis/publication role.

The baseline also found only eight of 23 benchmark definitions with every explicit corpus/artifact both catalogued and physically present. Active catalog hashes are point-in-time identities, not coherent export backups; local and university catalog/root counts differ. This inventory cannot establish full end-to-end reproduction, publication readiness, ownership, or removability.

## Sources

- [Pre-break evidence baseline](../spice-pre-break-evidence-baseline.md), sections 4–6.
- [Pre-break path/size/content manifest](../spice-pre-break-evidence-manifest.tsv).
- `src/spice/config/models.py`, `src/spice/benchmarks/plan_materialization/_expansion.py`, and `tests/benchmarks/test_plan_materialization.py`.
- Tracked YAML under `src/spice/conf/evaluations`, `src/spice/conf/evaluator`, and `src/spice/conf/benchmark`.
