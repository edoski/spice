# SPICE

SPICE is a temporal fee-timing pipeline for EVM chains. It acquires canonical block corpora, builds resolved feature tables through explicit feature families, tunes models, trains artifacts, and evaluates stored artifacts under real delay budgets.

## Stack

- `Typer` for the CLI
- `Pydantic` + `PyYAML` for config loading
- `SQLAlchemy Core` for SPICE-owned state
- `Polars` for corpus IO and validation
- `PyTorch` for modeling
- `Optuna` for tuning
- `web3.py` for RPC access

## Setup

```bash
brew install uv
uv sync --extra dev
source .venv/bin/activate
```

`uv` manages the repo-local `.venv/`. If you do not want to activate it, prefix commands with `uv run`.
Repo helper: `spice-sync-remote <branch>` pushes the branch to both `origin` and `giano-sync`.

## CLI

Local workflow commands:

```bash
spice acquire --preset icdcs_2026
spice train --preset icdcs_2026 --variant baseline
spice tune --preset icdcs_2026 --trial-count 20
spice evaluate --preset icdcs_2026 --variant baseline
```

Submitted workflow commands:

```bash
spice train --preset icdcs_2026 --submit --target disi_l40
spice tune --preset icdcs_2026 --trial-count 20 --submit --target disi_l40
spice evaluate --preset icdcs_2026 --variant baseline --submit --target disi_l40
```

Workflow stdout is intentionally compact:

- one header line with the selected facts
- a few milestone lines for real state changes
- one final result line

Examples:

```text
acquire dataset=icdcs_2026 chain=ethereum problem=icdcs_2026 provider=publicnode
acquire complete history=reused history_blocks=4096 evaluation=created evaluation_blocks=512

train dataset=icdcs_2026 chain=ethereum problem=icdcs_2026 prediction=candidate_offset_selection model=lstm variant=baseline
fit epoch=3/12 objective.profit_over_baseline=0.0184 validation.profit_over_baseline=0.0184 best_epoch=3 best.profit_over_baseline=0.0184
train complete artifact=outputs/artifacts/ethereum/... best_epoch=9 validation.profit_over_baseline=0.0211 test.profit_over_baseline=0.0179

tune dataset=icdcs_2026 chain=ethereum problem=icdcs_2026 feature_set=icdcs_2026 prediction=candidate_offset_selection model=lstm study=default trials=20
trial 4/20 complete value=0.0211 best_epoch=7
best improved trial=4 value=0.0211
```

Local config and storage commands:

```bash
spice config list provider
spice config show dataset icdcs_2026
spice config edit problem icdcs_2026
spice show dataset
spice show artifact --chain avalanche --dataset icdcs_2026 --model lstm --problem icdcs_2026 --variant baseline
spice delete artifact --chain avalanche --dataset icdcs_2026 --model lstm --problem icdcs_2026 --variant baseline
spice push dataset --chain avalanche --dataset icdcs_2026
spice pull artifact --chain avalanche --dataset icdcs_2026 --model lstm --problem icdcs_2026 --variant baseline
spice refresh catalog
```

## Config

Config ownership is split across [src/spice/config](src/spice/config):

- `registry.py`: named YAML discovery, validation, and canonical load/edit helpers
- `presets.py`: preset overlay models, single-parent `extends`, and request overlays
- `resolution.py`: workflow request resolution into one typed workflow config
- `models.py`: resolved runtime config models

Modeling workflows (`train`, `tune`, `evaluate`) use the CUDA runtime. Submission resolves the workflow locally, sends the resolved config snapshot to the target, and applies the target storage root before the Slurm job starts.

Named specs live under [src/spice/conf](src/spice/conf):

- `preset/`: workflow bundles and the user-facing experiment unit
- `dataset/`: evaluation-date selectors
- `chain/`: chain runtime specs
- `provider/`: HTTP RPC transport and per-chain endpoint specs
- `execution/`: internal submission target spec
- `problem/`: delay budgets and sampling contracts
- internal registry-loaded seams: `model/`, `feature_set/`, `prediction/`,
  `dataset_builder/`, `evaluation/`, `objective/`, `tuning_space/`

Rules:

- presets are the main workflow entrypoint
- internally, presets resolve as one overlay chain rather than one flat full spec
- workflow CLI composition is preset-first; only `--chain` remains as a seam selector
- run knobs stay explicit: `--dry-run`, `--trial-count`, `--delay-seconds`,
  `--study`, and `--variant`
- `provider` is preset-owned runtime config, not a workflow CLI selector
- presets may use one `extends: <preset>` parent; parent presets must be runnable
- child presets replace scalar/name fields and deep-merge only known config blocks
- `acquire` resolves the selected provider into one chain-specific RPC endpoint before runtime
- the execution target is selected with `--target`, validated through
  `execution/models.py`, and not stored in presets
- `problem.compiler.id` selects the temporal compiler
- `feature_set.family.id` selects the feature family
- `prediction.family.id` selects the prediction family
- `dataset_builder.id` selects the dataset preparation path
- `acquire` requests a cushioned bootstrap history window and allows one measured prefix refill
- `train` and `evaluate` validate that the selected feature graph matches the stored artifact

## Core Seams

Strong domain seams stay separate:

- feature family
- temporal compiler
- prediction family
- evaluator
- model family
- representation

Current shipped ids:

- feature families: `block_native`, `block_open_native`, `time_native`
- compilers: `timestamp_native`, `estimated_block`
- prediction families: `candidate_offset_selection`, `min_block_fee_multitask`
- evaluators: `poisson_replay`, `paper_fullset`, `paper_windowed`
- input normalization: `row_standard`, `window_weighted_standard`
- representation: `sequence_inputs`

## Output Layout

- catalog: `outputs/.spice/catalog.sqlite`
- history corpus: `outputs/corpora/<chain>/<corpus_id>/history/...`
- evaluation corpus: `outputs/corpora/<chain>/<corpus_id>/evaluation/...`
- corpus state: `outputs/corpora/<chain>/<corpus_id>/.spice/state.sqlite`
- tuned study state: `outputs/studies/<chain>/<study_id>/.spice/state.sqlite`
- model artifacts: `outputs/artifacts/<chain>/<artifact_id>/...`
- artifact state: `outputs/artifacts/<chain>/<artifact_id>/.spice/state.sqlite`

These roots are derived deterministically by `storage/identity.py` and
`storage/layout.py`. They are outputs of workflow resolution, not workflow
composition inputs, except for `--storage-root`.

Corpus ids identify raw chain/dataset storage only. Study ids include search
semantics such as sampler seed, pruning policy, tuning space, model, problem,
feature set, split, and training config; `trial_count` and `timeout_seconds`
are run limits and do not change study identity.

Users query by selectors such as `--dataset`, `--study`, `--model`, `--problem`, and `--variant`.
Those selector flags are storage selectors only. They identify existing records for
`show`, `delete`, `push`, and `pull`; they do not compose workflow configs.

## Baseline Replication

Thesis/internship baselines should be regenerated through normal workflows:

```bash
spice acquire --preset icdcs_2026 --chain ethereum
spice tune --preset icdcs_2026 --chain ethereum --trial-count 20
spice train --preset icdcs_2026 --chain ethereum --variant baseline
spice evaluate --preset icdcs_2026 --chain ethereum --variant baseline
```

Repeat the same preset family for `polygon` and `avalanche`, and use the LSTM,
Transformer, and Transformer-LSTM presets needed for the baseline matrix.

## Verification

```bash
uv run ruff check src tests
uv run pyright
uv run pytest -q
```
