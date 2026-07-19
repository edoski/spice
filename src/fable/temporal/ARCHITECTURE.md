# Temporal Preparation

FABLE (Fee Analysis through Blockchain Learning and Estimation) has two direct temporal preparation paths: historical fixed-block examples and live closed-head inference. Both use the same ordered feature functions and persisted training-only feature state.

## Historical interface

`prepare_fit_history(corpus, experiment)` validates complete context and outcome support, fits state from training support only, and returns:

```text
HistoricalPreparation
  training: HistoricalDataset
  validation: HistoricalDataset
  feature_state: FeatureState
  target_state: TargetState
  classification_state: ClassificationLossState | None
```

`prepare_historical_window(corpus, experiment, window, *, feature_state, target_state)` prepares an exact validation or testing window with persisted state. A validation window must equal the experiment's authored validation window. A testing window must begin after all validation outcomes are complete.

For origin `h`, support is exact by block number:

```text
context:  h-C+1 ... h
outcome:  h+1   ... h+K
action k: target h+1+k
```

The Corpus must include every context and outcome block named by this geometry.

## Lazy dataset

Preparation builds one contiguous CPU backing over the needed range:

- transformed feature rows: float32 `[rows,F]`;
- raw base fees: int64 `[rows]`;
- block numbers: int64 `[rows]`.

It stores per-origin row positions and first-argmin labels as int64 vectors and standardized targets as a float32 vector. `HistoricalDataset.__getitem__()` slices one float32 `[C,F]` input and one int64 `[K]` raw fee outcome on demand, plus scalar int64 label and origin block and scalar float32 target.

## Feature state

The ordered feature tuple is request authority. Names must be unique and supported by the direct implementation. Raw features are assembled in exactly that order as Float64. Training-support population means and standard deviations use `ddof=0`; a constant feature is invalid. Transform applies those values and returns finite C-contiguous float32 rows.

Exact formulas, units, causal availability, and the Ethereum forming-fee recurrence belong to the [theory](../../../docs/theory.md#causal-features).

## Outcome preparation

Historical outcomes remain positive int64 fees. For each origin, NumPy first-index `argmin` over `h+1 … h+K` produces the label; the selected raw minimum feeds the fitted target state. Training fits classification support only when the request asks for corrected inverse-frequency weighting.

Role boundaries are complete-outcome boundaries. The training last parent plus `K` must be strictly before the first validation parent; an authored testing window obeys the same rule after validation. Training alone fits feature state, target state, classification support, and model weights.

## Live interface

Serving freezes one latest closed head `h`, reads exactly `C-1` predecessors, validates the same seven row fields, transforms the ordered features with the artifact's `FeatureState`, and constructs float32 `[1,C,F]`. Historical preparation owns outcomes, labels, and target values.

The artifact fixes `C`, `K`, feature order, and fitted states. Decoding returns `k`, and serving reports `h+1+k` as the target block coordinate.
