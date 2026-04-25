# Configuration

SPICE config is a flat set of named YAML specs under [src/spice/conf](src/spice/conf).
The resolver uses PyYAML plus Pydantic models; there is no Hydra or OmegaConf layer.

## Surfaces

`surface/*.yaml` is durable benchmark context. A surface names stable specs and explicit workflow-section refs:

```yaml
chain: ethereum
dataset: icdcs_2026
provider: publicnode
problem: current_row_nominal_window
dataset_builder: fixed_context_temporal
prediction: icdcs_2026
acquisition: default
training: default
split: default
tuning: default
model: lstm
tuning_space: lstm_fixed_context
feature_set: same_block_closed_full
objective: profit_poisson_replay_2h_mean
evaluation: poisson_replay_2h_mean
delay_seconds: 36
```

Canonical mechanism surfaces:

- `same_block_closed`: paper-faithful unsafe same-block closed path.
- `block_open_lagged`: safe current-row sibling with lagged finalized block facts.

`model`, `feature_set`, `objective`, `evaluation`, `tuning_space`, `delay_seconds`, `study`, `variant`, and `trial_count` may be supplied by benchmark cases or CLI overrides when a surface leaves variation to the run request.

## Workflow Refs

Workflow sections are named refs, not inline blocks:

- `acquisition/default.yaml`
- `training/default.yaml`
- `split/default.yaml`
- `tuning/default.yaml`

Add a new named ref only when behavior differs. Small run variation should normally live in benchmark cases or CLI flags.

## CLI Fields

Workflow commands use `--surface`. `--preset` is intentionally unsupported.

Common selectors include `--chain`, `--problem`, `--feature-set`, `--objective`, `--evaluation`, `--model`, `--tuning-space`, `--training`, `--split`, `--tuning`, `--study`, `--variant`, `--delay-seconds`, and `--trial-count`. `acquire` also accepts `--acquisition` and `--dry-run`.

Resolution order:

1. load the surface
2. load referenced typed specs
3. apply CLI or benchmark case overrides
4. validate the final workflow config
5. derive storage identity from the resolved config

Storage identity does not include the surface or benchmark name. It changes when resolved semantic payloads such as model, objective, feature set, problem, training, split, tuning, or tuning space change.

## Benchmarks

`benchmark/*.yaml` defines experiment matrices and workflow DAGs. Each case has a scalar
`base`, standard `dimensions`, and one or more ordered `steps`. Global dimensions apply
to all steps; step dimensions apply only to that step. Local `after` dependencies become
Slurm dependencies during remote submission.

```yaml
cases:
  - id: lookback_window_sweep
    base:
      surface: block_open_lagged
      training: default
      split: default
      tuning: extensive
      study: lookback_window_sweep
    dimensions:
      models:
        - set:
            model: lstm
            tuning_space: lstm_large_capacity
      problems:
        - grid:
            base: current_row_nominal_window
            fields:
              lookback_seconds: [600, 900, 1200]
              sample_count: [1000000]
    steps:
      - id: tune
        workflow: tune
        set:
          objective: validation_total_loss
          evaluation: fullset
          trial_count: 100
      - id: train_tuned
        workflow: train
        after: [tune]
        set:
          objective: validation_total_loss
          evaluation: fullset
          variant: tuned
      - id: evaluate
        workflow: evaluate
        after: [train_tuned]
        set:
          objective: profit_poisson_replay_2h_mean
          evaluation: poisson_replay_2h_mean
          variant: tuned
          delay_seconds: 36
```

Planning validates every row before printing anything:

```bash
spice benchmark plan lookback_window_sweep
```

Remote submission writes local run state under `outputs/benchmarks/runs/<name>/<timestamp>/`
and uses the configured remote target:

```bash
spice benchmark submit lookback_window_sweep
```

Collection pulls remote studies/artifacts through storage sync and prints JSONL status.
Use `--write` only when all expected evaluation rows are complete; missing rows abort the
ledger write.

```bash
spice benchmark collect lookback_window_sweep
spice benchmark collect lookback_window_sweep --write
```
