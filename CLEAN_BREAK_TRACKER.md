# SPICE Clean-Break Tracker

## Done

- Core ML clean-break refactor implemented locally.
- Local `outputs/` artifacts migrated and renamed.
- Local migrated artifacts verified with `load_training_artifact()`: 38 loaded.
- Local A/B baseline ID map: `art_428e9ef4dda2748668ba` -> `art_c433194c8699a301f7c5`.
- Local verification passed: `ruff`, `pyright`, `pytest`, `vulture`, `compileall`, `uv lock --check`, `uv sync --frozen`.

## In Progress

- Migrate SSH university artifact/study roots under `/scratch.hpc/edoardo.galli3/spice/outputs`.
- Keep the one-shot migration script until SSH migration is verified.
- Temporary migration tool restored at `scripts/rewrite_clean_break_storage.py`.
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
- `uv audit --locked --python-platform x86_64-unknown-linux-gnu` still fails on locked third-party advisories in `aiohttp`, `mako`, `torch`, and `urllib3`.

## Still To Do

- Commit the clean-break refactor.
- Push commit to `university`.
- Submit the 36s Ethereum LSTM `validation_total_loss` A/B training job.
- Submit pectra edge-case evaluation jobs for the current profit-objective baseline and the new total-loss artifact.
- Record job IDs, log paths, artifact IDs, config diff, and economic metrics for the A/B decision.

## Known Blockers / Notes

- `uv audit` currently fails on locked third-party advisories in `aiohttp`, `mako`, `torch`, and `urllib3`.
- Whole-tree `ruff check .` includes unrelated untracked benchmark scripts; scoped `ruff check src/spice tests scripts` passes.
