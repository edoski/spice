# Asset inventory red-team findings

Date: 2026-07-11. Scope: independent read-only review for **Inventory research
scripts, evaluation-suite data, and publication assets**. This is not a retention
or deletion decision.

## Frozen evidence is complete only for its declared slice

`spice-pre-break-evidence-manifest.tsv` has 1,245 data rows (1,246 lines including
its header); every listed relative path existed during this review. It groups as 414
`benchmarks/` paths (274,170,530 bytes) and 831 `outputs/` paths (35,106,757 bytes).
This agrees with the baseline's stated 145 derived exports, 265 figures, 830
historical-run files, and five catalog/result-index files. The one extra `outputs/`
path is therefore a catalog/result-index item, not evidence that the baseline's 830
run-file count is wrong.

The manifest excludes the source side of the evidence chain: `benchmarks/scripts/`,
all benchmark/evaluation YAML, raw corpus bytes, model/artifact bytes, root-local
`.spice` state, the thesis PDF, and the Obsidian figure copies. It is a content
identity for selected outputs, not a reproducibility manifest and not an exhaustive
publication-asset inventory. Preserve that distinction in the ticket report.

## Status claims must be evidence-qualified

| Proposed status | Evidence needed before use | Current constraint |
|---|---|---|
| maintained | tracked source plus an active caller/declared workflow | An ignored export/figure is not maintained merely because its renderer remains. |
| reproducible | identified inputs, source revision, environment, and a read-only-safe command | Baseline says many exports lack renderer hash; six of eight historical collections fail the current strict codec. |
| generated | a concrete producer and matching input/output provenance | Writer code alone proves a possible producer, not that it produced an existing file. |
| archival-only | explicit historical provenance or documented retention purpose | `ARCHIVE.md` and `PROGRESS.md` call several old names/evidence historical, but this cannot be projected onto every similarly named asset. |
| stale / unknown | positive contradictory evidence / insufficient evidence | No-load or no-current-reference is insufficient for either deletion or “stale”. |

`docs/research/spice-pre-break-evidence-baseline.md` establishes that only two
historical block-quartile collections load in current code and that the result index
omits older observations. Thus index visibility and current loader success are not
valid filters for publication or archival value.

## Publication provenance breaks outside this checkout

Five renderer families write a second copy to the hard-coded external path
`/Users/edo/Documents/Obsidian/the-vault/notes/benchmark_figures`: edge-case cross
chain, wall-clock quartile, edge-case class-only, block-count quartile, and Ethereum
June edge figures. The paper audit separately reads
`/Users/edo/Documents/Obsidian/the-vault/university/Thesis/ICDCS_2026.pdf`. Neither
external tree is covered by the 1,245-row manifest. A final inventory must record
them as external/unverified publication dependencies, never as absent or stale.

Several renderer and scan scripts create output directories and overwrite named CSV,
Markdown, or figure paths. Do not execute them as inventory validation. Static script
inspection can establish intended output paths only; rerunning could destroy the
frozen identity of ignored assets.

## Sensitive and mutable local inputs

`.gitignore` excludes `.env`, `.spice/`, `outputs/`, `data/`, `benchmarks/exports/`,
`benchmarks/figures/`, and SQLite journal sidecars. The ignored tree includes
`.spice/serving.env`, `.spice/sepolia-deployer.json`, `.spice/serving.sqlite`, and
multiple SQLite databases. Their names make them potential secret or live-state
material. Inventory rows should contain paths, type, byte count, and digest only
where approved; do not publish contents, connection strings, keys, or raw database
copies. SQLite `-wal`/`-shm` files are mutable companions, not standalone artifacts.

## Required validation constraints

1. Treat the baseline manifest SHA-256 and its capture window as the authoritative
   identity for its selected slice; do not regenerate it while concurrent work uses it.
2. For every claimed figure/export, retain producer script path, input identities,
   output identity, and external-copy location separately. Missing links mean
   `unknown`, not `generated` or `reproducible`.
3. Keep raw corpora, models, state stores, and external thesis/vault assets as
   references with availability/provenance limits; no copying or hashing sweep is
   required to make the inventory useful.
4. Explicitly separate active suite definitions (22 YAML suites and 3,059 windows in
   the baseline) from historical run collections, derived exports, and figures. A
   suite being unreferenced by a current benchmark does not make its derived assets
   removable.

Primary evidence: `.gitignore`; `benchmarks/scripts/*.py` static output paths;
`docs/research/spice-pre-break-evidence-manifest.tsv`;
`docs/research/spice-pre-break-evidence-baseline.md`; `PROGRESS.md`; `ARCHIVE.md`.
