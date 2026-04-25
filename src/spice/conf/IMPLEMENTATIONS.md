# Concrete Config Presets

This package contains the checked-in YAML presets that define the experiments SPICE can run without writing Python. A preset is not executable by itself. It becomes executable after config resolution combines named YAML fragments into one typed workflow config.

The key idea is composition:

```text
surface preset
  -> chain + dataset + provider
  -> problem + feature_set + dataset_builder
  -> model + prediction + objective + evaluation
  -> training + split + tuning/tuning_space
  -> typed workflow config
```

## Mental Model

A YAML file names one concrete choice. For example, a model YAML chooses a neural network family and hyperparameters; an evaluation YAML chooses one evaluator engine and its sampling policy. A surface YAML is a higher-level recipe that points at many lower-level presets.

This keeps the command line small. A user can say "use the `same_block_closed` surface" and then override a small number of fields.

## Chains And Providers

Chain presets define blockchain identity and timing assumptions.

| Preset | Chain id | Nominal block time | POA middleware |
| --- | ---: | ---: | --- |
| `ethereum` | `1` | `12.0s` | no |
| `polygon` | `137` | `2.0s` | yes |
| `avalanche` | `43114` | `1.6s` | yes |

The provider preset `publicnode` supplies RPC endpoint templates plus HTTP timeout, retry count, and backoff. Acquisition code combines the chain and provider to build the actual RPC client.

## Dataset Presets

Dataset presets name the research corpus and the evaluation date. The evaluation date defines a UTC day:

```text
history window ends at evaluation day start
evaluation window covers that UTC day
```

Current dataset presets are `icdcs_2026` and `icdcs_2026_3m`. Both use evaluation date `2025-11-09`; the difference is the sample-count scale selected by paired problem presets.

## Acquisition Preset

`acquisition/default.yaml` defines the concrete RPC acquisition behavior:

```text
dry_run: false
chunk_size: 8192
rpc.batch_size: 256
rpc.min_batch_size: 64
rpc.concurrency: 48
rpc.concurrency_rungs: [8, 16, 24, 32, 48]
```

`chunk_size` controls parquet chunk materialization. RPC batch and concurrency fields control the adaptive pull scheduler.

## Problem Presets

Problem presets define how a training example becomes a decision problem.

`current_row_nominal_window` and `current_row_recent_delta_window` use the `timestamp_future_window` compiler. They define a time horizon in seconds and estimate action spacing with either nominal chain timing or recent observed block deltas.

`estimated_block_*` presets use the `estimated_block` compiler. They convert time horizons into block-step counts using nominal or calibrated intervals. The `3m` variants request larger sample counts. The `12s`, `24s`, and default variants choose different maximum decision delays.

## Feature-Set Presets

Feature-set YAMLs select output columns from a concrete feature family. Current families are:

| Family | Preset examples | Purpose |
| --- | --- | --- |
| `same_block_closed` | `same_block_closed_full`, `same_block_closed_no_time`, `same_block_closed_standard` | Uses information known after the current block is closed. |
| `block_open_lagged` | `block_open_lagged_full`, `block_open_lagged_calendar_only_time` | Uses current base fee plus lagged block signals available at the next block opening. |
| `timestamp_features` | `timestamp_features_baseline` | Uses timestamp-window features instead of fixed block-count windows. |

The suffix tells the ablation: full feature set, no time features, only calendar time, only time-since-start, or standard baseline.

## Dataset Builders

`standard_temporal` builds variable-context temporal samples after compiling the full feature/problem store.

`fixed_context_temporal` derives a fixed sequence length from the training segment and persists that length in runtime metadata. Current YAML bounds are `min_sequence_length: 64` and `max_sequence_length: 4096`.

## Model Presets

Current model families:

| Preset | Family | Use |
| --- | --- | --- |
| `lstm` | `lstm` | Recurrent sequence model. |
| `lstm_icdcs_2026` | `lstm` | LSTM tuned for the main experiment surface. |
| `transformer` | `transformer` | Attention encoder over temporal rows. |
| `transformer_lstm` | `transformer_lstm` | Transformer encoder followed by recurrent aggregation. |

All current modeling code expects CUDA for training.

## Prediction Presets

`candidate_offset_selection` predicts one offset distribution over candidate actions.

`icdcs_2026` uses `min_block_fee_multitask`, which predicts both a candidate offset class and a scalar minimum log fee during training. Inference still decodes candidate offsets.

## Evaluation And Objective Presets

Evaluation presets choose an evaluator engine:

| Preset | Engine | Main behavior |
| --- | --- | --- |
| `fullset` | `replay` | Evaluate every sample once with `total_ratio`. |
| `poisson_replay_2h_mean` | `replay` | Simulate Poisson arrivals in two-hour windows and average event-level ratios. |
| `poisson_replay_2h_total` | `replay` | Same sampling, aggregate by total fee sums. |
| `zero_stop_rollout_fullset` | `zero_stop_rollout` | Repeatedly apply predictions until offset `0` stops. |
| `anchor_basefee_fullset` | `anchor_basefee` | Compare realized fee against the anchor-row base fee. |

Objective presets choose what training and tuning optimize. `validation_total_loss` minimizes validation loss. `profit_poisson_replay_2h_mean` and `profit_poisson_replay_2h_total` maximize evaluation profit against the named replay benchmark.

## Surfaces

Surface presets are the highest-level experiment recipes. Current surfaces are `same_block_closed` and `block_open_lagged`.

They share the same broad research setting: Ethereum, PublicNode RPC, `icdcs_2026`, fixed-context temporal data, LSTM model, `current_row_nominal_window`, `min_block_fee_multitask`, and Poisson replay objective. They differ mainly in feature-set family.

## Execution Target

`execution/disi_l40.yaml` is the checked-in remote cluster target. CLI commands use `disi_l40` as their default target only at the command edge. Downstream execution and sync APIs receive an explicit target name.

## Invariants

| Rule | Why it matters |
| --- | --- |
| YAML ids name concrete specs. | Registries dispatch by id or engine. |
| Surface fields point at existing presets. | Config resolution must produce a complete workflow config. |
| Evaluation configs include `engine`. | Evaluator dispatch is engine-specific. |
| Objective benchmark ids match training/tuning evaluation configs. | Early stopping and tuning optimize the intended metric. |
| Execution target fallback lives in CLI commands. | Remote behavior stays explicit below the CLI layer. |

