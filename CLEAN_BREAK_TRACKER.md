# SPICE Clean-Break Tracker

## Done

- Core ML clean-break refactor implemented locally.
- Local `outputs/` artifacts migrated and renamed.
- Local migrated artifacts verified with `load_training_artifact()`: 38 loaded.
- Local A/B baseline ID map: `art_428e9ef4dda2748668ba` -> `art_c433194c8699a301f7c5`.
- Local verification passed: `ruff`, `pyright`, `pytest`, `vulture`, `compileall`, `uv lock --check`, `uv sync --frozen`.
- SSH university inventory: scratch root has 8 corpora, 41 study roots, and 433 artifact roots.
- SSH scratch preflight found 25 old study manifests and 431 old artifact manifests; empty placeholder roots are skipped.
- SSH clean-code-compatible dry-run found 21 migratable studies and 220 migratable artifacts.
- SSH obsolete roots skipped by design: old orphan/top-level study schemas and artifacts using feature generators not present in the clean code.
- SSH migration applied under `/scratch.hpc/edoardo.galli3/spice/outputs`.
- SSH migration backup/id-map: `/scratch.hpc/edoardo.galli3/spice/outputs/.spice/clean-break-backup-20260627T185552`.
- SSH migrated roots verified by ID map: 21 study roots and 220 artifact roots present, no legacy builder keys left in rewritten payloads.
- SSH rewritten A/B baseline loaded with `load_training_artifact()`: `art_428e9ef4dda2748668ba` -> `art_c433194c8699a301f7c5`.
- One-shot migration script deleted locally after local and SSH migration verification.
- Temporary remote migration directory `/scratch.hpc/edoardo.galli3/spice-clean-break-migration` deleted; no top-level `spice-*` directory remains in scratch.
- Local gates after SSH migration: `uv lock --check`, scoped `ruff`, `pyright`, `vulture`, and `pytest -q` pass.
- Clean-break refactor committed as `725c915 refactor(ml): clean break core training stack`.
- Clean-break refactor pushed to `university/main`.
- SSH university repo normalized to `/home/students/edoardo.galli3/spice`, clean at `725c915`.
- Scratch project/data root normalized to `/scratch.hpc/edoardo.galli3/spice`; no top-level `/scratch.hpc/edoardo.galli3/spice-*` remains.
- A/B benchmark config planned locally: `ethereum_pectra_jun20_edge_case_lstm_36s`.
- A/B benchmark shape: 1 train job plus 472 evaluate jobs over 236 June-20 Pectra edge windows.
- A/B baseline artifact: `art_c433194c8699a301f7c5`.
- A/B planned total-loss artifact: `art_956319e1b7a77b77dcfc`.
- A/B training corpus/cutoff match baseline: `cor_2edb8f7b84a4edf95e2b`, cutoff `2025-12-08T00:00:11Z`.
- A/B evaluation corpus/windows: `cor_7bea5a071afaf090c05a`, `ethereum_pectra_jun20_edge_case_recommended`.
- `uv audit --locked --python-platform x86_64-unknown-linux-gnu` still fails on locked third-party advisories in `aiohttp`, `mako`, `torch`, and `urllib3`.

## In Progress

- Commit and push the A/B benchmark config and tracker update.
- Submit the 36s Ethereum LSTM `validation_total_loss` A/B training job.
- Submit Pectra edge-case evaluation jobs for the current profit-objective baseline and the new total-loss artifact.

## Still To Do

- Record job IDs, log paths, artifact IDs, config diff, and economic metrics for the A/B decision.

## Known Blockers / Notes

- `uv audit` currently fails on locked third-party advisories in `aiohttp`, `mako`, `torch`, and `urllib3`.
- Whole-tree `ruff check .` includes unrelated untracked benchmark scripts; scoped `ruff check src/spice tests scripts` passes.
