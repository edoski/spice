# Minimum-Block-Fee Task

FABLE (Fee Analysis through Blockchain Learning and Estimation) keeps the architecture-neutral target, loss, and decode contract in top-level `fable.min_block_fee`. Temporal preparation supplies its targets, model families return its output, and evaluation consumes the result.

## Owned values

`TargetState` contains the Float64 population mean and positive population standard deviation of `ln(raw horizon minimum)` over retained training origins.

`ClassificationLossState` contains one positive support count per action for corrected inverse-frequency classification. Unweighted classification carries `None`.

`MinBlockFeeOutput` has two tensors:

```text
action_logits:  [B,K]
minimum_fee_z:  [B]
```

The scalar head predicts the standardized natural log of the horizon minimum. Its scientific interpretation is defined in the [theory](../../../docs/theory.md#targets-loss-and-decode).

## Direct functions

- `fit_target_state(raw_minima)` requires a nonempty positive int64 vector, computes Float64 `ln`, mean, and `ddof=0` standard deviation, and rejects constant targets.
- `standardize_target(raw_minima, state)` returns finite contiguous float32 z values.
- `target_natural_log(target_z, state)` reconstructs Float64 natural-log coordinates.
- `fit_classification_loss_state(labels, *, horizon_blocks, loss_definition)` validates label range and, for corrected weighting, requires positive training support for every action.
- `min_block_fee_loss(...)` validates both heads and targets, computes scaled per-origin classification and regression contributions, and returns their per-origin sum plus the sample-denominator mean.
- `decode_action(output)` applies native first-index `argmax` along the action dimension.

The exact equations and weighting alternatives are in the [theory](../../../docs/theory.md#targets-loss-and-decode).

## Boundaries

Temporal preparation owns raw `[K]` outcomes, first-argmin labels, and standardized targets. Model code owns the sequence encoder and the two concrete heads. Evaluation owns observation publication and economic accounting.
