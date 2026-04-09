# SPICE Temporal Baseline

Practical reproduction scaffold for the temporal module described in `ICDCS_2026.pdf`.

## Scope

- Build chain-local datasets from raw block data.
- Train baseline LSTM, Transformer, and Transformer-LSTM models.
- Evaluate training diagnostics on pre-evaluation history and paper-comparable temporal profit on the evaluation day.
- Prepare a later handoff to chain-specific hyperparameter optimization.

## Architecture

- `config.py`: typed experiment, training, and chain configuration.
- `contracts.py`: typed boundary contracts for raw rows, tensor batches, and model outputs.
- `env.py`: local `.env` loading and Alchemy URL resolution.
- `cryo.py`: cryo pull planning and execution.
- `io.py` and `enrich.py`: block-dataset loading plus `gas_limit` enrichment for cryo output.
- `features.py`, `datasets.py`, and `normalization.py`: feature engineering, supervised example construction, chronological splits, and train-only scaling.
- `models.py`, `torch_datasets.py`, `training.py`, and `evaluation.py`: PyTorch models, tensor adapters, training loop, and metrics.
- `pipeline.py`: training-dataset preparation, inference-dataset preparation, and one-run model training.
- `artifacts.py`: canonical training artifact manifest plus model save/load helpers.
- `reporting.py`: structured JSON report artifacts for training and simulation runs.
- `simulation.py`: paper-style evaluation-day temporal simulation.
- `cli.py`: Typer entrypoints for pull, enrich, train, and simulate commands.

## Recommended environment

- Python 3.11 or 3.12 for the most predictable PyTorch support.
- Apple Silicon is supported through the PyTorch MPS backend.
- Define `ALCHEMY_API_KEY` in a local `.env` before running data pulls.

## Planned workflow

1. Pull raw block data with `cryo`.
2. Enrich missing block fields if needed.
3. Build supervised datasets with fixed lookback and bounded delay budgets.
4. Train the 27-model baseline matrix into canonical artifact directories.
5. Run evaluation-day temporal simulations from persisted artifacts.
6. Start chain-specific HPO only after the baseline matrix is verified.

## First pilot

Use the dedicated pilot config to validate the full raw-data-to-training-and-simulation path before larger pulls:

1. `python -m spice_temporal.cli pull-blocks configs/pilots/ethereum-36s.yaml ethereum history --no-dry-run`
2. `python -m spice_temporal.cli enrich-blocks configs/pilots/ethereum-36s.yaml ethereum artifacts/pilots/ethereum-36s/raw/ethereum/history artifacts/pilots/ethereum-36s/enriched/ethereum/history`
3. `python -m spice_temporal.cli pull-blocks configs/pilots/ethereum-36s.yaml ethereum evaluation --no-dry-run`
4. `python -m spice_temporal.cli enrich-blocks configs/pilots/ethereum-36s.yaml ethereum artifacts/pilots/ethereum-36s/raw/ethereum/evaluation artifacts/pilots/ethereum-36s/enriched/ethereum/evaluation`
5. `python -m spice_temporal.cli train configs/pilots/ethereum-36s.yaml artifacts/pilots/ethereum-36s/enriched/ethereum/history artifacts/pilots/ethereum-36s/runs/ethereum/lstm-36s ethereum lstm 36`
6. `python -m spice_temporal.cli simulate configs/pilots/ethereum-36s.yaml artifacts/pilots/ethereum-36s/runs/ethereum/lstm-36s artifacts/pilots/ethereum-36s/enriched/ethereum/history artifacts/pilots/ethereum-36s/enriched/ethereum/evaluation`

The first pilot target is `Ethereum + 36s + LSTM`, using fixed chain block times and a 36-second maximum additional delay budget over next-block execution.

Training writes a canonical artifact directory containing:

- `artifact.json`: model and dataset contract metadata
- `model.pt`: trained model weights
- `train_report.json`: supervised training/test diagnostics
- `simulation_report.json`: paper-comparable evaluation-day temporal metrics

## Verification

- `ruff check src tests`
- `pyright`
- `PYTHONPATH=src pytest -q`

Typing is intentionally boundary-focused for now rather than repo-wide strict.

## Useful commands

- `python -m spice_temporal.cli show-config configs/baseline.yaml`
- `python -m spice_temporal.cli show-config configs/pilots/ethereum-36s.yaml`
- `python -m spice_temporal.cli plan-pull configs/baseline.yaml`
- `python -m spice_temporal.cli plan-pull configs/pilots/ethereum-36s.yaml`
- `python -m spice_temporal.cli pull-blocks configs/pilots/ethereum-36s.yaml ethereum history --no-dry-run`
- `python -m spice_temporal.cli pull-blocks configs/pilots/ethereum-36s.yaml ethereum evaluation --no-dry-run`
- `python -m spice_temporal.cli enrich-blocks configs/pilots/ethereum-36s.yaml ethereum <input-dir> <output-dir>`
- `python -m spice_temporal.cli train configs/pilots/ethereum-36s.yaml <history-dataset-path> <artifact-dir> ethereum lstm 36`
- `python -m spice_temporal.cli simulate configs/pilots/ethereum-36s.yaml <artifact-dir> <history-dataset-path> <evaluation-dataset-path>`
