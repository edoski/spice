# Concrete Config Presets

Checked-in YAML presets define runnable experiments without Python edits. A surface is the one-off workflow preset; benchmarks are matrix/DAG wrappers over surfaces and overrides. Presets are current runnable architecture only; historical unsafe and estimated-block paths are documented in top-level `ARCHIVE.md`.

## Default Surface

`current_row_fee_dynamics` resolves:

```yaml
chain: ethereum
dataset: icdcs_2026
features: core_fee_dynamics
problem: current_row_nominal
dataset_builder: fixed_sequence_temporal
model: lstm
prediction: icdcs_2026
objective: profit_poisson_replay_2h_mean
acquisition: {provider: publicnode, id: default}
training: {id: default, split: default}
tuning: {id: default, space: lstm_fixed_context}
evaluation: {id: poisson_replay_2h_mean, delay_seconds: 36}
```

Requests may override surface fields by name. `evaluation.delay_seconds` is optional in the surface; resolution defaults it to `problem.max_delay_seconds` for evaluation workflows.

The surface YAML uses targeted nesting where the nesting matches ownership:

| Field | Meaning |
| --- | --- |
| `chain` | Chain preset used for runtime chain id, POA handling, and nominal block time. |
| `dataset` | Corpus/evaluation-date preset. |
| `features` | Feature catalog/output preset. |
| `problem` | Temporal problem preset. |
| `dataset_builder` | Training/evaluation dataset builder. |
| `model` | Model family config. |
| `prediction` | Prediction head/decoder semantics. |
| `objective` | Training/tuning objective. |
| `acquisition.provider` | RPC provider preset. |
| `acquisition.id` | Acquisition behavior preset. |
| `training.id` | Training hyperparameter preset. |
| `training.split` | Split preset. |
| `tuning.id` | Optuna runtime preset. |
| `tuning.space` | Tuning search-space preset. |
| `evaluation.id` | Evaluator preset. |
| `evaluation.delay_seconds` | Concrete evaluation delay; defaults to problem capability when omitted. |

## Current Presets

Chains: `ethereum`, `polygon`, `avalanche`.

Provider: `publicnode`.

Dataset: `icdcs_2026`, plus `icdcs_2026_3m` for large sample-count work through the `current_row_fee_dynamics_3m` surface.

Features: `core_fee_dynamics`. `core_fee_dynamics_elapsed_position` is a post-refactor ablation preset only; it is identical to `core_fee_dynamics` plus `elapsed_seconds`, a corpus-position signal.

`core_fee_dynamics` selects safe fee, gas-pressure, cadence/calendar, rolling log-fee, tx-count, and fee-history priority-fee outputs. It does not include elapsed-time/corpus-position outputs and does not expose raw block author/proposer metadata.

Problems:

- `current_row_nominal`: `observed_time_window` with `slot_spacing.id: nominal`.
- `current_row_recent_median`: same compiler with `slot_spacing.id: recent_median`.

Dataset builders:

- `fixed_sequence_temporal`: derives and persists one fixed context length from training data.
- `variable_sequence_temporal`: keeps compiler-derived variable context lengths.

Evaluators: `fullset`, `poisson_replay_2h_mean`, `poisson_replay_2h_total`, `zero_stop_rollout_fullset`, `anchor_basefee_fullset`.

Benchmarks: `large_capacity_hpo`, `lookback_window_sweep`, `sample_count_sweep`, and `slot_spacing_sweep`.

`large_capacity_hpo` preserves the original large-capacity cells and moves them to the current safe surface. `sample_count_sweep` uses `current_row_fee_dynamics` for `400k`/`1m` cells and `current_row_fee_dynamics_3m` for `3m` cells. `slot_spacing_sweep` compares `nominal` and `recent_median`; it replaces the old problem-family sweep name because the only remaining problem-family dimension is slot spacing.

## Invariants

Config ids name concrete specs. Surface fields point at existing presets. Objective benchmark ids must match training/tuning evaluation configs. Old unsafe and estimated-block runnable paths are archived, not available as current configs.
